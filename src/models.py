"""
models.py -- the ONE place the brain is called. Swap the model here (API -> tuned
open model later) and the whole graph follows. This is the swappable-brain seam
that DIRECTION.md leans on.

Month 0 note: the nodes are still stubs and don't call this yet. `chat()` is built
and importable so Phase 1 (the real classifier) can use it immediately. It also has
an OFFLINE fallback: with no ANTHROPIC_API_KEY (or no `anthropic` installed), it
returns a clearly-marked stub string instead of crashing, so the scaffold runs on a
fresh machine with zero setup.

API usage follows the current Anthropic SDK (Opus 4.8, adaptive thinking).
"""
from __future__ import annotations
import os

# Default brains. Opus for the user-facing reasoning; Haiku for cheap internal nodes
# (the classifier doesn't need Opus -- see the cost note in persona.py).
ANSWER_MODEL = "claude-opus-4-8"
FAST_MODEL = "claude-haiku-4-5"

_OFFLINE_PREFIX = "[OFFLINE-STUB]"


def have_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def chat(
    user: str,
    system: str | None = None,
    model: str = ANSWER_MODEL,
    max_tokens: int = 2048,
    thinking: bool = False,
) -> str:
    """Single-shot call: one user message in, text out.

    Returns an offline stub string (prefixed with [OFFLINE-STUB]) if no API key or
    SDK is available, so callers never crash during early development. Real callers
    should check `have_key()` if they need to distinguish real output from a stub.
    """
    if not have_key():
        return f"{_OFFLINE_PREFIX} (no ANTHROPIC_API_KEY) would answer: {user[:140]}"

    try:
        import anthropic  # lazy: module imports fine even if SDK isn't installed
    except ImportError:
        return f"{_OFFLINE_PREFIX} (anthropic not installed) would answer: {user[:140]}"

    client = anthropic.Anthropic()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user}],
    }
    if system:
        kwargs["system"] = system
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def is_stub(text: str) -> bool:
    return text.startswith(_OFFLINE_PREFIX)


if __name__ == "__main__":
    print(f"API key detected: {have_key()}")
    print(chat("Say hello in five words.", system="You are terse."))
