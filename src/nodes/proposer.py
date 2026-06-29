"""
proposer -- opens the debate with a committed position (not a survey). Run only on
CONTESTED / SPECULATIVE.

STUB (Month 0): echoes a placeholder take. Phase 2: real call in Ekansh's voice that
commits to a defensible position with explicit reasoning.
"""
from __future__ import annotations


def propose(state: dict) -> dict:
    q = state.get("question", "")
    # TODO(phase 2): models.chat(ANSWER_MODEL, system=persona+proposer-role).
    return {"position": f"(stub) committed take on: {q}"}
