"""Price table and a persistent spend ledger with a hard budget.

Prices are USD per 1M tokens, copied from the providers' pricing pages on
2026-11-13. Update them here when they change; unknown models are refused
rather than guessed, so the budget can always be enforced.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .formats import Usage


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float
    cache_write: float


def _claude(i: float, o: float) -> Price:
    return Price(i, o, i * 0.1, i * 1.25)


# DeepSeek: peak prices; off-peak is exactly half (see deepseek_multiplier).
DEEPSEEK = {
    "deepseek-flash": Price(0.30, 1.20, 0.006, 0.30),
    "deepseek-v4-pro": Price(1.32, 3.96, 0.044, 1.32),
}
CLAUDE = {
    "claude-fable-5-2": _claude(8, 40), "claude-opus-5-5": _claude(4, 20),
    "claude-opus-5": _claude(5, 25), "claude-sonnet-5-5": _claude(2, 10),
    "claude-sonnet-5": _claude(2, 10), "claude-haiku-5-5": _claude(0.10, 0.50),
    "claude-haiku-4-5": _claude(1, 5),
}


def deepseek_multiplier(when: datetime) -> float:
    """1.0 at peak (Mon-Fri 01-04 and 06-10 UTC), else 0.5. Chinese public
    holidays are also off-peak; we ignore them, which can only overestimate."""
    w = when.astimezone(timezone.utc)
    peak = w.weekday() < 5 and (1 <= w.hour < 4 or 6 <= w.hour < 10)
    return 1.0 if peak else 0.5


def resolve_model(model: str, upstream: str = "") -> str:
    """Map a model name to its price-table key. DeepSeek's Anthropic endpoint
    accepts claude-* names and serves its own models (opus -> v4-pro, others
    -> flash), so those are priced as DeepSeek."""
    if "deepseek" in upstream and model.startswith("claude"):
        return "deepseek-v4-pro" if model.startswith("claude-opus") else "deepseek-flash"
    if model in DEEPSEEK or model in CLAUDE:
        return model
    raise KeyError(f"no price for model {model!r}; add it to ctxblame/pricing.py")


def cost(model: str, usage: Usage, when: datetime | None = None, upstream: str = "",
         assume_peak: bool = False) -> float:
    key = resolve_model(model, upstream)
    p = DEEPSEEK.get(key) or CLAUDE[key]
    mult = 1.0
    if key in DEEPSEEK and not assume_peak:
        mult = deepseek_multiplier(when or datetime.now(timezone.utc))
    return mult * (usage.input_uncached * p.input + usage.input_cache_read * p.cache_read
                   + usage.input_cache_write * p.cache_write + usage.output * p.output) / 1e6


class BudgetExceeded(Exception):
    pass


class Ledger:
    """Append-only spend log (one JSON line per paid call)."""

    def __init__(self, path: Path, budget: float) -> None:
        self.path = path
        self.budget = budget
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.total = 0.0
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip():
                    self.total += json.loads(line)["cost"]

    def remaining(self) -> float:
        return self.budget - self.total

    def check(self, next_estimate: float) -> None:
        if self.total + next_estimate > self.budget:
            raise BudgetExceeded(f"spent ${self.total:.4f}; next call (~${next_estimate:.4f}) "
                                 f"would pass the ${self.budget:.2f} budget")

    def add(self, run_id: str, model: str, usage: Usage, c: float) -> None:
        self.total += c
        with self.path.open("a") as f:
            f.write(json.dumps({"ts": time.time(), "run": run_id, "model": model,
                                "usage": usage.__dict__, "cost": c}) + "\n")
