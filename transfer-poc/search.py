"""Best-first search driven by a tiny, domain-agnostic *search controller*.

The controller never sees states, moves, or heuristic units. It only sees
scale-free signals about the search itself, and scores each frontier node:

    priority = w . phi(node)        (lower = expand sooner)

phi (all dimensionless, so the same w can run in any domain):
  0 h_rel      h / h(start)                      how close the heuristic says we are
  1 gain       (h_parent - h) / h(start)          did this step make local progress?
  2 depth_rel  g / (1 + g_best)                   depth vs. depth of best node so far
  3 crowding   log(1+#nodes in same h-bin) / log(1+budget)   plateau pressure
  4 sib_rank   rank of h among siblings, in [0,1]  relative quality among alternatives
  5 stall      (expansions since last new best h) / budget   recency bias that switches on when stuck
  6 stall*depth  interaction: when stuck, prefer shallow (restart-like) or deep (commit) nodes
"""
import heapq
import math

N_FEATURES = 7
GREEDY = (1.0, 0, 0, 0, 0, 0, 0)


def controller_search(inst, w, budget):
    """Returns number of expansions to find the goal, or None if budget exhausted."""
    s0 = inst.start
    h0 = inst.h(s0)
    if h0 == 0:
        return 0
    inv_h0 = 1.0 / h0
    log_b = math.log1p(budget)
    w0, w1, w2, w3, w4, w5, w6 = w
    bins = {}
    open_ = [(0.0, 0, s0, 0, h0)]
    seen = {s0}
    best_h, best_g, last_improve = h0, 0, 0
    tick = 0
    exp = 0
    while open_ and exp < budget:
        _, _, s, g, hp = heapq.heappop(open_)
        exp += 1
        kids = [(c, hc) for c, hc in inst.expand(s) if c not in seen]
        if not kids:
            continue
        order = sorted(range(len(kids)), key=lambda i: kids[i][1])
        denom = max(1, len(kids) - 1)
        g1 = g + 1
        stall = (exp - last_improve) / budget
        for rank, i in enumerate(order):
            c, hc = kids[i]
            if hc == 0:
                return exp
            seen.add(c)
            hr = hc * inv_h0
            b = int(hr * 40)
            cnt = bins.get(b, 0) + 1
            bins[b] = cnt
            if hc < best_h:
                best_h, best_g, last_improve = hc, g1, exp
            dr = g1 / (1 + best_g)
            p = (w0 * hr + w1 * (hp - hc) * inv_h0 + w2 * dr
                 + w3 * math.log1p(cnt) / log_b + w4 * rank / denom
                 + w5 * stall + w6 * stall * dr)
            tick += 1
            heapq.heappush(open_, (p, tick, c, g1, hc))
    return None


def classic_search(inst, budget, kind, weight=1.0):
    """Baselines using raw (unit-ful) heuristic: 'greedy', 'astar' (g + weight*h)."""
    s0 = inst.start
    h0 = inst.h(s0)
    if h0 == 0:
        return 0
    open_ = [(0.0, 0, s0, 0)]
    seen = {s0}
    tick = exp = 0
    while open_ and exp < budget:
        _, _, s, g = heapq.heappop(open_)
        exp += 1
        for c, hc in inst.expand(s):
            if c in seen:
                continue
            if hc == 0:
                return exp
            seen.add(c)
            tick += 1
            p = hc if kind == "greedy" else (g + 1) + weight * hc
            heapq.heappush(open_, (p, tick, c, g + 1))
    return None


def cost(result, budget):
    """Per-instance cost: log expansions; failure costs log(budget) + 1."""
    return math.log1p(budget) + 1.0 if result is None else math.log1p(result)
