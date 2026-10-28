"""Search domains. Every domain exposes the same tiny interface:

    inst.start            -> hashable start state
    inst.h(state)         -> cheap, imperfect heuristic (>= 0, == 0 iff goal)
    inst.expand(state)    -> list of (child_state, child_h)

Heuristics are in *domain-specific units* on purpose: a transferable
controller must not rely on what one unit of h means.

GAMES (training only):   sliding-tile, lights-out, maze
MATH  (held-out tests):  countdown arithmetic, group-word (TopSpin generators), planted 3-SAT
"""
import math
import random
from collections import deque

# ----------------------------------------------------------------- games

class SlidingTile:
    """15-puzzle. h = Manhattan distance (in moves)."""
    N = 4
    NEIGH = None

    def __init__(self, rng, scramble=(35, 70)):
        n = self.N
        if SlidingTile.NEIGH is None:
            SlidingTile.NEIGH = [
                [r * n + c for r, c in ((i // n - 1, i % n), (i // n + 1, i % n),
                                        (i // n, i % n - 1), (i // n, i % n + 1))
                 if 0 <= r < n and 0 <= c < n] for i in range(n * n)]
        s = list(range(1, n * n)) + [0]
        b, prev = n * n - 1, -1
        for _ in range(rng.randint(*scramble)):
            nb = rng.choice([x for x in self.NEIGH[b] if x != prev])
            s[b], s[nb] = s[nb], s[b]
            prev, b = b, nb
        self.start = tuple(s)

    def h(self, s):
        n, d = self.N, 0
        for i, t in enumerate(s):
            if t:
                g = t - 1
                d += abs(i // n - g // n) + abs(i % n - g % n)
        return d

    def expand(self, s):
        b = s.index(0)
        out = []
        for nb in self.NEIGH[b]:
            c = list(s)
            c[b], c[nb] = c[nb], 0
            c = tuple(c)
            out.append((c, self.h(c)))
        return out


class LightsOut:
    """5x5 Lights Out. h = lit cells / 5 (each press toggles <= 5)."""
    N = 5
    MASKS = None

    def __init__(self, rng, presses=(7, 11)):
        n = self.N
        if LightsOut.MASKS is None:
            LightsOut.MASKS = []
            for i in range(n * n):
                m = 1 << i
                r, c = divmod(i, n)
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < n and 0 <= cc < n:
                        m |= 1 << (rr * n + cc)
                LightsOut.MASKS.append(m)
        s = 0
        for i in rng.sample(range(n * n), rng.randint(*presses)):
            s ^= self.MASKS[i]
        self.start = s

    def h(self, s):
        return bin(s).count("1") / 5.0

    def expand(self, s):
        return [(s ^ m, bin(s ^ m).count("1") / 5.0) for m in self.MASKS]


class Maze:
    """Grid maze with random walls and dead ends. h = Manhattan to exit."""

    def __init__(self, rng, size=45, wall=0.36):
        while True:
            walls = {(r, c) for r in range(size) for c in range(size) if rng.random() < wall}
            # deceptive barrier: a wall band in the middle with a single gap far from the line of sight
            mid = size // 2
            gap = rng.choice([1, size - 2])
            for c in range(size):
                if c != gap:
                    walls.add((mid, c))
            walls.discard((mid, gap))
            a, b = (0, rng.randrange(size)), (size - 1, rng.randrange(size))
            walls.discard(a); walls.discard(b)
            if self._reachable(walls, size, a, b):
                break
        self.walls, self.size, self.goal, self.start = walls, size, b, a

    @staticmethod
    def _reachable(walls, n, a, b):
        q, seen = deque([a]), {a}
        while q:
            r, c = q.popleft()
            if (r, c) == b:
                return True
            for p in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= p[0] < n and 0 <= p[1] < n and p not in walls and p not in seen:
                    seen.add(p); q.append(p)
        return False

    def h(self, s):
        return abs(s[0] - self.goal[0]) + abs(s[1] - self.goal[1])

    def expand(self, s):
        r, c = s
        n = self.size
        return [(p, self.h(p)) for p in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
                if 0 <= p[0] < n and 0 <= p[1] < n and p not in self.walls]

# ------------------------------------------------------------------ math

class Countdown:
    """Reach a target integer by combining numbers with + - * / (exact).
    State = sorted tuple of remaining numbers. h = log(1 + min |n - target|)."""
    SMALL = list(range(1, 11)) * 2
    LARGE = [25, 50, 75, 100]

    def __init__(self, rng):
        while True:
            k = rng.randint(1, 2)
            nums = rng.sample(self.LARGE, k) + rng.sample(self.SMALL, 6 - k)
            # build a solvable target by actually playing 4-5 random operations
            pool = nums[:]
            rng.shuffle(pool)
            for _ in range(5):
                if len(pool) < 2:
                    break
                a, b = pool.pop(), pool.pop()
                opts = [a + b, a * b] + ([abs(a - b)] if a != b else []) + \
                       ([max(a, b) // min(a, b)] if min(a, b) > 1 and max(a, b) % min(a, b) == 0 else [])
                pool.append(rng.choice(opts))
            t = pool[-1]
            if 101 <= t <= 999 and t not in nums and len(pool) == 1:
                break
        self.target, self.start = t, tuple(sorted(nums))

    def h(self, s):
        return math.log1p(min(abs(n - self.target) for n in s))

    def expand(self, s):
        out, seen = [], set()
        L = len(s)
        for i in range(L):
            for j in range(i + 1, L):
                a, b = s[i], s[j]  # a <= b
                rest = s[:i] + s[i + 1:j] + s[j + 1:]
                res = [a + b, a * b]
                if b != a:
                    res.append(b - a)
                if a > 1 and b % a == 0:
                    res.append(b // a)
                for r in res:
                    c = tuple(sorted(rest + (r,)))
                    if c not in seen:
                        seen.add(c)
                        out.append((c, self.h(c)))
        return out


class GroupWord:
    """Word problem in S_n: express a permutation as a product of generators
    (rotate, rotate^-1, reverse-first-4; the TopSpin generating set).
    h = cyclic breakpoints + [0 not in position 0]; h == 0 iff identity."""
    N, K = 13, 4

    def __init__(self, rng, length=(40, 80)):
        p = tuple(range(self.N))
        for _ in range(rng.randint(*length)):
            p = rng.choice(self._gens(p))
        if p == tuple(range(self.N)):
            p = self._gens(p)[0]
        self.start = p

    def _gens(self, p):
        return [p[1:] + p[:1], p[-1:] + p[:-1], p[:self.K][::-1] + p[self.K:]]

    def h(self, p):
        n = self.N
        bp = sum(1 for i in range(n) if p[(i + 1) % n] != (p[i] + 1) % n)
        return bp + (p[0] != 0)

    def expand(self, p):
        return [(c, self.h(c)) for c in self._gens(p)]


class PlantedSAT:
    """Planted random 3-SAT. State = assignment bitmask, move = flip one var.
    h = number of unsatisfied clauses."""

    def __init__(self, rng, n=90, ratio=4.3):
        self.n = n
        sol = [rng.random() < 0.5 for _ in range(n)]
        clauses = []
        while len(clauses) < int(ratio * n):
            vs = rng.sample(range(n), 3)
            lits = [(v, rng.random() < 0.5) for v in vs]
            if any(sol[v] == pos for v, pos in lits):
                clauses.append(lits)
        self.clauses = clauses
        self.occ = [[] for _ in range(n)]
        for ci, cl in enumerate(clauses):
            for v, pos in cl:
                self.occ[v].append((ci, pos))
        self.start = rng.getrandbits(n)

    def _true_counts(self, s):
        return [sum(1 for v, pos in cl if ((s >> v) & 1) == pos) for cl in self.clauses]

    def h(self, s):
        return sum(1 for t in self._true_counts(s) if t == 0)

    def expand(self, s):
        tc = self._true_counts(s)
        h0 = sum(1 for t in tc if t == 0)
        out = []
        for v in range(self.n):
            val = (s >> v) & 1
            d = 0
            for ci, pos in self.occ[v]:
                if val == pos:           # literal was true, becomes false
                    if tc[ci] == 1:
                        d += 1
                else:                    # literal becomes true
                    if tc[ci] == 0:
                        d -= 1
            out.append((s ^ (1 << v), h0 + d))
        return out


GAMES = {"sliding_tile": SlidingTile, "lights_out": LightsOut, "maze": Maze}
MATH = {"countdown": Countdown, "group_word": GroupWord, "planted_3sat": PlantedSAT}
ALL = {**GAMES, **MATH}


def make_instances(name, count, seed):
    rng = random.Random(f"{name}:{seed}")
    return [ALL[name](rng) for _ in range(count)]


class Hanoi:
    """Tower of Hanoi from a random legal configuration; all disks to peg 2.
    State = tuple(peg of disk i), disk 0 smallest. h = disks not on peg 2.
    Most moves leave h unchanged -> a plateau-heavy game (added for the
    pre-registered prediction in plateau_test.py)."""
    N = 8

    def __init__(self, rng):
        while True:
            self.start = tuple(rng.randrange(3) for _ in range(self.N))
            if self.h(self.start) >= 4:
                break

    def h(self, s):
        return sum(1 for p in s if p != 2)

    def expand(self, s):
        top = {}
        for d in range(self.N - 1, -1, -1):
            top[s[d]] = d             # smallest disk on each peg ends up last
        out = []
        for src, d in top.items():
            for dst in range(3):
                if dst != src and (dst not in top or top[dst] > d):
                    c = s[:d] + (dst,) + s[d + 1:]
                    out.append((c, self.h(c)))
        return out


ALL["hanoi"] = Hanoi
