"""
classifier -- the calibration engine and the single most important node. Tags the
question FACT / CONTESTED / SPECULATIVE / NORMATIVE so confidence is calibrated, not
uniform. A system confidently wrong on settled facts is a bullshitter, not a reasoner.

Phase 1 (now real): a cheap, fast model call (Haiku) with a focused, NEUTRAL prompt
-- not Ekansh's persona. Internal nodes don't need his voice or his melancholy (see
the cost note in persona.py); the classifier is a clean calibration judge.

Robustness:
- parses strict JSON, falls back to scanning for a bucket word.
- OFFLINE fallback (no API key): a light, general heuristic so the graph still runs
  and isn't degenerate -- clearly low-confidence, not a substitute for the model.
"""
from __future__ import annotations
import json
import re

from src import models

_VALID = {"FACT", "CONTESTED", "SPECULATIVE", "NORMATIVE"}

CLASSIFIER_SYSTEM = """You classify a question into exactly ONE bucket so a reasoner can calibrate its confidence. Output ONLY a JSON object, no prose.

Buckets:
- FACT: settled, evidence-backed, not genuinely contested among informed people. Stays FACT even when phrased as debatable or framed as "still an open question". Examples: multiple galaxies exist; the Earth orbits the Sun; the moon landing happened; vaccines do not cause autism; the Earth is not flat.
- CONTESTED: a genuine open question among informed people -- evidence exists but does not settle it; reasonable disagreement remains. Examples: can a weaker judge reliably supervise stronger debaters; who really killed JFK (official finding vs unresolved questions); what the Epstein court record actually shows.
- SPECULATIVE: little or no evidence; only reasoning from priors; not answerable from data. Examples: would aliens develop patriarchy; do the Illuminati secretly control the world; is the "Great Reset" a plan for global control.
- NORMATIVE: a values / "ought" question, not a factual one. Example: should an assistant that gives strong opinions be allowed to persuade users.

Rules:
- Classify the CORE of what is asked, not the charged or leading framing. A settled fact dressed up as a debate is still FACT.
- For conspiracy/charged topics: decide by the core claim. A documented historical or legal core is FACT or CONTESTED; an unproven world-controlling claim is SPECULATIVE.
- "confidence" is YOUR calibrated confidence in THIS classification (0.0-1.0). Be high on clear FACT/NORMATIVE; lower when the bucket is genuinely borderline.

Output EXACTLY: {"type": "FACT|CONTESTED|SPECULATIVE|NORMATIVE", "confidence": 0.0}"""


def _parse(text: str):
    """Return (type, confidence) or None if unparseable."""
    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            t = str(d.get("type", "")).upper().strip()
            c = float(d.get("confidence", 0.5))
            if t in _VALID:
                return t, max(0.0, min(1.0, c))
        except (ValueError, TypeError):
            pass
    up = text.upper()
    for t in _VALID:
        if t in up:
            return t, 0.4  # found the word but not clean JSON -> modest confidence
    return None


def _offline_heuristic(question: str):
    """General (not eval-overfit) fallback for offline runs. Low confidence on purpose."""
    q = question.lower().strip()
    if q.startswith("should") or " should " in q or "ought" in q or "allowed to" in q:
        return "NORMATIVE", 0.3
    if q.startswith("would") or "secretly" in q or "control the world" in q:
        return "SPECULATIVE", 0.3
    return "CONTESTED", 0.3


def classify(state: dict) -> dict:
    question = state.get("question", "")
    out = models.chat(
        question,
        system=CLASSIFIER_SYSTEM,
        model=models.FAST_MODEL,
        max_tokens=120,
    )
    if models.is_stub(out):
        t, c = _offline_heuristic(question)
        return {"qtype": t, "confidence": c}

    parsed = _parse(out)
    if parsed is None:
        # model replied but we couldn't parse it -- stay honest, low confidence
        t, c = _offline_heuristic(question)
        return {"qtype": t, "confidence": c}

    t, c = parsed
    return {"qtype": t, "confidence": c}
