# DIRECTION — the AGI-associated capability plan (honest scope)

What this project can credibly reach toward, and the parts it can't. Pair with
`BUILD.md` (how the reasoner is built) and `RESEARCH.md` (the why). This file
exists to channel the AGI ambition into the capabilities that are *actually
buildable by one person on a rented brain* — and to keep us from overclaiming,
which a calibration project cannot afford.

---

## 0. The one rule (read this or the rest is dangerous)

**This is not AGI, and we never say it is.**

- **Generality** — reasoning and transferring skill across any domain — is the hard
  core of AGI. It lives in the model's *weights*, it's owned by frontier labs with
  thousands of researchers and billions in compute, and you **inherit it from the
  base model for free and cannot raise it.** Your intelligence ceiling *is* the
  base model's ceiling. No arrangement of API calls beats that.
- What you *can* build are the **other capabilities in the AGI bundle** — the ones
  that make a system *function* and *feel* like AGI in practice: self-correction,
  memory, autonomy, grounding, and a self-improvement loop. The industry calls this
  **"functional AGI"**: powerful through agency + memory + tools, on top of a
  non-general brain.

**The claim you can defend:** *"A calibrated, persistent, autonomous agent that
captures several AGI-associated capabilities — on top of a frontier base model."*
True, sharp, survives a thesis defense.

**The claim that ends you:** *"~X% of the way to AGI"* / *"generally intelligent."*
AGI is a threshold, not a dial; there is no honest percentage. Saying it is the
galaxies mistake about your own work.

**The commoditization risk (govern every build decision by this):** the base model
will keep absorbing generic features. If you spend six months on a memory system
and Claude ships native memory, your six months evaporate. So spend time on what
does **not** get commoditized — your calibration *discipline*, Ekansh's *specific
character*, deep personalization *to you*, and your *eval rigor* — and stay
swappable on the brain (`src/models.py` is the one place that changes).

---

## The five capabilities (ranked by leverage)

Each is a workstream: what it is, why it's AGI-associated, how to build it, where it
maps in the existing phase plan, its metric, and what to keep non-commoditized.

### 1. Self-correction & calibration  — *the core, and already the plan*
- **What:** knows what it knows; states confidence calibrated to the *kind* of
  claim; commits, survives self-attack, and won't fold to weak pushback.
- **Why AGI-associated:** reliable self-correction and uncertainty-awareness are
  things even frontier *products* fail at (they're tuned agreeable). A system that
  genuinely doesn't bullshit is doing something most "smart" systems can't.
- **How:** the existing pipeline — safety gate -> classifier (FACT/CONTESTED/
  SPECULATIVE/NORMATIVE) -> proposer->critic->judge debate -> anti-sycophancy guard.
- **Maps to:** BUILD.md Phases 1-3.
- **Metric:** classification accuracy + **did-it-fold rate** (the signature metric).
- **Keep yours:** the eval methodology and the anti-sycophancy discipline. These are
  judgment + taste, not plumbing — they don't commoditize.

### 2. Persistent memory & learning over time  — *promote this early*
- **What:** continuity across sessions — remembers your projects, your positions,
  your patterns; accumulates knowledge; can say "I argued X last week, has Z changed?"
- **Why AGI-associated:** a bare LLM is amnesiac. Memory is what lets a system
  *grow* with you instead of resetting. It's also what makes Ekansh a JARVIS rather
  than a chatbot — personality-critical, not just infrastructure.
- **How:** start with a lightweight persistent store (JSON/SQLite) of positions +
  reasoning + falsifiers; graduate to Postgres + pgvector for semantic recall only
  when the simple store hurts. Store: position, why, falsifier, timestamp, outcome.
- **Maps to:** BUILD.md Phase 4 — but moved up; it's a winning axis, not a footnote.
- **Metric:** recall precision (does it surface the *right* past position?) +
  "stale-belief catch rate" (does it flag when a past position is now falsified?).
- **Keep yours:** the *personalization to Ritu specifically* — a product built for a
  billion people can't do this; a system built for one person can.

### 3. Long-horizon autonomy  — *the biggest "feels like AGI" multiplier*
- **What:** pursues a goal across many steps without hand-holding; the proactive
  "reaches out first" Ekansh is a primitive instance.
- **Why AGI-associated:** agency over a horizon — plan, act, observe, replan — is the
  single property that most separates "agent" from "autocomplete." Pure architecture;
  no weights needed.
- **How:** an agentic loop (plan -> act -> observe -> revise, capped to avoid drift),
  plus the heartbeat for proactivity. Gate the heartbeat hard (cost + signal bar) —
  see the cost note in `src/persona.py`.
- **Maps to:** new workstream; overlaps the server phase and the persona's
  `initiates` / `interrupts` behavior.
- **Metric:** task-completion rate on multi-step goals; false-alarm rate on proactive
  pings (how often it buzzes you for nothing — lower is better).
- **Keep yours:** the *judgment about when to act vs. ask* — calibrated autonomy is
  rare and hard; that's the moat, not the loop itself.

### 4. Tool-grounding  — *acting on the world, not just talking about it*
- **What:** runs code, searches, reads/writes files, calls APIs, and feeds results
  back into its reasoning.
- **Why AGI-associated:** grounding — closing the loop between reasoning and
  consequence — is a real cognitive property and 100% scaffold-level. It's also what
  turns "gives advice" into "does the thing."
- **How:** the Claude API tool-use loop (tool runner or manual loop). Start with a
  small, safe tool surface (web search, code execution, file read/write); gate
  destructive tools behind confirmation.
- **Maps to:** new workstream; clean to add once the graph runs.
- **Metric:** tool-task success rate; safety-gate correctness on tool calls
  (it must not run a destructive tool it shouldn't).
- **Keep yours:** the *defensive posture* — which tools are gated, how intent is
  checked. That's the same intent+uplift line the safety gate already enforces.

### 5. Primitive self-improvement loop  — *the closest you get to touching the brain*
- **What:** the Path-A pipeline generates its own training data; you fine-tune an
  open model on the good traces and swap it in as the brain.
- **Why AGI-associated:** a system that produces its own training data and gets
  better from it is a baby version of recursive self-improvement — the most
  AGI-shaped thing in the whole project. (Honest limit: it adds *specialization and
  character into weights*, not *generality*.)
- **How:** `finetune/prepare_traces.py` -> QLoRA an open model (Qwen / Gemma) on your
  debate transcripts -> point `src/models.py` at it -> **re-run the same eval set** to
  prove the tuned brain held its calibration.
- **Maps to:** BUILD.md Phase 5.
- **Metric:** the before/after eval table — does the tuned model match or beat the
  API brain on classification accuracy and did-it-fold rate?
- **Keep yours:** this is the literal definition of "mine" — a brain trained on data
  your own architecture produced. Uncommoditizable by construction.

---

## Sequencing — how this folds into the build

The capabilities re-rank the original phase order, because the *winning axes*
(calibration, memory, autonomy) should come before the depth-engine polish.

```
Month 0   Scaffold: git, models.py, stub graph, eval harness runs end-to-end
Month 1   Eval set (50-80 items) + a trustworthy did-it-fold SCORER   [Cap 1 instrument]
Month 2   Classifier real + calibration reliability curve             [Cap 1]
Month 3   Memory: lightweight persistent store + stale-belief catch   [Cap 2]  <-- promoted
Month 4   Anti-sycophancy guard (hold vs. update)                     [Cap 1 heart]
Month 5   Agentic loop + proactive heartbeat (gated)                  [Cap 3]
Month 6   Tool-grounding (small safe surface, gated)                  [Cap 4]
Month 7   Debate loop polish + A/B it honestly (does it even help?)
Month 8+  Self-improvement: traces -> QLoRA -> swap -> re-eval        [Cap 5]
```

Two metrics gate everything, re-run every iteration (they regress silently):
**classification accuracy** (is it calibrated?) and **did-it-fold rate** (does it
hold under weak pushback?). Per-capability metrics are listed above.

---

## The paragraph you can actually put in a README or defense

> Ekansh is a calibrated reasoning agent built on a frontier base model. It does not
> claim general intelligence — generality lives in the model's weights and is
> inherited, not added. What it builds on top is a bundle of AGI-*associated*
> capabilities: self-correction and calibration (it commits, survives self-attack,
> and won't fold to weak pushback), persistent memory (it accumulates and revisits
> its own past positions), long-horizon autonomy (it pursues multi-step goals and
> reaches out proactively), tool-grounding (it acts on the world and feeds results
> back), and a primitive self-improvement loop (it fine-tunes on traces its own
> pipeline generated). On its chosen axes — calibration, honesty, character, and
> personalization to one user — it aims to beat general-purpose flagship assistants,
> while remaining strictly worse on raw capability, which it rents from its brain.
