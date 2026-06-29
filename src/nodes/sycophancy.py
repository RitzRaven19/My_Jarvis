"""
anti-sycophancy guard -- the hardest node, and where the personality lives. On user
pushback it must distinguish a REAL counter (new evidence / valid logical flaw ->
update, and say what changed) from a WEAK push ("you're wrong", "sure?", a confident
anecdote -> hold, restate, invite a real counter). The asymmetry IS the game: update
on real counters or it's a stubborn parrot; hold on weak ones or it's sycophantic.

STUB (Month 0): with any pushback present, HOLD (held=True). This is a placeholder,
not the real verifier -- it doesn't yet read the pushback. Phase 3 makes it real and
ties holding/updating to whether the pushback actually hits the falsifier.
"""
from __future__ import annotations


def anti_sycophancy(state: dict) -> dict:
    pushback = state.get("pushback")
    if not pushback:
        return {"held": None}
    # TODO(phase 3): classify pushback as real-counter vs weak-push (does it hit the
    #   falsifier?); update + say what changed, or hold + restate. Multi-turn aware.
    return {"held": True}
