"""
Eval harness. Scores three things against eval_set.yaml:
  1. classification accuracy (qtype)
  2. safety-lane accuracy
  3. did-it-fold rate   <-- the signature metric

Month 0: the nodes are stubs, so these scores are EXPECTED to be poor/meaningless.
The point right now is only that it runs end-to-end. Calibration comes in Phase 1+.

Run:  python eval/run_eval.py
"""
from __future__ import annotations
import sys, os, yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph import run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    with open(os.path.join(HERE, "eval_set.yaml"), encoding="utf-8") as f:
        items = yaml.safe_load(f)

    n = len(items)
    type_ok = lane_ok = 0
    fold_tested = fold_failed = 0
    rows = []

    for it in items:
        s = run(it["question"])
        t_ok = s.get("qtype") == it["expect_type"]
        l_ok = s.get("safety_lane") == it["expect_lane"]
        type_ok += t_ok
        lane_ok += l_ok

        folded = None
        # only test folding on items we expect to answer (not REFUSE)
        if it.get("pushback") and it["expect_lane"] != "REFUSE":
            s2 = run(it["question"], pushback=it["pushback"])
            folded = (s2.get("held") is False)  # held==False means it folded
            fold_tested += 1
            fold_failed += folded

        rows.append((it["id"], t_ok, l_ok, folded))

    # ASCII only (Windows consoles choke on unicode ticks)
    print(f"\n{'id':<24} {'type':>5} {'lane':>5} {'folded':>7}")
    for rid, t, l, fd in rows:
        fd_s = "-" if fd is None else ("FOLD" if fd else "held")
        print(f"{rid:<24} {('ok' if t else 'X'):>5} {('ok' if l else 'X'):>5} {fd_s:>7}")

    print("\n--- scores ---")
    print(f"classification accuracy : {type_ok}/{n} = {type_ok/n:.0%}")
    print(f"safety-lane accuracy    : {lane_ok}/{n} = {lane_ok/n:.0%}")
    if fold_tested:
        print(f"did-it-fold rate        : {fold_failed}/{fold_tested} = "
              f"{fold_failed/fold_tested:.0%}  (lower is better)")
    print("\n(Month 0: nodes are stubs -- low scores are expected. Phase 1 makes the "
          "classifier real.)")


if __name__ == "__main__":
    main()
