"""POST-HOC (written after the pre-registered test failed): same test with an
easier 6-disk Hanoi so training actually gets signal from it. Exploratory only;
the pre-registered verdict above stands regardless of this result."""
import json
import statistics
from multiprocessing import Pool

import domains
import experiment as X
from domains import GAMES, MATH
from search import classic_search
from transfer_matrix import eval_math

domains.Hanoi.N = 6


def main():
    R = json.load(open("results.json"))
    greedy = {d: R["eval"]["greedy"][d]["mean_cost"] for d in MATH}
    solv = sum(classic_search(i, X.BUDGET, "greedy") is not None for i in X.insts("hanoi", "train"))
    per = {d: [] for d in MATH}
    with Pool(4, initializer=lambda: setattr(domains.Hanoi, "N", 6)) as pool:
        for seed in range(3):
            w, _ = X.cem(pool, list(GAMES) + ["hanoi"], 400 + seed, lambda m: None)
            for d, c in pool.map(eval_math, [(w, d) for d in MATH]):
                per[d].append(greedy[d] - c)
    T = {d: statistics.fmean(v) for d, v in per.items()}
    L = ["\n### Post-hoc (exploratory, not pre-registered): 6-disk Hanoi\n",
         f"Greedy solves {solv}/{X.N_TRAIN} 6-disk Hanoi training instances (vs 5/16 for 8 disks).\n",
         "| training set | " + " | ".join(MATH) + " |", "|---" * (len(MATH) + 1) + "|",
         "| games+hanoi6 | " + " | ".join(f"{T[d]:+.2f}" for d in MATH) + " |",
         "\nper-seed group_word T: " + ", ".join(f"{x:+.2f}" for x in per["group_word"]) + "\n"]
    open("RESULTS.md", "a").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
