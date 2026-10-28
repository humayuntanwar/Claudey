"""Train search controllers with CEM and measure zero-shot transfer.

Conditions
  games[seed]     trained ONLY on sliding_tile + lights_out + maze      -> evaluated zero-shot on math
  oracle:<d>      trained on math domain d's own training instances      -> upper bound on d
  random          random controllers (null: does *learning* matter?)
  greedy / wA*    classic best-first baselines on raw heuristic units

Usage: python3 experiment.py            (writes results.json)
"""
import json
import math
import random
import statistics
import sys
import time
from multiprocessing import Pool

from domains import GAMES, MATH, make_instances
from search import N_FEATURES, GREEDY, controller_search, classic_search, cost

BUDGET = 3000
N_TRAIN, N_TEST = 16, 40
POP, ELITE, ITERS = 20, 5, 14

_cache = {}


def insts(name, split):
    key = (name, split)
    if key not in _cache:
        _cache[key] = make_instances(name, N_TRAIN if split == "train" else N_TEST, split)
    return _cache[key]


def fitness(args):
    w, domains = args
    per_domain = []
    for d in domains:
        per_domain.append(statistics.fmean(cost(controller_search(i, w, BUDGET), BUDGET)
                                           for i in insts(d, "train")))
    return statistics.fmean(per_domain)


def cem(pool, domains, seed, log):
    rng = random.Random(seed)
    mu = list(GREEDY)
    sigma = [1.0] * N_FEATURES
    best = (fitness((tuple(mu), domains)), tuple(mu))
    for it in range(ITERS):
        cands = [tuple(m + s * rng.gauss(0, 1) for m, s in zip(mu, sigma)) for _ in range(POP)]
        fits = pool.map(fitness, [(c, domains) for c in cands])
        ranked = sorted(zip(fits, cands))
        if ranked[0][0] < best[0]:
            best = ranked[0]
        elite = [c for _, c in ranked[:ELITE]]
        mu = [statistics.fmean(e[k] for e in elite) for k in range(N_FEATURES)]
        sigma = [max(0.05, statistics.pstdev(e[k] for e in elite)) for k in range(N_FEATURES)]
        log(f"  it {it:2d}  best-of-gen {ranked[0][0]:.3f}  best-ever {best[0]:.3f}")
    return best[1], best[0]


def eval_one(args):
    label, spec, d = args
    out = []
    for inst in insts(d, "test"):
        if spec[0] == "ctrl":
            r = controller_search(inst, spec[1], BUDGET)
        elif spec[0] == "greedy":
            r = classic_search(inst, BUDGET, "greedy")
        else:
            r = classic_search(inst, BUDGET, "astar", spec[1])
        out.append(r)
    return label, d, out


def summarize(results):
    solved = [r for r in results if r is not None]
    return {
        "solve_rate": len(solved) / len(results),
        "mean_cost": statistics.fmean(cost(r, BUDGET) for r in results),
        "median_expansions_solved": statistics.median(solved) if solved else None,
        "raw": results,
    }


def main():
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:7.1f}s] {m}", flush=True)
    controllers = {}
    with Pool(4) as pool:
        for seed in range(3):
            log(f"training games[{seed}] on {list(GAMES)}")
            w, f = cem(pool, list(GAMES), seed, log)
            controllers[f"games[{seed}]"] = {"w": w, "train_fit": f, "trained_on": list(GAMES)}
        for d in MATH:
            log(f"training oracle:{d}")
            w, f = cem(pool, [d], 100, log)
            controllers[f"oracle:{d}"] = {"w": w, "train_fit": f, "trained_on": [d]}

        rng = random.Random(7)
        for k in range(5):
            controllers[f"random[{k}]"] = {"w": tuple(rng.gauss(0, 1) for _ in range(N_FEATURES)),
                                           "trained_on": []}

        specs = {name: ("ctrl", c["w"]) for name, c in controllers.items()}
        specs["greedy"] = ("greedy",)
        specs["A*"] = ("astar", 1.0)
        specs["wA*(w=3)"] = ("astar", 3.0)

        jobs = [(label, spec, d) for label, spec in specs.items() for d in list(MATH) + list(GAMES)
                if not (label.startswith("oracle:") and label.split(":")[1] != d)]
        log(f"evaluating {len(jobs)} (controller, domain) pairs on held-out test instances")
        evals = {}
        for label, d, res in pool.imap_unordered(eval_one, jobs):
            evals.setdefault(label, {})[d] = summarize(res)

    out = {"config": {"budget": BUDGET, "n_train": N_TRAIN, "n_test": N_TEST,
                      "pop": POP, "elite": ELITE, "iters": ITERS},
           "controllers": controllers, "eval": evals}
    json.dump(out, open("results.json", "w"), indent=1)
    log("wrote results.json")


if __name__ == "__main__":
    main()
