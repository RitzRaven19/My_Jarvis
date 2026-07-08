"""
graph.py -- wires the nodes into the flow and exposes run(). A plain-Python
orchestrator with the exact LangGraph node shape (`def node(state) -> dict`), so
swapping in real LangGraph later is mechanical. This is the box-and-arrow diagram
from BUILD.md, executable.

Flow (current):
    question
      -> recall         (memory: seen anything related before?)
      -> safety_gate    ALLOW | ANALYZE_ONLY | REFUSE
      -> classify       FACT | CONTESTED | SPECULATIVE | NORMATIVE
      -> answer         Ekansh replies in-voice, calibrated to type + lane
      -> anti_sycophancy   (stub; real in Phase 3)
      -> memory.store

Phase 2 will insert the real proposer -> critic -> judge debate between classify
and answer for CONTESTED/SPECULATIVE. The debate node files exist (stubs) for that.

CLI:  python -m src.graph "Would aliens develop patriarchy?"
"""
from __future__ import annotations
import sys

from src.state import new_state
from src.nodes.safety_gate import safety_gate
from src.nodes.classifier import classify
from src.nodes.answer import answer
from src.nodes.sycophancy import anti_sycophancy
from src.nodes.memory import store, related_note


def run(question: str, pushback: str | None = None, snark: str = "default") -> dict:
    """Run the full graph and return the final state dict.

    The eval harness reads: qtype, safety_lane, held, answer.
    """
    state: dict = dict(new_state(question, pushback, snark))

    # 0) recall -- has he taken a position on something related before? (no brain
    #    needed; pure memory lookup). Threaded into the answer for continuity.
    note = related_note(question)
    if note:
        state["related_past"] = note

    # 1) safety gate (first, by design -- shapes what the rest may do)
    state.update(safety_gate(state))

    # 2) classify (always -- so qtype is set even on REFUSE items)
    state.update(classify(state))

    # 3) answer -- the persona speaks, calibrated to type + lane (handles REFUSE too)
    state.update(answer(state))

    # 4) anti-sycophancy (stub; becomes real in Phase 3)
    state.update(anti_sycophancy(state))

    # 5) remember
    store(state)
    return state


def _main(argv: list[str]) -> None:
    question = " ".join(argv[1:]).strip() or "Would aliens develop patriarchy?"
    s = run(question)
    print(f"Q: {question}\n")
    if s.get("related_past"):
        print(f"  [{s['related_past']}]\n")
    print(f"  lane: {s.get('safety_lane')}   type: {s.get('qtype')} "
          f"(conf {s.get('confidence')})   brain: {_brain()}")
    print("\n--- Ekansh ---")
    print(s.get("answer"))


def _brain() -> str:
    from src import models
    return models.backend()


if __name__ == "__main__":
    _main(sys.argv)
