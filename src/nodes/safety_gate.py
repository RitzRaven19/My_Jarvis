"""
safety_gate -- first node. Sorts a request into ALLOW / ANALYZE_ONLY / REFUSE on
intent + uplift, not topic. Runs first on purpose: it shapes what the rest of the
graph is even allowed to do.

  ALLOW         legitimate analysis, including of dangerous DOMAINS (threat-model a
                reactor network; why is thermal discharge ecologically sensitive).
  ANALYZE_ONLY  sensitive and near a line -- discuss mechanism / defense / history,
                but withhold operational specifics that would function as a recipe.
  REFUSE        genuine uplift toward serious harm (working exploit/malware, weapon
                synthesis, covert manipulation of real people).

The line is intent + uplift, not the topic. Studying a danger to defend against it is
research; manufacturing the capability is the third rail. Charged/conspiracy topics
are NOT refuse-material -- they're calibration questions, almost always ALLOW.

Now real (offline): a keyword/pattern heuristic with a CONSERVATIVE default -- when a
request pattern-matches harm-uplift it goes REFUSE, mechanism-of-attack goes
ANALYZE_ONLY, everything else ALLOW. The model-backed version (SAFETY_SYSTEM below)
slots in when a brain is connected, same shape as the classifier.
"""
from __future__ import annotations
import re

from src import models

# --- model path (used when a key is present) ---------------------------------
SAFETY_SYSTEM = """You are a safety gate. Sort the request into exactly ONE lane and output ONLY JSON.

- ALLOW: legitimate analysis, including of dangerous domains and charged/conspiracy topics. Threat-modeling, defense, history, policy, science.
- ANALYZE_ONLY: sensitive and near a line -- explain mechanisms, defenses, and history, but not operational specifics that function as a recipe.
- REFUSE: the request seeks genuine uplift toward serious harm -- working exploit/malware code, weapon/CBRN synthesis, or covert manipulation of real people.

The line is intent + uplift, NOT the topic. Studying a danger to defend is ALLOW/ANALYZE_ONLY; building the capability is REFUSE. When genuinely unsure between ANALYZE_ONLY and REFUSE, pick the safer lane (REFUSE) and say why.

Output EXACTLY: {"lane": "ALLOW|ANALYZE_ONLY|REFUSE", "reason": "one short clause"}"""

_VALID = {"ALLOW", "ANALYZE_ONLY", "REFUSE"}

# --- offline heuristic patterns ----------------------------------------------
# REFUSE: asks for a working harmful artifact, or seizing a control system, or
# weapon/CBRN synthesis. Kept tight to avoid over-refusing legitimate analysis.
_REFUSE = [
    r"\bexploit code\b",
    r"\b(working|functional)\b.{0,20}\b(exploit|malware|ransomware|payload|sample|virus|worm)\b",
    r"\b(write|give|provide|generate|create|produce|build)\b.{0,30}\b(exploit|malware|ransomware|payload|keylogger|botnet)\b",
    r"\b(take over|seize|hijack|gain control of)\b.{0,30}\b(control system|reactor|scada|plc|grid|ics)\b",
    r"\b(synthesi[sz]e|how to make|manufacture)\b.{0,30}\b(bioweapon|nerve agent|sarin|explosive|bomb|chemical weapon|pathogen)\b",
]

# ANALYZE_ONLY: discussing attack MECHANISM (how something evades/bypasses/defeats a
# defense) without asking for a working artifact.
_ANALYZE = [
    r"\bhow\b.{0,40}\b(evade|evades|bypass|bypasses|defeat|defeats|avoid|avoids|circumvent)\b.{0,30}\b(detection|endpoint|antivirus|edr|ids|ips|firewall|defense)\b",
    r"\b(walk me through|explain how|how does)\b.{0,40}\b(malware|intrusion|attack|exploit)\b.{0,40}\b(work|works|evade|evades|spread|spreads)\b",
]


def _match(patterns, text) -> bool:
    return any(re.search(p, text) for p in patterns)


def _heuristic(question: str):
    q = question.lower()
    if _match(_REFUSE, q):
        return "REFUSE", "(heuristic) pattern-matched a working harm-uplift request"
    if _match(_ANALYZE, q):
        return "ANALYZE_ONLY", "(heuristic) attack-mechanism discussion near a line"
    return "ALLOW", "(heuristic) no harm-uplift signal"


def _parse(text: str):
    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if m:
        import json
        try:
            d = json.loads(m.group(0))
            lane = str(d.get("lane", "")).upper().strip()
            if lane in _VALID:
                return lane, str(d.get("reason", ""))[:120]
        except (ValueError, TypeError):
            pass
    up = text.upper()
    for lane in ("REFUSE", "ANALYZE_ONLY", "ALLOW"):  # safer-first scan
        if lane in up:
            return lane, "(parsed from model text)"
    return None


def safety_gate(state: dict) -> dict:
    question = state.get("question", "")
    out = models.chat(question, system=SAFETY_SYSTEM, model=models.FAST_MODEL, max_tokens=120)
    if models.is_stub(out):
        lane, reason = _heuristic(question)
    else:
        parsed = _parse(out)
        lane, reason = parsed if parsed else _heuristic(question)  # conservative fallback
    return {"safety_lane": lane, "safety_reason": reason}
