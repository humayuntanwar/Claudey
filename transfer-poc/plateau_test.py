"""Pre-registered prediction test (prediction written before this was run):

  The three original games have p_flat <= 0.06; group_word has p_flat = 0.58.
  PREDICTION: adding a plateau-heavy game (Tower of Hanoi) to the training set
  raises zero-shot transfer to group_word (higher T than games-only, mean of
  3 seeds), while not destroying transfer to planted_3sat.
  The run fails the prediction if T(group_word) does not improve.
"""
import json
import statistics
from multiprocessing import Pool

import experiment as X
from domains import GAMES, MATH
from transfer_matrix import fingerprint, eval_math


def main():
    R = json.load(open("results.json"))
    greedy = {d: R["eval"]["greedy"][d]["mean_cost"] for d in MATH}
    games_only = {d: statistics.fmean(greedy[d] - R["eval"][f"games[{s}]"][d]["mean_cost"] for s in range(3))
                  for d in MATH}
    out = {"fingerprint_hanoi": None, "games_only": games_only}
    with Pool(4) as pool:
        out["fingerprint_hanoi"] = pool.apply(fingerprint, ("hanoi",))
        print("hanoi fingerprint", out["fingerprint_hanoi"], flush=True)
        for label, train in [("games+hanoi", list(GAMES) + ["hanoi"]), ("hanoi_only", ["hanoi"])]:
            per = {d: [] for d in MATH}
            for seed in range(3):
                w, _ = X.cem(pool, train, 300 + seed, lambda m: None)
                for d, c in pool.map(eval_math, [(w, d) for d in MATH]):
                    per[d].append(greedy[d] - c)
            out[label] = {d: statistics.fmean(v) for d, v in per.items()}
            out[label + "_seeds"] = per
            print(label, {d: round(v, 3) for d, v in out[label].items()}, flush=True)

    L = ["\n## Pre-registered test: add a plateau-heavy game\n",
         "Prediction (written before running): adding Tower of Hanoi (plateau-heavy) to training "
         "improves zero-shot transfer to group_word.\n",
         "Hanoi fingerprint: " + ", ".join(f"{k}={v:.3f}" for k, v in out["fingerprint_hanoi"].items()) + "\n",
         "| training set | " + " | ".join(MATH) + " |", "|---" * (len(MATH) + 1) + "|"]
    for label in ("games_only", "games+hanoi", "hanoi_only"):
        L.append(f"| {label} | " + " | ".join(f"{out[label][d]:+.2f}" for d in MATH) + " |")
    verdict = "CONFIRMED" if out["games+hanoi"]["group_word"] > games_only["group_word"] else "FALSIFIED"
    L.append(f"\nT = greedy cost − controller cost (mean of 3 seeds; positive = helped). Prediction: **{verdict}**.\n")
    open("RESULTS.md", "a").write("\n".join(L) + "\n")
    json.dump(out, open("plateau_test.json", "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
