"""Turn results.json into a readable table + the headline transfer metric."""
import json
import statistics

from domains import GAMES, MATH

R = json.load(open("results.json"))
E = R["eval"]
B = R["config"]["budget"]
CLASSIC = ["greedy", "A*", "wA*(w=3)"]
GAMES_CTRL = sorted(k for k in E if k.startswith("games["))
RANDOM = sorted(k for k in E if k.startswith("random["))


def row(label, d):
    s = E[label][d]
    med = s["median_expansions_solved"]
    return f"| {label} | {s['solve_rate']*100:5.1f}% | {s['mean_cost']:.2f} | {med if med is not None else '-'} |"


lines = [f"Budget {B} expansions/instance, {R['config']['n_test']} held-out test instances per domain. "
         "Cost = mean log(1+expansions), failure = log(1+budget)+1; lower is better.\n"]
headline = []
for d in list(MATH) + list(GAMES):
    kind = "MATH (zero-shot for games-trained)" if d in MATH else "GAME (in-distribution)"
    lines += [f"\n### {d} — {kind}\n", "| controller | solved | cost | median exp. |", "|---|---|---|---|"]
    labels = CLASSIC + GAMES_CTRL + ([f"oracle:{d}"] if d in MATH else []) + RANDOM
    lines += [row(l, d) for l in labels]
    if d in MATH:
        base = min(E[c][d]["mean_cost"] for c in CLASSIC)
        games = statistics.fmean(E[g][d]["mean_cost"] for g in GAMES_CTRL)
        oracle = E[f"oracle:{d}"][d]["mean_cost"]
        rnd = statistics.fmean(E[r][d]["mean_cost"] for r in RANDOM)
        gap = (base - games) / (base - oracle) if base - oracle > 1e-9 else float("nan")
        headline.append((d, base, games, oracle, rnd, gap))

lines += ["\n## Headline: transfer from games to math\n",
          "gap closed = (best classic − games-trained) / (best classic − oracle). "
          "1.0 = games-trained controller as good as one trained on the math domain itself; "
          "0 = no better than the best hand-picked classic search; <0 = worse.\n",
          "| math domain | best classic | games-trained (mean of 3) | oracle | random ctrl | gap closed |",
          "|---|---|---|---|---|---|"]
lines += [f"| {d} | {b:.2f} | {g:.2f} | {o:.2f} | {r:.2f} | {gap:+.2f} |" for d, b, g, o, r, gap in headline]

lines += ["\n## Learned controller weights\n",
          "features: h_rel, gain, depth_rel, crowding, sib_rank, stall, stall×depth\n",
          "| controller | weights (normalized by |w|) |", "|---|---|"]
for k, c in R["controllers"].items():
    if k.startswith("random"):
        continue
    w = c["w"]
    n = sum(x * x for x in w) ** 0.5
    lines.append(f"| {k} | " + ", ".join(f"{x / n:+.2f}" for x in w) + " |")

open("RESULTS.md", "w").write("# Results\n\n" + "\n".join(lines) + "\n")
print("\n".join(lines))
