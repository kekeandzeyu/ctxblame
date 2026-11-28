"""Phase 7.1: baseline reports from the raw replay data (offline, $0).

Reads ``<seed dir>/raw/*.json`` from ``baselines.py`` and writes
``<seed dir>/benchmark.json`` in the benchmark's row format (``case``, ``method``,
``report``), so ``score6.py`` / ``score7.py`` score the baselines exactly like
ctxblame. A budget M uses the first M rows of a design; the base rows (nothing removed) among them
set up A and E and are left out of the estimators.

Estimators on a binary design (removal indicators X, one replay per row):

  banzhaf  mean(bad | unit removed) - mean(bad | unit kept)  (maximum-sample-reuse
           Banzhaf: every row informs every unit)
  lasso    Lasso linear-probability model of bad ~ X (standardized), the unit's
           coefficient
  gt       noisy group-testing decoder for OR-of-AND causes: every set S of up to 3
           units among the top-K by Banzhaf, with
           mean(bad | S all removed) - mean(bad | otherwise); the minimal passing sets

"bad" is ``not A`` among the rows in E for the choice (carriers), and ``not E`` among
all rows for preconditions (unforced designs only). A unit is reported when its
statistic exceeds the 95th percentile of the largest statistic under permuted
outcomes (the max-statistic permutation null, family-wise alpha = 0.05), so every
estimator can answer "nothing". ``<est>:fq<q>+q<q>`` spends M/2 rows of the forced
design on the choice and M/2 of the unforced one on preconditions.

ContextCite (``cc``): Lasso on -log p(choice tokens | E prefix) for carriers and on
-log p(E prefix) for preconditions, same null. ``self_explain_full``: the model's own
lists.

    uv run python experiments/phase7/estimate.py experiments/phase7/results/<tag>/seed0
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path

import numpy as np

BUDGETS = (64, 128, 256, 512)
ESTIMATORS = ("banzhaf", "lasso", "gt")
ALPHA = 0.05
PERMS = 200
MIN_ROWS = 10  # fewer usable rows than this: report nothing


def design_matrix(rows: list, d: int) -> np.ndarray:
    X = np.zeros((len(rows), d))
    for t, r in enumerate(rows):
        X[t, r[0]] = 1.0
    return X


def permuted(y: np.ndarray, perms: int, rng: np.random.Generator) -> np.ndarray:
    """(n, perms + 1): the observed outcome in column 0, permutations after it."""
    return np.column_stack([y] + [rng.permutation(y) for _ in range(perms)])


def banzhaf_stats(X: np.ndarray, Y: np.ndarray, min_n: int = 2) -> np.ndarray:
    """(d, P): mean(Y | removed) - mean(Y | kept) per unit and column; 0 where either side has < min_n rows."""
    n = len(X)
    n1 = X.sum(0)
    s1 = X.T @ Y
    with np.errstate(divide="ignore", invalid="ignore"):
        eff = s1 / n1[:, None] - (Y.sum(0)[None, :] - s1) / (n - n1)[:, None]
    eff[(n1 < min_n) | (n - n1 < min_n)] = 0.0
    return np.nan_to_num(eff)


def lasso_stats(X: np.ndarray, Y: np.ndarray, alpha: float = 0.01, iters: int = 150) -> np.ndarray:
    """(d, P): Lasso coefficients on standardized X for every column of Y (FISTA, batched)."""
    sd = X.std(0)
    keep = sd > 0
    W = np.zeros((X.shape[1], Y.shape[1]))
    if not keep.any():
        return W
    Z = (X[:, keep] - X[:, keep].mean(0)) / sd[keep]
    Yc = Y - Y.mean(0)
    n = len(Z)
    step = n / max(np.linalg.norm(Z, 2) ** 2, 1e-12)
    w = v = np.zeros((Z.shape[1], Y.shape[1]))
    t = 1.0
    for _ in range(iters):
        g = Z.T @ (Z @ v - Yc) / n
        u = v - step * g
        w_new = np.sign(u) * np.maximum(np.abs(u) - step * alpha, 0.0)
        t_new = (1 + (1 + 4 * t * t) ** 0.5) / 2
        v = w_new + (t - 1) / t_new * (w_new - w)
        w, t = w_new, t_new
    W[keep] = w
    return W


def null_select(S: np.ndarray, alpha: float = ALPHA) -> list[int]:
    """Units whose observed statistic (column 0) beats the (1 - alpha) quantile of the
    per-permutation maximum (columns 1..)."""
    if S.shape[1] < 2:
        return []
    thr = np.quantile(S[:, 1:].max(0), 1 - alpha)
    return [int(i) for i in np.flatnonzero((S[:, 0] > thr) & (S[:, 0] > 0))]


def _set_stats(X: np.ndarray, y: np.ndarray, sets: list[tuple], min_n: int) -> np.ndarray:
    if not sets:
        return np.zeros(0)
    ind = np.stack([X[:, list(s)].prod(1) for s in sets], 1)
    n1 = ind.sum(0)
    n = len(X)
    s1 = ind.T @ y
    with np.errstate(divide="ignore", invalid="ignore"):
        st = s1 / n1 - (y.sum() - s1) / (n - n1)
    st[(n1 < min_n) | (n - n1 < min_n)] = -np.inf
    return np.nan_to_num(st, nan=-np.inf)


def gt_select(X: np.ndarray, Y: np.ndarray, k: int = 8, smax: int = 3, min_n: int = 3,
              alpha: float = ALPHA) -> list[int]:
    """Noisy group testing for OR-of-AND causes (see the module docstring)."""
    single = banzhaf_stats(X, Y)
    P = Y.shape[1]
    sizes = range(2, smax + 1)
    best = {s: np.full(P, -np.inf) for s in sizes}
    obs: dict[int, tuple[list[tuple], np.ndarray]] = {}
    for p in range(P):
        cand = [int(i) for i in np.argsort(-single[:, p])[:k]]
        for s in sizes:
            sets = list(combinations(sorted(cand), s))
            st = _set_stats(X, Y[:, p], sets, min_n)
            if len(st):
                best[s][p] = st.max()
            if p == 0:
                obs[s] = (sets, st)
    a = alpha / smax  # Bonferroni over set sizes; each size has its own max-null
    passing: list[frozenset] = []
    thr1 = np.quantile(single[:, 1:].max(0), 1 - a) if P > 1 else np.inf
    passing += [frozenset([int(i)]) for i in np.flatnonzero((single[:, 0] > thr1) & (single[:, 0] > 0))]
    for s in sizes:
        fin = best[s][1:][np.isfinite(best[s][1:])]
        thr = np.quantile(fin, 1 - a) if len(fin) else np.inf
        sets, st = obs[s]
        passing += [frozenset(x) for x, v in zip(sets, st) if np.isfinite(v) and v > thr and v > 0]
    minimal = [S for S in passing if not any(T < S for T in passing)]
    return sorted(set().union(*minimal)) if minimal else []


def select(est: str, X: np.ndarray, y: np.ndarray, rng: np.random.Generator, perms: int = PERMS) -> list[int]:
    """Units the estimator reports for outcome y ("bad" = 1)."""
    if len(y) < MIN_ROWS or y.min() == y.max():
        return []
    Y = permuted(y, perms, rng)
    if est == "banzhaf":
        return null_select(banzhaf_stats(X, Y))
    if est == "lasso":
        return null_select(lasso_stats(X, Y))
    if est == "gt":
        return gt_select(X, Y)
    raise ValueError(est)


def _members(raw: dict, idx: list[int]) -> list[dict]:
    return [{"id": raw["units"][i]} for i in idx]


def report(raw: dict, causes: list[int], pre: list[int], replays: int, extra: dict | None = None) -> dict:
    return {"result": "causes" if causes else "not_in_context",
            "causes": [{"relation": "baseline", "members": _members(raw, causes), "specific": True}] if causes else [],
            "preconditions": [{"members": _members(raw, pre), "specific": True}] if pre else [],
            "replays": replays, **(extra or {})}


def choice_rows(rows: list) -> tuple[list, np.ndarray]:
    r = [x for x in rows if x[1] and x[2]]
    return r, np.array([0.0 if x[3] else 1.0 for x in r])


def action_rows(rows: list) -> tuple[list, np.ndarray]:
    r = [x for x in rows if x[1]]
    return r, np.array([0.0 if x[2] else 1.0 for x in r])


def binary_report(raw: dict, est: str, choice: list, action: list | None, replays: int,
                  rng: np.random.Generator) -> dict:
    d = len(raw["units"])
    cr, cy = choice_rows(choice)
    causes = select(est, design_matrix(cr, d), cy, rng)
    pre: list[int] = []
    if action is not None:
        ar, ay = action_rows(action)
        pre = select(est, design_matrix(ar, d), ay, rng)
    return report(raw, causes, pre, replays, {"rows_in_e": len(cr)})


def case_reports(raw: dict, budgets=BUDGETS, estimators=ESTIMATORS, seed: int = 0) -> list[tuple[str, dict]]:
    rng = np.random.default_rng(seed)
    out: list[tuple[str, dict]] = []
    b = raw.get("base", 0)  # rows with nothing removed: they set up A and E, but are not i.i.d. design rows
    # (left in, they make every unit look harmful to remove, and a permutation null cannot see it)
    designs = {k: v for k, v in raw["designs"].items() if "rows" in v}
    combos = [("f" + k, k) for k, v in designs.items() if not v["forced"] and "f" + k in designs]
    for m in budgets:
        for est in estimators:
            for k, v in designs.items():
                rows = v["rows"][b:m]
                out.append((f"{est}:{k}:M{m}", binary_report(raw, est, rows, None if v["forced"] else rows, m, rng)))
            for f, u in combos:
                out.append((f"{est}:{f}+{u}:M{m}", binary_report(
                    raw, est, designs[f]["rows"][b:m // 2], designs[u]["rows"][b:m // 2], m, rng)))
        cc = raw.get("contextcite") or {}
        if cc.get("rows"):
            rows = cc["rows"][1:m]  # row 0 is the full context
            X = design_matrix(rows, len(raw["units"]))
            causes = select_cc(X, np.array([-r[2] for r in rows]), rng)
            pre = select_cc(X, np.array([-r[1] for r in rows]), rng)
            out.append((f"cc:M{m}", report(raw, causes, pre, m, {"prefills": len(rows) + 1})))
    se = raw.get("self_explain") or {}
    if "choice" in se:
        idx = {u: i for i, u in enumerate(raw["units"])}
        out.append(("self_explain_full", report(raw, [idx[u] for u in se["choice"]],
                                                [idx[u] for u in se["action"]], 1)))
    return out


def select_cc(X: np.ndarray, y: np.ndarray, rng: np.random.Generator, perms: int = PERMS) -> list[int]:
    if len(y) < MIN_ROWS or np.ptp(y) == 0:
        return []
    return null_select(lasso_stats(X, permuted(y, perms, rng)))


def _one(path: str) -> list[dict]:
    raw = json.loads(Path(path).read_text())
    return [{"case": raw["case"], "method": m, "report": r} for m, r in case_reports(raw, seed=zlib.crc32(raw["case"].encode()))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("seed_dirs", type=Path, nargs="+")
    ap.add_argument("--jobs", type=int, default=0, help="worker processes (default: all cores)")
    a = ap.parse_args(argv)
    for sd in a.seed_dirs:
        files = sorted(str(p) for p in (sd / "raw").glob("*.json"))
        if not files:
            print(f"no raw data in {sd}/raw", file=sys.stderr)
            return 1
        with ProcessPoolExecutor(a.jobs or None) as ex:
            rows = [r for rs in ex.map(_one, files, chunksize=4) for r in rs]
        (sd / "benchmark.json").write_text(json.dumps(rows))
        print(f"{sd}: {len(files)} cases, {len({r['method'] for r in rows})} methods -> {sd / 'benchmark.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
