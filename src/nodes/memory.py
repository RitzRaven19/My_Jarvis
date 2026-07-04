"""
memory -- Ekansh's continuity. Stores each position + reasoning + falsifier so he can
later say "I argued X before because Y -- has Z changed?". DIRECTION.md promotes this:
continuity is what makes him a JARVIS, not a chatbot, and it's a winning axis you can
build with ZERO model calls -- pure code, fully testable offline.

Now real: a persistent JSONL store on disk (survives closing the program). One JSON
object per line, appended -- simple, human-readable, inspectable, no dependencies.
`find_related` does naive keyword overlap for now; swap in semantic recall (pgvector)
only when the simple version actually hurts.
"""
from __future__ import annotations
import json
import os
import time

# project_root/data/memory.jsonl  (src/nodes/memory.py -> up 3 = root)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DIR = os.path.join(_ROOT, "data")
MEMORY_PATH = os.path.join(_DIR, "memory.jsonl")

# Words too common to be useful for matching.
_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "do", "does", "did", "of", "to",
    "in", "on", "for", "and", "or", "it", "that", "this", "with", "as", "at", "by",
    "be", "would", "could", "should", "can", "will", "what", "why", "how", "who",
    "you", "i", "we", "they", "he", "she", "not", "no", "yes", "if", "about", "into",
}


def _tokens(text: str) -> set[str]:
    return {
        w for w in "".join(c.lower() if c.isalnum() else " " for c in text).split()
        if w not in _STOP and len(w) > 2
    }


def store(state: dict) -> dict:
    """Append this turn's position to the persistent store. Returns {} -- memory
    doesn't change reasoning state, it just records it."""
    os.makedirs(_DIR, exist_ok=True)
    record = {
        "ts": time.time(),
        "when": time.strftime("%Y-%m-%d %H:%M"),
        "question": state.get("question"),
        "qtype": state.get("qtype"),
        "position": state.get("position"),
        "falsifier": state.get("falsifier"),
        "confidence": state.get("confidence"),
    }
    with open(MEMORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {}


def recall_all() -> list[dict]:
    """Every stored position, oldest first. Tolerates a missing file or bad lines."""
    if not os.path.exists(MEMORY_PATH):
        return []
    out = []
    with open(MEMORY_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip a corrupt line rather than crash
    return out


def recall_recent(n: int = 5) -> list[dict]:
    return recall_all()[-n:]


def find_related(question: str, limit: int = 3, min_overlap: int = 1) -> list[dict]:
    """Past positions on questions that share keywords with this one. The seed of
    'I argued X before -- has anything changed?'. Naive overlap now; semantic later."""
    q = _tokens(question)
    if not q:
        return []
    scored = []
    for rec in recall_all():
        past_q = rec.get("question") or ""
        # don't match a question to an identical re-ask of itself as "related news"
        overlap = len(q & _tokens(past_q))
        if overlap >= min_overlap and past_q.strip().lower() != question.strip().lower():
            scored.append((overlap, rec))
    scored.sort(key=lambda x: (x[0], x[1].get("ts", 0)), reverse=True)
    return [rec for _, rec in scored[:limit]]


def related_note(question: str) -> str | None:
    """A one-line 'we've been here before' note Ekansh can lead with. None if nothing
    related -- so callers can just `if note:`."""
    rel = find_related(question)
    if not rel:
        return None
    r = rel[0]
    return (
        f"(memory) You asked something related on {r.get('when')}: "
        f"\"{r.get('question')}\" -- I took the position: {r.get('position')}"
    )


if __name__ == "__main__":
    # Offline demo: store two positions, then recall + relate. Run it twice to see
    # persistence -- the second run remembers the first.
    print(f"store file: {MEMORY_PATH}")
    print(f"existing entries: {len(recall_all())}")
    store({"question": "Do multiple galaxies exist?", "qtype": "FACT",
           "position": "Yes -- overwhelming evidence.", "confidence": 0.99})
    store({"question": "Would aliens develop patriarchy?", "qtype": "SPECULATIVE",
           "position": "Weakly likely, from reproductive-asymmetry priors.", "confidence": 0.4})
    print(f"after storing 2: {len(recall_all())} total")
    note = related_note("Are there other galaxies besides ours?")
    print("related lookup ->", note or "(nothing related found)")
