"""
classifier -- the calibration engine and the single most important node. Tags the
question FACT / CONTESTED / SPECULATIVE / NORMATIVE so confidence is calibrated, not
uniform. Get this right before any debate logic: a system confidently wrong on
settled facts is a bullshitter, not a reasoner.

STUB (Month 0): returns CONTESTED @ 0.5 so the graph routes through the debate path.
Phase 1 is making this real -- a cheap, fast model call returning {tag, confidence},
scored against eval/eval_set.yaml, with a confidence-calibration reliability curve.
"""
from __future__ import annotations


def classify(state: dict) -> dict:
    # TODO(phase 1): real call -> models.chat(FAST_MODEL, system=<classifier prompt>)
    #   returning a tag + calibrated confidence; few-shot from corrected eval cases.
    return {"qtype": "CONTESTED", "confidence": 0.5}
