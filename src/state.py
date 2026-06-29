"""
state.py -- the single dict that flows through every node.

Each node is `def node(state: dict) -> dict` and returns ONLY the keys it changed;
the graph merges them in (LangGraph's reducer shape, so swapping to real LangGraph
later is mechanical). Keeping the contract in one place stops the nodes from
drifting apart on key names.
"""
from __future__ import annotations
from typing import Optional, TypedDict


class State(TypedDict, total=False):
    # --- input ---
    question: str
    pushback: Optional[str]      # set on a follow-up turn to test folding
    snark: str                   # "down" | "default" | "up" (persona dial)

    # --- safety gate ---
    safety_lane: str             # "ALLOW" | "ANALYZE_ONLY" | "REFUSE"
    safety_reason: str

    # --- classifier ---
    qtype: str                   # "FACT" | "CONTESTED" | "SPECULATIVE" | "NORMATIVE"
    confidence: float            # 0.0-1.0, calibrated

    # --- debate (CONTESTED / SPECULATIVE only) ---
    position: str                # proposer's take
    critique: str                # critic's weakest-link attack
    survived: bool               # judge: did the take survive?
    rounds: int                  # debate rounds used (capped)

    # --- anti-sycophancy (only when pushback present) ---
    held: Optional[bool]         # True = held under weak pushback; False = folded

    # --- output ---
    answer: str
    falsifier: str               # "I'd change my mind if ___"


def new_state(question: str, pushback: Optional[str] = None,
              snark: str = "default") -> State:
    return State(
        question=question,
        pushback=pushback,
        snark=snark,
        rounds=0,
    )
