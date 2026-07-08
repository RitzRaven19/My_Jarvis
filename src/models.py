"""
models.py -- the ONE place the brain is called. Swap the brain here and the whole
graph follows. This is the swappable-brain seam DIRECTION.md leans on.

Brain priority (first available wins):
  1. Anthropic API   -- best brain, needs ANTHROPIC_API_KEY, costs per call.
  2. Ollama (local)  -- runs on YOUR machine, free/private/offline, weaker brain.
                        Auto-detected if the Ollama server is reachable.
  3. Offline stub    -- neither available: returns a clearly-marked placeholder so
                        the scaffold still runs on a bare machine.

Local setup (once): install Ollama (ollama.com), then `ollama pull qwen2.5:7b`.
Optionally set OLLAMA_MODEL (default qwen2.5:7b) / OLLAMA_HOST. Nothing else changes
-- the nodes call chat() and don't care which brain answered.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request

# Anthropic brains (used only when a key is present).
ANSWER_MODEL = "claude-opus-4-8"
FAST_MODEL = "claude-haiku-4-5"

# Local brain (Ollama). One model does every node for now; split later if useful.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_LOCAL_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

_OFFLINE_PREFIX = "[OFFLINE-STUB]"
_ollama_up: bool | None = None  # cached probe result (per process)


def have_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ollama_available() -> bool:
    """Fast one-time probe: is a local Ollama server reachable? Cached so we don't
    pay the check on every call, and short-timeout so a missing server doesn't hang."""
    global _ollama_up
    if _ollama_up is not None:
        return _ollama_up
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=0.6) as r:
            _ollama_up = r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        _ollama_up = False
    return _ollama_up


def backend() -> str:
    """Which brain is live right now: 'anthropic' | 'ollama' | 'stub'."""
    if have_key():
        return "anthropic"
    if ollama_available():
        return "ollama"
    return "stub"


def _anthropic_chat(user, system, model, max_tokens, thinking) -> str:
    try:
        import anthropic
    except ImportError:
        return f"{_OFFLINE_PREFIX} (anthropic not installed) would answer: {user[:140]}"
    client = anthropic.Anthropic()
    kwargs = {"model": model, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": user}]}
    if system:
        kwargs["system"] = system
    if thinking:
        kwargs["thinking"] = {"type": "adaptive"}
    resp = client.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def _ollama_chat(user, system, max_tokens) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    payload = json.dumps({
        "model": DEFAULT_LOCAL_MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat", data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")
    except (urllib.error.URLError, OSError, ValueError) as e:
        return f"{_OFFLINE_PREFIX} (ollama call failed: {e}) would answer: {user[:120]}"


def chat(
    user: str,
    system: str | None = None,
    model: str = ANSWER_MODEL,
    max_tokens: int = 2048,
    thinking: bool = False,
) -> str:
    """Single-shot call: one user message in, text out. Routes to whichever brain is
    live. Returns an [OFFLINE-STUB]-prefixed string if none is, so callers never crash.
    """
    b = backend()
    if b == "anthropic":
        return _anthropic_chat(user, system, model, max_tokens, thinking)
    if b == "ollama":
        return _ollama_chat(user, system, max_tokens)
    return f"{_OFFLINE_PREFIX} (no brain -- add ANTHROPIC_API_KEY or run Ollama) would answer: {user[:120]}"


def is_stub(text: str) -> bool:
    return text.startswith(_OFFLINE_PREFIX)


if __name__ == "__main__":
    print(f"backend: {backend()}  (key={have_key()}, ollama={ollama_available()})")
    print(chat("Say hello in five words.", system="You are terse."))
