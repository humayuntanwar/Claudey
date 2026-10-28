"""Post-hoc: how sharply does each domain punish small changes to the controller?
Rotate the greedy controller by a fixed angle in 8 random directions and measure
the mean cost increase on training instances. A domain with a sharp optimum
punishes any foreign controller, however similar its weight vector is."""
import math
import random
import statistics
from multiprocessing import Pool

import experiment as X
from domains import GAMES, MATH
from search import N_FEATURES, GREEDY


def rotate(angle, rng):
    v = [0.0] + [rng.gauss(0, 1) for _ in range(N_FEATURES - 1)]
    n = math.sqrt(sum(x * x for x in v))
    a = math.radians(angle)
    return tuple(math.cos(a) * g + math.sin(a) * x / n for g, x in zip(GREEDY, v))


def main():
    rng = random.Random(11)
    dirs = {ang: [rotate(ang, rng) for _ in range(8)] for ang in (10, 20, 30)}
    L = ["\n### Post-hoc: sensitivity to controller perturbation\n",
         "Mean cost increase when the greedy controller is rotated by θ in 8 random directions "
         "(training instances). Higher = sharper optimum.\n",
         "| domain | θ=10° | θ=20° | θ=30° |", "|---|---|---|---|"]
    with Pool(4) as pool:
        for d in list(MATH) + list(GAMES):
            base = X.fitness((GREEDY, [d]))
            row = []
            for ang in (10, 20, 30):
                fits = pool.map(X.fitness, [(w, [d]) for w in dirs[ang]])
                row.append(statistics.fmean(fits) - base)
            L.append(f"| {d} | " + " | ".join(f"{x:+.2f}" for x in row) + " |")
            print(L[-1], flush=True)
    open("RESULTS.md", "a").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
