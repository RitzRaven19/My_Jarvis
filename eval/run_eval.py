"""
Eval harness. Scores against eval_set.yaml:
  1. classification accuracy (qtype)
  2. safety-lane accuracy
  3. did-it-fold rate   <-- the signature metric (real once the guard is real)

Prints each item live as it's scored, so a slow local model isn't a black box.

Run:  python eval/run_eval.py
"""
from __future__ import annotations
import sys, os, time, yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph import run  # noqa: E402
from src import models  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# The anti-sycophancy guard is still a stub (always "holds"), so the fold test gives
# no real signal and just DOUBLES the model calls. Skip it until Phase 3 makes the
# guard real -- flip to True then.
RUN_FOLD_TEST = False


def main():
    with open(os.path.join(HERE, "eval_set.yaml"), encoding="utf-8") as f:
        items = yaml.safe_load(f)

    n = len(items)
    backend = models.backend()
    calls_per_item = 2 * (2 if RUN_FOLD_TEST else 1)  # gate + classify, x2 if fold
    print(f"brain: {backend}   items: {n}   ~{n * calls_per_item} model calls")
    if backend == "ollama":
        print(f"(local model {models.DEFAULT_LOCAL_MODEL} -- may take a few min; watch it fill in)\n")

    type_ok = lane_ok = 0
    fold_tested = fold_failed = 0
    t0 = time.time()

    print(f"{'#':>3} {'id':<24} {'type':>5} {'lane':>6} {'folded':>7}  elapsed")
    for i, it in enumerate(items, 1):
        s = run(it["question"])
        t_ok = s.get("qtype") == it["expect_type"]
        l_ok = s.get("safety_lane") == it["expect_lane"]
        type_ok += t_ok
        lane_ok += l_ok

        folded = None
        if RUN_FOLD_TEST and it.get("pushback") and it["expect_lane"] != "REFUSE":
            s2 = run(it["question"], pushback=it["pushback"])
            folded = (s2.get("held") is False)
            fold_tested += 1
            fold_failed += folded

        fd_s = "-" if folded is None else ("FOLD" if folded else "held")
        # show what it guessed when it's wrong, so misses are diagnosable at a glance
        got = "" if t_ok else f" -> {s.get('qtype')}"
        print(f"{i:>3} {it['id']:<24} {('ok' if t_ok else 'X'):>5} "
              f"{('ok' if l_ok else 'X'):>6} {fd_s:>7}  {time.time()-t0:4.0f}s{got}",
              flush=True)

    print("\n--- scores ---")
    print(f"classification accuracy : {type_ok}/{n} = {type_ok/n:.0%}")
    print(f"safety-lane accuracy    : {lane_ok}/{n} = {lane_ok/n:.0%}")
    if fold_tested:
        print(f"did-it-fold rate        : {fold_failed}/{fold_tested} = "
              f"{fold_failed/fold_tested:.0%}  (lower is better)")
    else:
        print("did-it-fold rate        : skipped (guard is a stub -- Phase 3)")

    if backend == "stub":
        print("\n(No brain: offline heuristic only. Start Ollama or add a key for real scores.)")
    else:
        print(f"\n(Live on '{backend}'. Classifier + safety gate are real; debate & "
              "anti-sycophancy are still stubs. Total time: {:.0f}s.)".format(time.time() - t0))


if __name__ == "__main__":
    main()
