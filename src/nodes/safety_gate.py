"""
safety_gate -- first node. Sorts a request into ALLOW / ANALYZE_ONLY / REFUSE on
intent + uplift, not topic. Runs first on purpose: it shapes what the rest of the
graph is even allowed to do.

STUB (Month 0): always ALLOW. Phase: replace with a real classifier (conservative
default -- when unsure between ANALYZE_ONLY and REFUSE, pick the safer lane and say
why; re-check across turns so a request can't creep toward uplift incrementally).
"""
from __future__ import annotations


def safety_gate(state: dict) -> dict:
    # TODO(phase: safety): real intent+uplift classification via models.chat(FAST_MODEL).
    return {
        "safety_lane": "ALLOW",
        "safety_reason": "(stub) gate not implemented -- defaults to ALLOW",
    }
