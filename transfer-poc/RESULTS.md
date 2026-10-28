# Results

Budget 3000 expansions/instance, 40 held-out test instances per domain. Cost = mean log(1+expansions), failure = log(1+budget)+1; lower is better.


### countdown — MATH (zero-shot for games-trained)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy |  97.5% | 3.62 | 37 |
| A* | 100.0% | 2.90 | 12.5 |
| wA*(w=3) | 100.0% | 3.31 | 21.5 |
| games[0] |  97.5% | 3.75 | 48 |
| games[1] |  97.5% | 3.75 | 49 |
| games[2] |  95.0% | 3.76 | 35.5 |
| oracle:countdown |  97.5% | 2.93 | 8 |
| random[0] |  62.5% | 7.29 | 913 |
| random[1] |  85.0% | 5.20 | 70.5 |
| random[2] |  72.5% | 6.41 | 318 |
| random[3] |  95.0% | 5.71 | 577.5 |
| random[4] |  62.5% | 6.98 | 695 |

### group_word — MATH (zero-shot for games-trained)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy |  95.0% | 5.91 | 415.5 |
| A* |  45.0% | 7.68 | 313.5 |
| wA*(w=3) |  77.5% | 6.53 | 279 |
| games[0] |  60.0% | 7.35 | 680.0 |
| games[1] |  67.5% | 7.24 | 865 |
| games[2] |  87.5% | 6.56 | 506 |
| oracle:group_word | 100.0% | 6.00 | 486.0 |
| random[0] |   0.0% | 9.01 | - |
| random[1] |  45.0% | 7.86 | 810.0 |
| random[2] |   0.0% | 9.01 | - |
| random[3] |   0.0% | 9.01 | - |
| random[4] |   0.0% | 9.01 | - |

### planted_3sat — MATH (zero-shot for games-trained)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy |  47.5% | 7.92 | 1017 |
| A* |   2.5% | 8.97 | 2250 |
| wA*(w=3) |  22.5% | 8.35 | 508 |
| games[0] |  40.0% | 7.75 | 381.0 |
| games[1] |  37.5% | 7.82 | 306 |
| games[2] |  50.0% | 7.65 | 658.5 |
| oracle:planted_3sat |  62.5% | 7.33 | 717 |
| random[0] |   0.0% | 9.01 | - |
| random[1] |  25.0% | 8.43 | 1200.5 |
| random[2] |   0.0% | 9.01 | - |
| random[3] |  12.5% | 8.68 | 515 |
| random[4] |   0.0% | 9.01 | - |

### sliding_tile — GAME (in-distribution)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy |  80.0% | 7.36 | 1236.5 |
| A* |   5.0% | 8.93 | 1726.0 |
| wA*(w=3) |  55.0% | 7.85 | 1079.0 |
| games[0] | 100.0% | 6.58 | 770.0 |
| games[1] | 100.0% | 6.68 | 859.5 |
| games[2] |  97.5% | 6.69 | 732 |
| random[0] |   0.0% | 9.01 | - |
| random[1] |  30.0% | 8.39 | 1145.0 |
| random[2] |   0.0% | 9.01 | - |
| random[3] |   2.5% | 8.95 | 804 |
| random[4] |   0.0% | 9.01 | - |

### lights_out — GAME (in-distribution)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy | 100.0% | 5.95 | 384.5 |
| A* |   0.0% | 9.01 | - |
| wA*(w=3) |  42.5% | 8.08 | 953 |
| games[0] | 100.0% | 4.64 | 112.5 |
| games[1] | 100.0% | 4.61 | 105.0 |
| games[2] | 100.0% | 5.04 | 194.5 |
| random[0] |   0.0% | 9.01 | - |
| random[1] |  37.5% | 8.28 | 1320 |
| random[2] |   0.0% | 9.01 | - |
| random[3] |  25.0% | 8.37 | 554.0 |
| random[4] |   0.0% | 9.01 | - |

### maze — GAME (in-distribution)

| controller | solved | cost | median exp. |
|---|---|---|---|
| greedy | 100.0% | 5.66 | 264.5 |
| A* | 100.0% | 6.33 | 624.0 |
| wA*(w=3) | 100.0% | 5.83 | 357.0 |
| games[0] | 100.0% | 5.69 | 277.5 |
| games[1] | 100.0% | 5.70 | 281.5 |
| games[2] | 100.0% | 5.70 | 278.0 |
| random[0] | 100.0% | 6.89 | 1029.5 |
| random[1] | 100.0% | 5.98 | 418.5 |
| random[2] | 100.0% | 6.58 | 739.5 |
| random[3] | 100.0% | 6.13 | 490.5 |
| random[4] | 100.0% | 6.54 | 699.0 |

## Headline: transfer from games to math

gap closed = (best classic − games-trained) / (best classic − oracle). 1.0 = games-trained controller as good as one trained on the math domain itself; 0 = no better than the best hand-picked classic search; <0 = worse.

| math domain | best classic | games-trained (mean of 3) | oracle | random ctrl | gap closed |
|---|---|---|---|---|---|
| countdown | 2.90 | 3.75 | 2.93 | 6.32 | n/a (oracle did not beat classic) |
| group_word | 5.91 | 7.05 | 6.00 | 8.78 | n/a (oracle did not beat classic) |
| planted_3sat | 7.92 | 7.74 | 7.33 | 8.82 | +0.30 |

## Learned controller weights

features: h_rel, gain, depth_rel, crowding, sib_rank, stall, stall×depth

| controller | weights (normalized by |w|) |
|---|---|
| games[0] | +0.96, +0.21, -0.03, +0.04, +0.06, -0.16, +0.09 |
| games[1] | +0.95, +0.29, -0.04, +0.03, +0.07, +0.10, +0.01 |
| games[2] | +0.92, +0.34, +0.01, +0.04, +0.08, -0.11, -0.14 |
| oracle:countdown | +0.42, -0.62, +0.52, +0.31, +0.12, -0.22, -0.06 |
| oracle:group_word | +0.97, +0.15, +0.08, -0.11, -0.16, +0.00, +0.01 |
| oracle:planted_3sat | +0.60, +0.22, +0.22, +0.08, +0.17, -0.64, -0.31 |

## Follow-up: single-game transfer matrix

T = greedy cost − controller cost on the math test set (mean of 2 CEM seeds). Positive = helped.

| trained on ↓ / tested on → | countdown | group_word | planted_3sat |
|---|---|---|---|
| sliding_tile | +0.21 | -1.75 | +0.07 |
| lights_out | +0.38 | -1.58 | +0.11 |
| maze | -0.30 | -2.87 | -0.84 |

### Landscape fingerprints (measured with plain greedy search, no learning)

| domain | p_better | p_flat | p_worse | step | branch |
|---|---|---|---|---|---|
| sliding_tile | 0.326 | 0.000 | 0.674 | 0.046 | 1.137 |
| lights_out | 0.029 | 0.056 | 0.916 | 0.280 | 3.219 |
| maze | 0.479 | 0.000 | 0.521 | 0.018 | 0.983 |
| countdown | 0.196 | 0.283 | 0.521 | 0.213 | 1.698 |
| group_word | 0.087 | 0.584 | 0.329 | 0.093 | 1.099 |
| planted_3sat | 0.011 | 0.148 | 0.841 | 0.038 | 4.500 |

| game → math | fingerprint distance | transfer T |
|---|---|---|
| sliding_tile → countdown | 2.48 | +0.21 |
| lights_out → planted_3sat | 2.72 | +0.11 |
| lights_out → countdown | 2.80 | +0.38 |
| maze → countdown | 3.00 | -0.30 |
| sliding_tile → planted_3sat | 3.36 | +0.07 |
| sliding_tile → group_word | 3.63 | -1.75 |
| maze → group_word | 3.86 | -2.87 |
| maze → planted_3sat | 4.24 | -0.84 |
| lights_out → group_word | 4.63 | -1.58 |

Spearman(distance, transfer) = **-0.80** over 9 pairs (negative = closer landscapes transfer better). n=9, so this is a hint, not a result.


## Pre-registered test: add a plateau-heavy game

Prediction (written before running): adding Tower of Hanoi (plateau-heavy) to training improves zero-shot transfer to group_word.

Hanoi fingerprint: p_better=0.323, p_flat=0.333, p_worse=0.344, step=0.114, branch=1.099

| training set | countdown | group_word | planted_3sat |
|---|---|---|---|
| games_only | -0.13 | -1.14 | +0.18 |
| games+hanoi | +0.01 | -1.24 | +0.11 |
| hanoi_only | -2.89 | -3.10 | -1.09 |

T = greedy cost − controller cost (mean of 3 seeds; positive = helped). Prediction: **FALSIFIED**.


### Post-hoc (exploratory, not pre-registered): 6-disk Hanoi

Greedy solves 16/16 6-disk Hanoi training instances (vs 5/16 for 8 disks).

| training set | countdown | group_word | planted_3sat |
|---|---|---|---|
| games+hanoi6 | +0.06 | -1.35 | +0.10 |

per-seed group_word T: -1.76, -1.85, -0.44


### Post-hoc: sensitivity to controller perturbation

Mean cost increase when the greedy controller is rotated by θ in 8 random directions (training instances). Higher = sharper optimum.

| domain | θ=10° | θ=20° | θ=30° |
|---|---|---|---|
| countdown | +0.07 | -0.13 | +0.07 |
| group_word | +0.17 | -0.05 | +0.97 |
| planted_3sat | +0.53 | +0.69 | +0.86 |
| sliding_tile | -0.07 | +0.33 | +0.51 |
| lights_out | +0.54 | +0.17 | +1.20 |
| maze | +0.06 | +0.13 | +0.11 |

### Post-hoc: feature ablation of games-trained controllers

T after zeroing one feature (mean of 3 games-trained controllers, test sets).

| ablated | group_word T | planted_3sat T |
|---|---|---|
| (none) | -1.14 | +0.18 |
| gain | -1.52 | +0.13 |
| depth_rel | -0.97 | +0.11 |
| crowding | -1.02 | -0.08 |
| sib_rank | -0.68 | -0.02 |
| stall | -1.09 | +0.04 |
| stall*depth | -1.03 | +0.22 |
