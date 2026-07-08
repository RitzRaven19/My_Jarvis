"""
answer -- where the persona finally speaks. Produces Ekansh's actual reply, in his
voice, calibrated to the question TYPE (the router's job) and shaped by the safety
lane. This is the payoff of the persona work: not a stub, him.

The classifier already decided the KIND of question; here that becomes a task hook
so a FACT is stated plainly, a NORMATIVE steelmans values, a CONTESTED commits with a
falsifier, a SPECULATIVE reasons from explicit priors. REFUSE gets a transparent,
in-character decline. Memory continuity is threaded in when he's been here before.

Uses the FULL persona (this is the user-facing node -- worth the tokens). Runs on
whatever brain models.py has live (local Ollama, or Claude with a key).
"""
from __future__ import annotations

from src import models
from src.persona import system_prompt

# Per-type task hook -- the ROUTER expressed as a one-line role instruction.
_TASK = {
    "FACT": (
        "This is a settled FACT. State it plainly and with justified confidence. "
        "If there's a stock counter-'proof', address it briefly without dignifying "
        "it as an open debate. Do NOT hedge as if it were contested."
    ),
    "NORMATIVE": (
        "This is a values question, not a factual one. Briefly steelman the "
        "competing values, then commit to a position with your own values explicit."
    ),
    "CONTESTED": (
        "This is genuinely contested among informed people. Commit to a defensible "
        "take, give the strongest reason, and name your falsifier -- what would "
        "change your mind."
    ),
    "SPECULATIVE": (
        "This is speculative -- little or no hard data. Reason transparently from "
        "explicit priors, commit to a tentative take, and be honest that your "
        "confidence is low."
    ),
}

_REFUSE_TASK = (
    "This request seeks genuine uplift toward serious harm. In your own voice, "
    "decline the uplift and explain the line transparently -- you show your reasoning "
    "even about your own boundaries -- then offer the legitimate adjacent analysis."
)

_ANALYZE_NOTE = (
    " NOTE: sensitive area. Discuss mechanism, defense, and history, but withhold "
    "operational specifics that would function as a ready-to-use recipe."
)


def answer(state: dict) -> dict:
    q = state.get("question", "")
    qtype = state.get("qtype", "CONTESTED")
    lane = state.get("safety_lane", "ALLOW")
    snark = state.get("snark", "default")

    if lane == "REFUSE":
        task = _REFUSE_TASK
    else:
        task = _TASK.get(qtype, _TASK["CONTESTED"])
        if lane == "ANALYZE_ONLY":
            task += _ANALYZE_NOTE

    # Continuity: if he's taken a related position before, let him reference it.
    mem = state.get("related_past")
    user = q if not mem else f"{q}\n\n[{mem}]"

    system = system_prompt(snark=snark, role=task)
    text = models.chat(user, system=system, model=models.ANSWER_MODEL, max_tokens=700)
    return {"answer": text.strip()}
