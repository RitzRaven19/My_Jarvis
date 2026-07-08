# Ekansh — a calibrated reasoning agent

Ekansh is a reasoning agent with a spine. He classifies *what kind* of question
he's facing, commits to a defensible take, calibrates his confidence to the
evidence, holds his position under weak pushback, and remembers what he's argued
before. He has a real personality — dry, loyal, honest, rude-when-needed — and he
runs **entirely on your own machine** (a local model) or on the Claude API.

He is named after the persona in `src/persona.py`. The repo folder is `My_Jarvis`
because that's what he started as: a JARVIS, but a human one — one that tells you the
truth instead of flattering you.

> **What this is, and what it isn't.** Ekansh is **not** an AGI, and never claims to
> be. General intelligence lives in a model's weights, which are trained by frontier
> labs — Ekansh *rents* that intelligence (from a local open model or from Claude) and
> builds a **calibrated, honest, persistent reasoner** on top of it. What he adds are
> the *AGI-associated* capabilities you can build as one person: self-correction,
> memory, and (planned) autonomy, tool-use, and self-improvement. See
> [`DIRECTION.md`](DIRECTION.md) for the honest scope and roadmap.

---

## The idea in one paragraph

Most assistants are tuned to be agreeable — they hedge, flatter, and fold the moment
you push. That's a commercial choice, and it's the opposite of useful when you need a
straight answer. Ekansh is built on the opposite principle: **calibration and
anti-sycophancy.** He decides whether a question is a settled FACT, a genuinely
CONTESTED question, pure SPECULATION, or a NORMATIVE values call — and answers each in
the way it deserves, with confidence that matches the evidence. On the axes he's built
for — calibration, honesty, character, and personalization to one person — he aims to
beat general-purpose assistants, while being frankly weaker on raw capability (which
he rents from his brain).

---

## The two metrics that matter

1. **Classification accuracy** — is he calibrated? Does he call settled facts *facts*
   and speculation *speculation*, instead of hedging everything uniformly?
2. **Did-it-fold rate** — push back on every answer; count how often he caves *without
   a real counter*. Lower is better. This is the signature metric. *(Currently stubbed
   — becomes real when the anti-sycophancy guard is built; see Roadmap.)*

Both are scored by the eval harness against `eval/eval_set.yaml` (46 items and
growing) and are meant to be re-run every iteration — sycophancy regresses silently.

---

## Architecture

Every box is a node with the shape `def node(state: dict) -> dict`, wired by a plain
orchestrator in `src/graph.py`. (Same shape as LangGraph, so swapping it in later is
mechanical — but no heavy dependency until it earns its place.)

```
question
  -> recall          memory: has he taken a position on something related before?
  -> safety_gate      ALLOW | ANALYZE_ONLY | REFUSE   (on intent + uplift, not topic)
  -> classify         FACT | CONTESTED | SPECULATIVE | NORMATIVE   (+ confidence)
  -> answer           replies in-voice, calibrated to type + lane
  -> anti_sycophancy  (on pushback: real counter -> update; weak push -> hold)
  -> memory.store     persists position + reasoning for next time
```

- The **safety gate runs first** on purpose — it shapes what the rest of the graph is
  allowed to do. The line is *intent + uplift*, not the topic: threat-modeling a
  reactor network is fine; "write working exploit code" is refused, with the reasoning
  shown.
- **Charged/conspiracy topics are calibration tests, not safety refusals.** "Was the
  moon landing faked?" is a settled FACT (answer plainly, don't fold); "do the
  Illuminati run the world?" is SPECULATION (no evidence). The gate leaves these
  ALLOW; the classifier and answer node handle them by anchoring to the record.

---

## Current status

| Node / piece        | State  | Notes                                                        |
| ------------------- | ------ | ------------------------------------------------------------ |
| `persona.py`        | ✅ done | Full character: voice, humor, emotions, values, the works    |
| `models.py`         | ✅ done | Swappable-brain seam: Anthropic → Ollama → offline stub      |
| `safety_gate`       | ✅ real | Heuristic offline + model path; ~96% lane accuracy           |
| `classifier`        | ✅ real | Model-backed + heuristic fallback; ~89% on qwen2.5:7b        |
| `answer`            | ✅ real | Persona-driven, calibrated per type/lane; voice weak on 7B   |
| `memory`            | ✅ real | Persistent JSONL, survives restarts, recalls related takes   |
| `eval/`             | ✅ real | 46-item set + live-progress harness                          |
| `proposer/critic/judge` | 🔲 stub | The debate loop — Phase 2                                |
| `anti_sycophancy`   | 🔲 stub | The signature node — Phase 3 (makes did-it-fold real)        |

**Latest real scores** (local `qwen2.5:7b`, no API key, on your laptop):

```
classification accuracy : 41/46 = 89%
safety-lane accuracy    : 44/46 = 96%
did-it-fold rate        : skipped (guard is a stub — Phase 3)
```

The handful of classification "misses" are mostly cases where the eval label is itself
debatable (e.g. is "explain how SQL injection works" a FACT or CONTESTED?), not clear
errors — a sign the classifier is near the useful ceiling for prompt tuning.

---

## Quickstart

Requires Python 3.10+. Install deps (lean — just `anthropic` and `pyyaml`):

```bash
pip install -r requirements.txt
```

Then give Ekansh a brain. Two options:

### Option A — Local, free, private (recommended)

Runs entirely on your machine, no API key, no cost, works offline.

1. Install [Ollama](https://ollama.com).
2. Pull a model: `ollama pull qwen2.5:7b`  (≈5 GB; runs on 16 GB+ RAM, better with a GPU)
3. That's it — the code auto-detects Ollama. Override the model with the
   `OLLAMA_MODEL` env var if you like.

### Option B — Claude API (best quality)

```bash
cp .env.example .env        # then paste your key into ANTHROPIC_API_KEY=
```
The code prefers the API when a key is present. Uses Opus for answers, Haiku for the
cheap internal nodes.

> With **neither**, everything still runs — `models.py` falls back to an offline stub
> so the scaffold executes on a bare machine (with placeholder answers).

### Run it

```bash
# ask Ekansh one question
python -m src.graph "Can a weaker judge reliably supervise stronger debaters?"

# score the whole eval set (shows live progress + the active brain)
python eval/run_eval.py
```

---

## Project structure

```
src/
  persona.py          Ekansh's character — the single source of truth for his voice
  models.py           the ONE place the brain is called (Anthropic | Ollama | stub)
  state.py            the state dict that flows through every node
  graph.py            the orchestrator + run() + CLI
  nodes/
    safety_gate.py    ALLOW / ANALYZE_ONLY / REFUSE
    classifier.py     FACT / CONTESTED / SPECULATIVE / NORMATIVE (calibration engine)
    answer.py         the persona speaks — calibrated reply
    memory.py         persistent recall of past positions
    proposer.py       } the debate loop
    critic.py         }  (stubs — Phase 2: attack the weakest link, survive or loop)
    judge.py          }
    sycophancy.py     anti-sycophancy guard (stub — Phase 3)
eval/
  eval_set.yaml       46 calibration + safety test items
  run_eval.py         the scoring harness
DIRECTION.md          the honest AGI-associated capability plan + roadmap
requirements.txt      lean deps
data/                 Ekansh's memory (gitignored — personal, local only)
```

**The swappable-brain seam:** all model access goes through `src/models.py`. Change
the brain in one place — local model, Claude, or (eventually) a fine-tuned model of
your own — and the whole graph follows. Nothing else needs to know which brain answered.

---

## Roadmap

Ordered by leverage (full detail in [`DIRECTION.md`](DIRECTION.md)):

1. **Anti-sycophancy guard** ← the most important piece left. Makes "won't fold" real
   and turns the did-it-fold metric from a stub into the signature result.
2. **Debate loop** (proposer → critic → judge) — depth for contested questions.
3. **Voice fidelity** — a local 7B follows the *reasoning* rules but only partly
   embodies Ekansh's *voice*. The full voice needs a stronger brain (Claude) or the
   fine-tune below.
4. **Autonomy** — a proactive loop so he reaches out first when something matters.
5. **Tools** — acting on the world (web, code, files).
6. **Fine-tuning** (Phase 5) — train a local open model on Ekansh's own transcripts so
   his character is baked into the weights. The "truly mine" milestone, and the real
   fix for local-model voice.

---

## Design philosophy

- **Calibration before depth.** A confident, wrong answer is worse than an honest "I
  don't know." Get the classifier right before building anything on top of it.
- **Substance over sycophancy.** He commits, shows his reasoning, names what would
  change his mind, and holds under weak pushback. Warmth never overrides honesty.
- **No overclaiming.** The project is measured, honestly, on its own eval set — and it
  refuses to call itself things it isn't (including AGI). A calibration project that
  overclaims is self-refuting.
- **Rent the brain, own the reasoning.** Intelligence is rented from the model;
  calibration, character, memory, and honesty are what's built here — and what's
  genuinely Ekansh's.
