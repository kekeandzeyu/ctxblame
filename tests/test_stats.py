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


class _CondAuditor:
    """Conditional audit on 20 replays. ``table`` maps a removal to (E count, A-given-E count)."""
    def __init__(self, table):
        self.table, self.calls = table, []

    async def audit(self, removed, n):
        self.calls.append(frozenset(removed))
        e, a = self.table[frozenset(removed)]
        gv = "intact" if e > 14 else "collapsed" if e < 5 else "unclear"
        v = "collapsed" if gv == "collapsed" else "flipped" if a < e * 0.2 else "kept" if a > e * 0.7 else "unclear"
        return Outcome(a, e, v, k_given=e, n_total=n, given_verdict=gv)

    def p_value(self, o, kind):
        return audit_p(o, kind, 0.45, 0.475)


def test_audit_keeps_a_member_coupled_with_the_action_family():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # p0/tool_result_sentence_config shape: removing both flips with E intact;
    # removing only b while keeping the carrier a stops E, so a's restoration is
    # untestable. a must not be dropped as a hitchhiker; it is certified as coupled.
    t = {frozenset("ab"): (20, 0), frozenset("b"): (0, 0), frozenset("a"): (20, 20)}
    f = Cause(["a", "b"])
    aud = _CondAuditor(t)
    asyncio.run(audit_findings([f], aud, 20, 0.05))
    assert f.members == ["a", "b"] and f.coupled == ["a"] and f.certified is True
    assert "stage1:a" in f.audit and "a" in f.audit  # stage 2 tested the collapse on new replays
    assert aud.calls == [frozenset("ab"), frozenset("b"), frozenset("a")] * 2


def test_audit_never_drops_a_member_on_an_uninformative_test():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # keeping b alone leaves E at 10/20: neither intact nor clearly stopped
    t = {frozenset("ab"): (20, 0), frozenset("a"): (10, 2), frozenset("b"): (20, 20)}
    f = Cause(["a", "b"])
    asyncio.run(audit_findings([f], _CondAuditor(t), 20, 0.05))
    assert f.members == ["a", "b"] and f.coupled == [] and f.certified is False
    assert "stage1:b" in f.audit and f.audit["b"].given_verdict == "unclear"  # tested again, still unclear


def test_audit_drops_a_conditional_hitchhiker_only_when_e_stays_intact():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    t = {frozenset("ab"): (20, 0), frozenset("a"): (20, 0), frozenset("b"): (20, 20)}
    f = Cause(["a", "b"])
    asyncio.run(audit_findings([f], _CondAuditor(t), 20, 0.05))
    assert f.members == ["a"] and f.coupled == [] and f.certified is True


def test_audit_reaudits_every_bundle_on_new_replays_even_when_nothing_is_dropped():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # a true OR bundle: stage 1 changes nothing, but must not be the evidence
    t = {frozenset("ab"): (20, 0), frozenset("a"): (20, 20), frozenset("b"): (20, 20), frozenset("c"): (20, 0)}
    f, single = Cause(["a", "b"]), Cause(["c"])
    aud = _CondAuditor(t)
    asyncio.run(audit_findings([f, single], aud, 20, 0.05))
    assert f.certified and single.certified and f.members == ["a", "b"]
    assert aud.calls == [frozenset("ab"), frozenset("b"), frozenset("a")] * 2 + [frozenset("c")]


class _ForcedCondAuditor(_CondAuditor):
    """_CondAuditor plus E forced: ``forced`` maps a removal to A-count of 20 under do(E)."""
    force_tool = "bash"

    def __init__(self, table, forced):
        super().__init__(table)
        self.forced = forced

    async def can_force(self):
        return True

    async def audit(self, removed, n, forced=False):
        if not forced:
            return await super().audit(removed, n)
        self.calls.append(("forced", frozenset(removed)))
        a = self.forced[frozenset(removed)]
        return Outcome(a, n, "flipped" if a < 5 else "kept" if a > 14 else "unclear", k_given=n, n_total=n)

    def p_value(self, o, kind):
        return audit_p(o, kind, 0.45, 0.475, 0.45)


def test_audit_tests_a_coupled_member_with_E_forced():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # the p0 shape again: keeping a while removing b stops E, so unforced a's role is
    # untestable; with E forced, keeping a restores the choice -> certified as restoring
    t = {frozenset("ab"): (20, 0), frozenset("b"): (0, 0), frozenset("a"): (20, 20)}
    f = Cause(["a", "b"])
    aud = _ForcedCondAuditor(t, {frozenset("b"): 20})
    asyncio.run(audit_findings([f], aud, 20, 0.05))
    assert f.members == ["a", "b"] and f.coupled == ["a"] and f.certified is True
    assert "forced:a" in f.audit and "a" not in f.audit  # stage 2 tested a's restoration under do(E)
    assert aud.calls.count(("forced", frozenset("b"))) == 2  # stage 1 picks, stage 2 decides


def test_audit_drops_a_coupled_member_that_does_not_restore_with_E_forced():
    import asyncio

    from ctxblame.blame import Cause, audit_findings
    # same, but with E forced keeping a does not bring the choice back: a only looked
    # coupled (like the 9 table-neutral "coupled" members of Phase 6) and is dropped.
    # What is left, {b}, is removed by exactly a's leave-one-in test: unforced it stops
    # E, forced it flips A. So b triggers and steers (p6/0-1187: the pnpm rule), and
    # stage 2 certifies "with E forced, removing b flips the choice" on new replays.
    t = {frozenset("ab"): (20, 0), frozenset("b"): (0, 0), frozenset("a"): (20, 20)}
    f = Cause(["a", "b"])
    aud = _ForcedCondAuditor(t, {frozenset("b"): 0})
    asyncio.run(audit_findings([f], aud, 20, 0.05))
    assert f.members == ["b"] and f.coupled == [] and f.forced is True and f.certified is True
    assert "stage1:forced:a" in f.audit and f.audit["together"].k == 0 and not f.audit["together"].collapsed
    assert aud.calls[-1] == ("forced", frozenset("b"))  # stage 2: the forced claim, on new replays


def test_null_simulation_steering_claims_under_forced_E():
    from null_sim import simulate
    assert simulate("tas_power", 30, 1, 20, 0.05)["power"] >= 0.9
    assert simulate("pure_precondition", 30, 1, 20, 0.05)["fwer"] == 0
    assert simulate("boundary_tas", 120, 1, 20, 0.05)["fwer"] <= 0.06
