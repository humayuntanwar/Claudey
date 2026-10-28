"""Follow-up: WHICH game transfers to WHICH math problem, and can we predict it
before training from a cheap fingerprint of each domain's search landscape?

1. Train one controller per single game (2 CEM seeds each).
2. Transfer score T(game, math) = greedy cost - controller cost on math test set
   (positive = training on that game helped zero-shot).
3. Landscape fingerprint per domain, measured with 300 greedy expansions on
   training instances (no learning involved):
     p_better, p_flat, p_worse   fraction of children that improve / tie / worsen h
     step      mean |dh| / h(start)
     branch    log mean branching factor
4. Spearman correlation between fingerprint distance(game, math) and T.
"""
import heapq
import json
import math
import statistics
from multiprocessing import Pool

import experiment as X
from domains import GAMES, MATH
from search import controller_search, cost


def fingerprint(name):
    better = flat = worse = 0
    steps, branch = [], []
    for inst in X.insts(name, "train"):
        h0 = inst.h(inst.start)
        open_, seen, n = [(h0, 0, inst.start)], {inst.start}, 0
        while open_ and n < 300:
            hp, _, s = heapq.heappop(open_)
            n += 1
            kids = inst.expand(s)
            branch.append(len(kids))
            for c, hc in kids:
                better += hc < hp; flat += hc == hp; worse += hc > hp
                steps.append(abs(hc - hp) / h0)
                if c not in seen:
                    seen.add(c); heapq.heappush(open_, (hc, n * 1000 + len(seen), c))
    tot = better + flat + worse
    return {"p_better": better / tot, "p_flat": flat / tot, "p_worse": worse / tot,
            "step": statistics.fmean(steps), "branch": math.log(statistics.fmean(branch))}


def eval_math(args):
    w, d = args
    return d, statistics.fmean(cost(controller_search(i, w, X.BUDGET), X.BUDGET) for i in X.insts(d, "test"))


def spearman(a, b):
    ra = {i: r for r, i in enumerate(sorted(range(len(a)), key=a.__getitem__))}
    rb = {i: r for r, i in enumerate(sorted(range(len(b)), key=b.__getitem__))}
    n = len(a)
    return 1 - 6 * sum((ra[i] - rb[i]) ** 2 for i in range(n)) / (n * (n * n - 1))


def main():
    R = json.load(open("results.json"))
    greedy = {d: R["eval"]["greedy"][d]["mean_cost"] for d in MATH}
    T = {}
    with Pool(4) as pool:
        for g in GAMES:
            scores = {d: [] for d in MATH}
            for seed in (0, 1):
                w, _ = X.cem(pool, [g], 200 + seed, lambda m: None)
                for d, c in pool.map(eval_math, [(w, d) for d in MATH]):
                    scores[d].append(greedy[d] - c)
            T[g] = {d: statistics.fmean(v) for d, v in scores.items()}
            print(g, {d: round(v, 3) for d, v in T[g].items()}, flush=True)
        fps = dict(zip(list(GAMES) + list(MATH), pool.map(fingerprint, list(GAMES) + list(MATH))))

    keys = list(next(iter(fps.values())))
    sd = {k: statistics.pstdev(fp[k] for fp in fps.values()) or 1 for k in keys}
    dist = lambda a, b: math.sqrt(sum(((fps[a][k] - fps[b][k]) / sd[k]) ** 2 for k in keys))
    pairs = [(g, d, dist(g, d), T[g][d]) for g in GAMES for d in MATH]
    rho = spearman([p[2] for p in pairs], [p[3] for p in pairs])

    L = ["\n## Follow-up: single-game transfer matrix\n",
         "T = greedy cost − controller cost on the math test set (mean of 2 CEM seeds). Positive = helped.\n",
         "| trained on ↓ / tested on → | " + " | ".join(MATH) + " |", "|---" * (len(MATH) + 1) + "|"]
    L += [f"| {g} | " + " | ".join(f"{T[g][d]:+.2f}" for d in MATH) + " |" for g in GAMES]
    L += ["\n### Landscape fingerprints (measured with plain greedy search, no learning)\n",
          "| domain | " + " | ".join(keys) + " |", "|---" * (len(keys) + 1) + "|"]
    L += [f"| {n} | " + " | ".join(f"{fp[k]:.3f}" for k in keys) + " |" for n, fp in fps.items()]
    L += ["\n| game → math | fingerprint distance | transfer T |", "|---|---|---|"]
    L += [f"| {g} → {d} | {di:.2f} | {t:+.2f} |" for g, d, di, t in sorted(pairs, key=lambda p: p[2])]
    L += [f"\nSpearman(distance, transfer) = **{rho:+.2f}** over {len(pairs)} pairs "
          "(negative = closer landscapes transfer better). n=9, so this is a hint, not a result.\n"]
    open("RESULTS.md", "a").write("\n".join(L) + "\n")
    json.dump({"T": T, "fingerprints": fps, "spearman": rho}, open("transfer_matrix.json", "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
