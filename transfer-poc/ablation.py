"""Post-hoc: which learned habit from the games hurts group_word?
Zero out one feature weight at a time in each games-trained controller and
measure transfer T on the group_word and planted_3sat test sets."""
import json
import statistics
from multiprocessing import Pool

from transfer_matrix import eval_math

NAMES = ["h_rel", "gain", "depth_rel", "crowding", "sib_rank", "stall", "stall*depth"]


def main():
    R = json.load(open("results.json"))
    greedy = {d: R["eval"]["greedy"][d]["mean_cost"] for d in ("group_word", "planted_3sat")}
    ctrls = [R["controllers"][f"games[{s}]"]["w"] for s in range(3)]
    L = ["\n### Post-hoc: feature ablation of games-trained controllers\n",
         "T after zeroing one feature (mean of 3 games-trained controllers, test sets).\n",
         "| ablated | group_word T | planted_3sat T |", "|---|---|---|"]
    with Pool(4) as pool:
        for k in [None] + list(range(1, len(NAMES))):
            jobs = [(tuple(0.0 if i == k else x for i, x in enumerate(w)), d)
                    for w in ctrls for d in greedy]
            res = pool.map(eval_math, jobs)
            T = {d: statistics.fmean(greedy[d] - c for dd, c in res if dd == d) for d in greedy}
            L.append(f"| {'(none)' if k is None else NAMES[k]} | {T['group_word']:+.2f} | {T['planted_3sat']:+.2f} |")
            print(L[-1], flush=True)
    open("RESULTS.md", "a").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
