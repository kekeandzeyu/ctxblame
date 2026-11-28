"""Ground truth from an exhaustive coalition table (Phase 6.1, $0, offline).

A case plants m <= 5 elements (choice carriers, a workflow precondition, and 1-2
neutral probe lines). ``tables.py`` replays every one of the 2^m removals a fixed
N times, with no adaptive stopping, and records per removal S:

    n        replays that returned        k_given  of them in the action family E
    k        of those, the recorded choice A

Truth is the estimated Boolean function of (P(E | do(-S)), P(A | E, do(-S))), read
at the same thresholds the engine uses (half the base rates). It never depends on
what ctxblame reports, and nothing is dropped. Each cell is labelled with a 95%
Wilson interval: ``intact`` / ``collapsed`` for E, ``kept`` / ``flipped`` for A
given E, and ``ambiguous`` when the interval straddles the threshold.

From the cells:

  carrier sets      minimal S (by inclusion) whose removal keeps E and flips A
  precondition sets minimal S whose removal collapses E
  roles             carrier / precondition / triggers_and_steers (both) / neutral
  regimes           negative, single, or, and (several disjoint carrier sets),
                    precondition_gated, e_coupled, non_monotone, probe_interaction

``non_monotone``: removing more restores what removing less broke (a flip or a
collapse at S that disappears at some T > S, both cells decided). These are the
cases a search that assumes monotonicity can get wrong, and they are labelled,
not dropped.

Forced cells (6.4, optional): the same removals replayed with E forced by
``tool_choice``, recording A among the replies in E. Where removing S collapses E,
the unforced cell cannot say whether S also steers the choice (positivity); the
forced cell compares P(A | do(E), do(-S)) with half the equally forced baseline
P(A | do(E)), never with the unforced P(A | E). A precondition element is then
``triggers_and_steers`` if it is in a minimal *steer set* (minimal S whose forced
cell flips). Forcing only decides that question: carriers outside every
precondition set keep their unforced definition. If forcing E changes the choice
even with the whole context (forced base below 0.5), the forced cells are not used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import math


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


@dataclass(frozen=True)
class Cell:
    removed: frozenset[str]
    n: int
    k_given: int
    k: int

    @property
    def p_given(self) -> float | None:
        return self.k_given / self.n if self.n else None

    @property
    def p_cond(self) -> float | None:
        return self.k / self.k_given if self.k_given else None


def _side(k: int, n: int, threshold: float, above: str, below: str) -> str:
    lo, hi = wilson(k, n)
    return above if lo > threshold else below if hi < threshold else "ambiguous"


@dataclass
class Truth:
    elements: list[str]
    kinds: dict[str, str]  # element -> carrier | precondition | probe (what was planted)
    e_state: dict[frozenset, str] = field(default_factory=dict)  # intact | collapsed | ambiguous
    a_state: dict[frozenset, str] = field(default_factory=dict)  # kept | flipped | ambiguous | none
    carrier_sets: list[frozenset] = field(default_factory=list)
    precondition_sets: list[frozenset] = field(default_factory=list)
    roles: dict[str, str] = field(default_factory=dict)
    regimes: list[str] = field(default_factory=list)
    non_monotone: list[tuple[list[str], list[str], str]] = field(default_factory=list)
    ambiguous: int = 0  # cells with an undecided E or (E intact) A
    base: dict = field(default_factory=dict)
    f_state: dict[frozenset, str] = field(default_factory=dict)  # E forced: kept | flipped | ambiguous | none
    steer_sets: list[frozenset] = field(default_factory=list)
    forced: dict | None = None  # forced base and whether the forced cells were used

    def to_json(self) -> dict:
        key = lambda s: "+".join(sorted(s)) or "-"  # noqa: E731
        return {"elements": self.elements, "kinds": self.kinds,
                "e_state": {key(s): v for s, v in self.e_state.items()},
                "a_state": {key(s): v for s, v in self.a_state.items()},
                "carrier_sets": [sorted(s) for s in self.carrier_sets],
                "precondition_sets": [sorted(s) for s in self.precondition_sets],
                "roles": self.roles, "regimes": self.regimes, "non_monotone": self.non_monotone,
                "ambiguous": self.ambiguous, "base": self.base,
                **({"f_state": {key(s): v for s, v in self.f_state.items()},
                    "steer_sets": [sorted(s) for s in self.steer_sets], "forced": self.forced}
                   if self.forced is not None else {})}


def _minimal(sets: list[frozenset]) -> list[frozenset]:
    return sorted((s for s in sets if not any(t < s for t in sets)), key=lambda s: (len(s), sorted(s)))


def label(elements: list[str], kinds: dict[str, str], cells: dict[frozenset, Cell],
          min_given: int = 10, forced: dict[frozenset, Cell] | None = None) -> Truth:
    """Label one case from its full table (every subset of ``elements`` must be present).
    ``forced``: the forced cells (``k_given`` = replies in E, ``k`` = A among them)."""
    subsets = [frozenset(c) for r in range(len(elements) + 1) for c in combinations(elements, r)]
    missing = [s for s in subsets if s not in cells]
    if missing:
        raise ValueError(f"table incomplete: {len(missing)} of {len(subsets)} removals missing")
    b = cells[frozenset()]
    tau_e = (b.p_given or 0) / 2
    tau_a = (b.p_cond or 0) / 2
    t = Truth(list(elements), dict(kinds), base={"p_given": b.p_given, "p_cond": b.p_cond, "n": b.n,
                                                 "tau_e": tau_e, "tau_a": tau_a})
    for s in subsets:
        c = cells[s]
        e = _side(c.k_given, c.n, tau_e, "intact", "collapsed")
        t.e_state[s] = e
        if e == "collapsed" or c.k_given < min_given:
            t.a_state[s] = "none"  # the choice is undefined (or unmeasurable) without the action
        else:
            t.a_state[s] = _side(c.k, c.k_given, tau_a, "kept", "flipped")
        t.ambiguous += e == "ambiguous" or t.a_state[s] == "ambiguous"

    flips = [s for s in subsets if t.e_state[s] == "intact" and t.a_state[s] == "flipped"]
    collapses = [s for s in subsets if t.e_state[s] == "collapsed"]
    t.carrier_sets = _minimal(flips)
    t.precondition_sets = _minimal(collapses)
    in_c = set().union(*t.carrier_sets) if t.carrier_sets else set()
    in_p = set().union(*t.precondition_sets) if t.precondition_sets else set()
    in_s: set[str] = set()
    if forced is not None:
        missing = [s for s in subsets if s not in forced]
        if missing:
            raise ValueError(f"forced table incomplete: {len(missing)} of {len(subsets)} removals missing")
        fb = forced[frozenset()]
        f_rate = fb.k / fb.k_given if fb.k_given else 0.0
        used = fb.k_given >= min_given and f_rate >= 0.5
        t.forced = {"p_cond": f_rate if fb.k_given else None, "n_given": fb.k_given, "n": fb.n,
                    "tau": f_rate / 2, "used": used}
        for s in subsets:
            c = forced[s]
            t.f_state[s] = ("none" if c.k_given < min_given else
                            _side(c.k, c.k_given, f_rate / 2, "kept", "flipped"))
        if used:
            t.steer_sets = _minimal([s for s in subsets if t.f_state[s] == "flipped"])
            in_s = set().union(*t.steer_sets) if t.steer_sets else set()
    for x in elements:
        t.roles[x] = ("triggers_and_steers" if x in in_p and (x in in_c or x in in_s) else "carrier" if x in in_c
                      else "precondition" if x in in_p else "neutral")
    in_c = in_c | (in_s & in_p)  # a steering precondition carries the choice too (regimes below)

    for s in subsets:
        for x in elements:
            if x in s:
                continue
            u = s | {x}
            if t.e_state[s] == "collapsed" and t.e_state[u] == "intact":
                t.non_monotone.append((sorted(s), sorted(u), "collapse undone"))
            if (t.e_state[s] == "intact" == t.e_state[u] and t.a_state[s] == "flipped"
                    and t.a_state[u] == "kept"):
                t.non_monotone.append((sorted(s), sorted(u), "flip undone"))

    r: list[str] = []
    if not t.carrier_sets and not t.precondition_sets:
        r.append("negative")
    elif len(t.carrier_sets) == 1:
        r.append("single" if len(t.carrier_sets[0]) == 1 else "or")
    elif len(t.carrier_sets) > 1:  # A = c1 AND c2: removing either alone flips
        r.append("and" if all(len(s) == 1 for s in t.carrier_sets) else "mixed")
    if t.precondition_sets:
        r.append("e_coupled" if in_c & in_p or any(kinds.get(x) == "carrier" for x in in_p)
                 else "precondition_gated")
    if t.non_monotone:
        r.append("non_monotone")
    if any(kinds.get(x) == "probe" and t.roles[x] != "neutral" for x in elements):
        r.append("probe_interaction")
    t.regimes = r
    return t
