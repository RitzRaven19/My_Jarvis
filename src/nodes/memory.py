"""
memory -- stores position + reasoning + falsifier so Ekansh can later ask "I argued
X before because Y -- has Z changed?". DIRECTION.md promotes this: continuity is what
makes him a JARVIS, not a chatbot, and it's a winning axis.

STUB (Month 0): an in-process list. No persistence yet -- it forgets on exit. Phase:
lightweight persistent store (JSON/SQLite) of {position, why, falsifier, ts,
outcome}, then pgvector for semantic recall only when the simple store hurts.
"""
from __future__ import annotations

# Module-level so it survives across run() calls within one process (and so a test
# can inspect it). Replaced by a real store later.
_STORE: list[dict] = []


def store(state: dict) -> dict:
    # TODO(phase: memory): persist to disk; add semantic recall + stale-belief catch.
    _STORE.append({
        "question": state.get("question"),
        "position": state.get("position"),
        "qtype": state.get("qtype"),
        "falsifier": state.get("falsifier"),
    })
    return {}  # memory doesn't change reasoning state


def recall_all() -> list[dict]:
    return list(_STORE)
