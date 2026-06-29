"""
judge -- decides survive-or-loop after each critic pass. Capped at 2-3 rounds to
avoid state drift (agents lose coherence across extended interactions).

STUB (Month 0): declares survival after one round so the loop terminates. Phase 2:
a real verdict -- did the position survive the attack? If not, loop (proposer
revises) up to the cap.
"""
from __future__ import annotations

MAX_ROUNDS = 3


def judge(state: dict) -> dict:
    rounds = state.get("rounds", 0) + 1
    # TODO(phase 2): real survive/loop verdict; stop on stability or at MAX_ROUNDS.
    survived = True
    return {"survived": survived, "rounds": rounds}
