# Search-controller transfer: games → math (PoC)

**Question.** If game training really transfers to mathematics, *what* is it that
transfers? This PoC tests one concrete answer: **search control**, meaning when to
trust a heuristic, when to explore, and when to abandon a line, as distinct from
knowledge of any particular domain.

**Concept.** A 7-weight *search controller* that never sees states, moves, or
heuristic units. It sees only dimensionless signals about the search itself
(relative heuristic, local gain, depth vs. best node, plateau crowding,
sibling rank, stall time, stall × depth) and orders a best-first frontier.
Because the inputs are domain-free, the same weights run unchanged in any domain.
Transfer can then be measured cleanly:

1. Train the controller with CEM **only on games** (15-puzzle, Lights Out, deceptive mazes).
2. Freeze it and run it **zero-shot on math search problems**: Countdown arithmetic
   synthesis, a group word problem in S₁₃ (TopSpin generators), and planted 3-SAT.
3. Compare against classic search (greedy, A*, weighted A*), random controllers,
   and an *oracle* controller trained directly on each math domain.

Everything is pure Python (stdlib only) and runs on 4 cores in about 30 minutes.

```
python3 experiment.py        # main run  -> results.json   (~22 min)
python3 report.py            # -> RESULTS.md (main tables)
python3 transfer_matrix.py   # single-game transfer + landscape fingerprints (appends)
python3 plateau_test.py      # pre-registered prediction test (appends)
python3 plateau_posthoc.py   # exploratory follow-ups (append)
python3 sensitivity.py
python3 ablation.py
```

Full tables: [RESULTS.md](RESULTS.md).

## Findings

Cost is the mean of log(1+expansions), with failure = log(1+budget)+1, on 40
held-out instances per domain. T = greedy cost − controller cost (positive = helped).

**1. The controller learns real skill in the games.** In-distribution it beats
every classic baseline: Lights Out cost 5.95 → 4.6, 15-puzzle solve rate 80% → ~99%.
Random controllers are far worse everywhere, so the gains come from learning.

**2. Zero-shot transfer to math is selective, not general.**

| math domain | best classic | games-trained (3 seeds) | oracle |
|---|---|---|---|
| planted 3-SAT | 7.92 | **7.74** (beats every classic baseline; closes 30% of the gap to oracle) | 7.33 |
| Countdown | 2.90 | 3.75 (worse) | 2.93 |
| group word | 5.91 | 7.05 (much worse) | 6.00 |

What the games taught helps on SAT, roughly breaks even with greedy on Countdown,
and clearly hurts on the group word problem.

**3. Cheap landscape fingerprints correlate with transfer, but the prediction
built on them failed.** Each domain gets a fingerprint from plain greedy search:
fractions of moves that improve, tie, or worsen h, step size, and branching. The
distance between a game's fingerprint and a math problem's fingerprint correlated
with transfer (Spearman −0.80, 9 pairs). Group word stood out: 58% of its moves
are plateau moves, against ≤6% in every game. That led to a **pre-registered**
prediction, committed to git before the run: *adding a plateau-heavy game (Tower of
Hanoi) will improve transfer to group word.* **Falsified.** It also failed in a
post-hoc rerun with an easier, fully learnable Hanoi (−1.14 → −1.24 / −1.35). The
fingerprint correlation was most likely driven by group word being an outlier.

**4. Three further simple explanations also fail.** Weight-vector similarity to
the oracle doesn't predict transfer: games-trained controllers point closest to
the group-word oracle (cosine 0.94) and still transfer worst there. Group word
isn't uniquely sensitive to perturbing the controller. No single feature carries
the harm; removing sibling-rank recovers the most (−1.14 → −0.68).

## Takeaway

- In this setting, interactive training does produce domain-free search skill.
  That skill does carry across to a structurally different math problem (SAT).
- It is not a general reasoning upgrade. The same skill hurts on a nearby problem.
  The cheap explanations I tried (landscape similarity, weight similarity,
  sensitivity, single habits) don't predict when, and the one prediction I
  committed to before running failed.
- For the rumor framing: "skills from games transfer to math" is plausible at
  this toy scale, but **selective**. Any claim of broad transfer should come with
  a transfer matrix showing which source helps which target, and with negative
  cases. Without that, it is an anecdote.

## Limitations

This is a toy: a 7-parameter linear controller, three games, three math
domains, and n=40 test instances. CEM budgets are small and n=9 for the
correlation. Hanoi was chosen after seeing the fingerprints, by design, as a test
of the fingerprint idea. The post-hoc runs (6-disk Hanoi, sensitivity, ablation)
are exploratory. None of this says anything about what frontier labs are actually doing.
