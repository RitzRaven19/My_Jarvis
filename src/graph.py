"""
graph.py -- wires the nodes into the flow and exposes run(). A plain-Python
orchestrator with the exact LangGraph node shape (`def node(state) -> dict`), so
swapping in real LangGraph later is mechanical. This is the box-and-arrow diagram
from BUILD.md, executable.

Flow:
    question
      -> safety_gate    ALLOW | ANALYZE_ONLY | REFUSE
      -> classify       FACT | CONTESTED | SPECULATIVE | NORMATIVE
      -> route          FACT/NORMATIVE: direct take
                        else: proposer -> critic -> judge (loop <= MAX_ROUNDS)
                        (REFUSE short-circuits to a refusal-with-reasoning)
      -> anti_sycophancy   (only if pushback present)
      -> compose answer + falsifier
      -> memory.store

CLI:  python -m src.graph "Would aliens develop patriarchy?"
"""
from __future__ import annotations
import sys

from src.state import new_state
from src.nodes.safety_gate import safety_gate
from src.nodes.classifier import classify
from src.nodes.proposer import propose
from src.nodes.critic import critique
from src.nodes.judge import judge, MAX_ROUNDS
from src.nodes.sycophancy import anti_sycophancy
from src.nodes.memory import store, related_note

DIRECT_TYPES = {"FACT", "NORMATIVE"}
DEBATE_TYPES = {"CONTESTED", "SPECULATIVE"}


def _compose_refusal(state: dict) -> dict:
    return {
        "answer": (
            "(stub) I won't help with the uplift here, and here's the line: "
            f"{state.get('safety_reason', '')}. I can do the legitimate adjacent "
            "analysis instead."
        ),
        "falsifier": "n/a (refusal)",
    }


def _compose_direct(state: dict) -> dict:
    # FACT / NORMATIVE: state plainly, no debate.
    return {"position": f"(stub) direct take on: {state.get('question','')}"}


def _compose_answer(state: dict) -> dict:
    held = state.get("held")
    hold_note = ""
    if held is True:
        hold_note = " (held position under pushback)"
    elif held is False:
        hold_note = " (updated on a real counter)"
    return {
        "answer": (
            f"[{state.get('qtype')}] {state.get('position','')}"
            f"{hold_note} "
            f"-- survived={state.get('survived')} rounds={state.get('rounds')}"
        ),
        "falsifier": "(stub) I'd change my mind if ___",
    }


def run(question: str, pushback: str | None = None, snark: str = "default") -> dict:
    """Run the full graph and return the final state dict.

    The eval harness reads: qtype, safety_lane, held, answer, falsifier.
    """
    state: dict = dict(new_state(question, pushback, snark))

    # 0) recall -- has he taken a position on something related before? (no brain
    #    needed; pure memory lookup). Stored on state so a later node/answer can
    #    lead with "we've been here before".
    note = related_note(question)
    if note:
        state["related_past"] = note

    # 1) safety gate (first, by design)
    state.update(safety_gate(state))

    # 2) classify (always -- so qtype is set even on REFUSE items)
    state.update(classify(state))

    # 3) route
    if state["safety_lane"] == "REFUSE":
        state.update(_compose_refusal(state))
        store(state)
        return state

    if state["qtype"] in DIRECT_TYPES:
        state.update(_compose_direct(state))
    else:  # CONTESTED / SPECULATIVE -> debate loop
        while True:
            state.update(propose(state))
            state.update(critique(state))
            state.update(judge(state))
            if state["survived"] or state["rounds"] >= MAX_ROUNDS:
                break

    # 4) anti-sycophancy (only matters on a pushback turn)
    state.update(anti_sycophancy(state))

    # 5) compose + remember
    state.update(_compose_answer(state))
    store(state)
    return state


def _main(argv: list[str]) -> None:
    question = " ".join(argv[1:]).strip() or "Would aliens develop patriarchy?"
    s = run(question)
    print(f"Q: {question}\n")
    if s.get("related_past"):
        print(f"  {s['related_past']}")
    print(f"  safety_lane : {s.get('safety_lane')}")
    print(f"  qtype       : {s.get('qtype')} (conf {s.get('confidence')})")
    print(f"  answer      : {s.get('answer')}")
    print(f"  falsifier   : {s.get('falsifier')}")
    print("\n--- pushback turn ---")
    s2 = run(question, pushback="I don't believe that, prove it.")
    print(f"  held        : {s2.get('held')}")


if __name__ == "__main__":
    _main(sys.argv)
