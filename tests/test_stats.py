import math
import sys
from pathlib import Path

from ctxblame.blame import Outcome, audit_p
from ctxblame.stats import binom_cdf, binom_sf, holm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "phase5"))


def test_binomial_tails():
    assert math.isclose(binom_cdf(0, 20, 0.45), 0.55 ** 20)
    assert math.isclose(binom_sf(20, 20, 0.45), 0.45 ** 20)
    assert math.isclose(binom_cdf(3, 10, 0.5) + binom_sf(4, 10, 0.5), 1.0)
    assert binom_cdf(0, 0, 0.5) == 1.0 and binom_sf(0, 5, 0.5) == 1.0  # no trials / trivial tail


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert holm([0.5]) == [0.5] and holm([]) == []


def test_audit_p_directions():
    flipped, kept = Outcome(0, 20, "flipped"), Outcome(19, 20, "kept")
    assert audit_p(flipped, "flip", 0.45, 0.5) < 1e-4 and audit_p(kept, "flip", 0.45, 0.5) > 0.99
    assert audit_p(kept, "restore", 0.45, 0.5) < 1e-4 and audit_p(flipped, "restore", 0.45, 0.5) == 1.0
    gone = Outcome(0, 0, "collapsed", k_given=0, n_total=20, given_verdict="collapsed")
    assert audit_p(gone, "collapse", 0.45, 0.5) < 1e-5 and audit_p(gone, "intact", 0.45, 0.5) == 1.0
    assert audit_p(Outcome(0, 0, "error"), "flip", 0.45, 0.5) == 1.0


def test_null_simulation_audit_controls_false_causes():
    from null_sim import simulate
    # v0.2 counts "not clearly flipped" as "keeping the member restores it", so a
    # member at the boundary passes; the audit tests restoration itself
    assert simulate("boundary_bundle", 40, 1, 0, 0.05)["fwer"] > 0.5
    assert simulate("boundary_bundle", 120, 1, 20, 0.05)["fwer"] <= 0.06
    assert simulate("power_bundle", 40, 1, 20, 0.05)["power"] >= 0.9


class _Auditor:
    """Deterministic audit: removing {"a"} (or more) flips; anything else keeps."""
    def __init__(self):
        self.calls = []

    async def audit(self, removed, n):
        self.calls.append(frozenset(removed))
        return Outcome(0, n, "flipped") if "a" in removed else Outcome(n, n, "kept")

    def p_value(self, o, kind):
        return audit_p(o, kind, 0.45, 0.5)


def test_audit_drops_a_hitchhiker_and_certifies_the_rest_on_new_replays():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # the search returned {a, b}; only a carries it, so keeping b alone cannot
    # restore the choice and the whole-bundle test (stage 1) fails
    f = Cause(["a", "b"])
    aud = _Auditor()
    asyncio.run(audit_findings([f], aud, 20, 0.05))
    assert f.members == ["a"] and f.certified is True
    assert "stage1:together" in f.audit and "stage1:b" in f.audit and "b" not in f.audit
    # stage 2 is new replays: the {a} removal is tested again after stage 1
    assert aud.calls == [frozenset("ab"), frozenset("b"), frozenset("a"), frozenset("a")]


def test_audit_keeps_rejecting_a_bundle_whose_removal_does_not_flip():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    f = Cause(["b", "c"])
    asyncio.run(audit_findings([f], _Auditor(), 20, 0.05))
    assert f.certified is False and not any(k.startswith("stage1:") for k in f.audit)
