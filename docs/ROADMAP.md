# `ctxblame` Roadmap (`v0.2` → paper & `v0.3`)

This is the single canonical plan. Experiment phases continue the repository's
numbering (Phases 0–4 are done; see [WRITEUP.md](WRITEUP.md) and
[experiments/phase3/RESULTS.md](../experiments/phase3/RESULTS.md)), so new runs go
under `experiments/phase5/` … `experiments/phase8/`, and engine changes that
alter numbers are re-run under a fresh `results/<tag>/`, never over the `v0.2`
directories.

## 1. Where `v0.2.0` stands

- **Engine:** auth-stripping recording proxy; structure-preserving ablation
  (tool-call/result pairing, id rotation on reasoning removal); conditional blame
  $P(A \mid E)$ that keeps workflow preconditions apart from choice carriers;
  suffix-first delta debugging; leave-one-in pruning of OR bundles; random
  same-size controls.
- **Evidence (open models, vLLM, $0, 3 seeds):** F1 85–95% on generated cases,
  92% vs ≤60% on 13 real Qwen3-14B steps; preconditions separated in 76–100%
  (all baselines 0%); habit-only negatives 97–100% (ContextCite 0%). Suffix-first
  search: −23…27% replays, −34…38% uncached input on 14k–35k-char prompts, no
  saving on short ones.
- **Known weaknesses:** Llama-3.1-8B ties ContextCite (neutral lines join OR
  bundles and pass every vetting check); one real failure (`real/run4/step21`,
  diffuse precondition); real-trace evidence is one task, one convention, one
  model; the upgraded engine was never run on a paid API.

## 2. Audit: what must change before a paper

Verified against the code (line numbers as of `v0.2.0`):

| # | Problem | Where | Consequence |
|---|---|---|---|
| 1 | The "task" is the **last** user message with any text; a later `tool_result` turn carrying a `<system-reminder>` text block becomes the task, and the real prompt in `messages[0]` becomes removable. The task message is also exempt as a whole, hiding `CLAUDE.md` injected into it. | `blame.py:115-119`, `:185` | Wrong chunks on every Claude Code–style trace. |
| 2 | Precondition handling ends the whole search: at `max_preconditions` (`blame.py:873-874`) and on a diffuse precondition (`len(s) > max_members`, `:879-882`). *Corrected in Phase 5:* on `real/run4/step21` the stratified search stops at the **first** of these in all 3 seeds (three single read-output lines found, each revealing another); the diffuse `break` is what the flat search hits. | `blame.py:873-882` | `real/run4/step21`: preconditions reported, carriers never searched. |
| 3 | Confirmation reuses search samples (`old = self.samples[key]`), and each test peeks every batch of 5 at a fixed-n Wilson interval. | `blame.py:493`, `:499-541` | No valid error-rate statement for reported causes. |
| 4 | A rule that both triggers $E$ and picks $A$ (`e_coupled`, 0–15 oracle cases per model) collapses $P(E)$ when removed, so it is reported as a precondition only. | `blame.py:941-950`, `oracle.py:152` | Positivity violation: $P(A \mid E, do(\neg S))$ is undefined. |
| 5 | The oracle reuses ctxblame's own `resolve_given` and 0.5× thresholds and drops 30–41% of cases (incl. AND and E-coupled ones). | `oracle.py:94-152` | Ground truth shares the method's assumptions; selection bias. |
| 6 | Baselines are not steelmanned: ContextCite scores the whole tool-call JSON unconditionally and selects `w ≥ 0.25·max w` (it can almost never return "nothing"); self-explanation sees each chunk cut to 320 chars. | `contextcite.py:143`, `benchmark.py:259` | Part of the margin may be baseline handicap. |
| 7 | Anthropic `cache_control` breakpoints are not managed; tail removals can strip them. | `ablate.py`, `blame.py` | Cache economics unmeasured on the API that needs them most. |

### Correction to the earlier theory plan

The previous roadmap planned to prove that uniform-mask surrogates need
$\Omega(4^k \log d)$ queries versus $O(k \log d)$ for adaptive search under
$k$-way OR redundancy. **Drop that claim.** "The decision survives iff any
carrier is kept" is exactly *group testing* (a test is the kept set; it is
positive iff it contains a carrier). The $2^{-(k-1)}$ dilution is an artefact of
keep-probability $q = 1/2$: Bernoulli($q \approx 1/k$) non-adaptive designs
recover $k$ carriers among $d$ chunks with $O(k \log d)$ tests, and
$\Omega(k \log(d/k))$ is a lower bound for *every* method, adaptive or not
(Aldridge, Johnson & Scarlett, *Group Testing: An Information-Theoretic
Perspective*, 2019). An informed reviewer would reject the separation as stated.

What remains defensible and is ctxblame's actual structure:

- **The precondition gate.** With $m$ precondition chunks that must stay for
  $E$ to happen at all, a Bernoulli($q$) design keeps all of them with
  probability $q^m$; every other test is uninformative about $P(A \mid E)$. Small
  $q$ (good for OR recovery) and large $q$ (good for keeping the gate open)
  conflict; an adaptive search that finds and protects the gate first does not
  pay this. This is the separation to prove and to measure (Phase 7).
- **Calibrated "nothing in the context"** and a post-selection error guarantee
  (Phase 5), which surrogate methods do not provide.
- **Cache-aware test ordering** as an engineering result (measured ~1.5×, not
  a headline).

### Scope guardrails

- Benchmarks use **wire-exact proxy recordings only**; `ctxblame import` stays a
  CLI convenience marked `reconstructed (not wire-verified)`.
- No automated prompt repair (`ctxblame patch`) as a contribution; use a
  deterministic single-shot fix-verification study instead.
- No individual-level PNS claims; report interventional bundle necessity and
  leave-one-in sufficiency, which are point-identified from replays.
- `--chain` (backward traversal over attributed earlier calls) stays a short
  formulation plus 2–3 case studies.
- Report the sampling settings with every number: attributions are properties
  of $P(\cdot)$ at a given temperature (the `v0.2` runs used 0.7 for Qwen with
  thinking off, 0.6 for Qwen thinking and Llama; exact `extra_body` is in each
  `results/<tag>/oracle_all.json`).

## 3. Plan

Each phase has an exit gate; the next one starts only when it is met.

### Phase 5 — Engine correctness and valid statistics ($0, offline + one re-run)

Details and results: [experiments/phase5/README.md](../experiments/phase5/README.md).

- [x] **5.1 Block-level user-turn chunking** (audit #1). The task is the latest
  user turn with text the user wrote; `<system-reminder>`, `<environment_details>`
  and `<context>` blocks in any user turn (string or block content, both wire
  formats) are removable `injected` chunks with line children. Chunking of every
  existing benchmark case is byte-identical to `v0.2` (5,090 chunks), so the
  `v0.2` numbers are unaffected.
- [x] **5.2 Stabilizer instead of stopping** (audit #2). When preconditions run
  out (`max_preconditions`) or one is diffuse, a minimal stabilizer $K$ of $E$
  (removing everything else keeps $E$; prefix kept first, so its probes stay
  cache-friendly) is protected once, reported as `diffuse_preconditions`, and the
  choice search continues. `--no-stabilize` restores `v0.2`. Mock-model tests
  reproduce the `run4/step21` shape. *Acceptance on the real case: 5.5.*
- [x] **5.3 Search / audit split** (audit #3). After the search, every finding
  is audited on `--audit-n` (default 20) fresh replays per test that the search
  never sees: bundle flip + each leave-one-in restore (exact one-sided binomial
  tests at the search's thresholds), intersection–union within a bundle, Holm
  across findings at `--alpha` (0.05); uncertified findings move to
  `uncertified`. **Result (null simulation, real `Tester` + simulated model, 500
  runs):** with a bundle member at the boundary, `v0.2` reports a false bundle
  in 93% of runs (its leave-one-in check counts "not clearly flipped" as
  "restores"); with the audit 1.6% [0.8, 3.1] ≤ α, at 99% power on a true
  bundle and +60–75 replays per run. *Two-stage audit* (found by `p5-gen`):
  members that do not restore are dropped and the smaller bundle is re-audited
  on new replays (sample splitting), 3.0% [1.8, 4.9] ≤ α.
- [x] **5.4 `cache_control` pinning** (audit #7): on Anthropic requests recorded
  with prompt caching, stale breakpoints after the first changed block are
  removed and one is pinned on the last unchanged block (recorded style kept,
  never on reasoning, ≤ 4). Requests recorded without caching are replayed as
  recorded.
- [x] **5.5 Re-run on GPU** (`experiments/phase5/run_p5.sh`), same oracle-valid
  cases as `v0.2`:
  1. `p5-repro-real`: `--audit-n 0 --no-stabilize` on `real` reproduces `v0.2`
     exactly (92% F1 [77, 100], every seed).
  2. `p5-real` and `p5-gen`: the Phase 5 engine (defaults), 3 seeds. They found
     5.2b (after a stabilizer the suffix probe stopped on an E collapse; fixed by
     probing for the first flip over the same tiers) and the hitchhiker bundles
     that led to the two-stage audit.
  3. `p5c-real` / `p5c-gen`, the final engine: **92% [77, 100]** and
     **93% [84, 100]** (`v0.2`: 92% / 95% [87, 99]), all findings audited.
     `run4/step21` continues past the stabilizer but stays unsolved
     (`triggers_and_steers`: the `bash` description is both precondition and
     carrier). The gen misses are E-coupled bundles where stage 1 drops a
     member on an E-collapsed restore test (→ 6.4).

- [x] **5.6 Audit for coupled bundles** (from `p5c-gen`), offline:
  - Stage 1 drops a bundle member only when E stays intact and the choice is not
    restored.
  - A member whose leave-one-in test stops E is kept as `coupled`, and stage 2
    tests that collapse.
  - Every bundle is re-audited on new replays, so stage 1 is never evidence: the
    v2 design allowed about 2α.
  - Null simulation v3: boundary false-cause rates 1.4% and 3.8% ≤ α; power on
    the `p0` coupled shape 0% → 97%.
  - `triggers_and_steers suspected` is reported when the stabilizer keeps the
    choice.
  - GPU confirmation, done (`p5d-*`):
    - real: 92% [77, 100], unchanged.
    - gen: **97% [92, 100]** (`p5c` 93%, `v0.2` 95%). `p0` and `gen/0-013` are recovered in every seed.
    - The remaining gen miss, `p3/precond_2or_pnpm`, is a design label: its "precondition"
      `edit_pkg` is `triggers_and_steers`, measured by direct replays (→ 6.4).

**Gate:** offline suite green; type-I simulation within α; re-run F1 within
the `v0.2` CI (or a documented reason why not); `run4/step21` finds a carrier or
reports `diffuse_precondition` with the search continuing.

### Phase 6 — Ground truth independent of the method (Tier 1, $0)

- [x] **6.1 Exhaustive coalition tables.** For each case, enumerate all $2^m$
  removals of its planted elements ($m \le 5$: carriers, precondition, plus 1–2
  *neutral probe lines*), fixed $N = 50$ replays each. Truth = the estimated
  Boolean function of $(P(E), P(A \mid E))$; nothing is dropped, cases are
  labelled by regime: single, OR, AND, precondition-gated, E-coupled,
  conflict/override, habit-negative, and *non-monotone / interaction*.
- [x] **6.2 Pilot first.** 10 cases on Qwen3-14B to measure throughput, then
  size the suite (target 200–300 cases; ~1,600 replays per case at $m = 5$).
  *Done (Qwen3-14B and Llama-3.1-8B):* 1,080 replays/case, 76–94 replays/s on one
  RTX 5090, so the tables for 250 cases take about 1 h per model. The suite stays at 250.
  [experiments/phase6/README.md](../experiments/phase6/README.md#62-pilot-2026-11-28).
- [x] **6.3 Settle the Llama question.** The neutral probes say directly whether
  Llama's neutral lines are real interactions (they appear in the table) or
  ctxblame false positives (they do not).
- [ ] **6.4 E-coupled cases** (audit #4). Estimate the coupled effect with a
  matched intervention: compare $P(A \mid do(E), do(\neg S))$ against the
  equally forced baseline $P(A \mid do(E))$ — never against unforced
  $P(A \mid E)$. `tool_choice` forces a tool name only, so this applies where
  $E$ is a tool; intent-level $E$ (a Bash command family) is reported as not
  identifiable rather than forced. Then classify `precondition` vs
  `triggers_and_steers` in the engine. The audit's `coupled` members (5.6) and
  `triggers_and_steers suspected` notes are the engine's first, conservative
  version: check them against the 6.1 tables, and add line-level stabilizing for
  the `run4/step21` tool description.

**Gate:** ≥ 200 labelled cases on ≥ 2 models; ctxblame scored on all of them
(per regime), with the oracle-dropped subset reported separately for comparison
with `v0.2`.

*Gate met (2026-11-28).* 250 cases each on Qwen3-14B and Llama-3.1-8B
([experiments/phase6/README.md](../experiments/phase6/README.md#61--63-the-full-suite-2026-11-28)):
- Oracle-valid F1 is 95% / 85%, as in `v0.2`.
- Oracle-dropped F1 is 71% / 44%.
- 6.3: Llama's neutral lines are real interactions. A probe is a carrier in 14%
  of cases, and ctxblame blames table-neutral probes in 1% of rows.
- 6.4's engine side stays open. Qwen has 50 `e_coupled` cases, and F1 there is 46%.

### Phase 7 — Steelmanned baselines and theory ($0)

- [ ] **7.1 Baselines at matched replay budgets** ($M \in \{64, 128, 256\}$):
  - *ContextCite-contrastive*: target-span log-likelihood given the tool-call
    prefix (conditional on $E$), with a permutation-null threshold so it can
    answer "nothing".
  - *Black-box group testing / Lasso / Banzhaf* on binary $\mathbb{I}[A]$ given
    $E$, **sweeping the keep-probability** $q \in \{1/2, 1/4, 1/k\}$. This is the
    decisive comparison: if a tuned non-adaptive design matches ctxblame on
    choice carriers, the contribution is the gate handling, not the search.
  - *Self-explain-full*: no 320-char truncation, $(A, E)$ stated in the prompt.
- [ ] **7.2 Theory section:**
  1. Noisy group-testing formulation and the $\Omega(k \log(d/k))$ lower bound;
     delta debugging / binary splitting meets it adaptively.
  2. Gate proposition: non-adaptive Bernoulli($q$) designs waste a $1 - q^m$
     fraction of tests under $m$ preconditions; adaptive protection removes the
     $q^{-m}$ factor. Verified empirically on Phase 6 cases by varying $m$.
  3. Audit theorem for Phase 5.3 (IUT + Holm, fresh draws).
  4. Diagnostic: total influence of the estimated Boolean function per model
     (from Phase 6 tables) as a measurable "noisy model" property that predicts
     when monotone search assumptions break.

**Gate:** baseline table on Phase 6 suite; propositions written with proofs and
matched by the measured curves. **Venue decision here:** if the gate separation
holds against tuned group testing → main track (method + theory); otherwise →
NeurIPS Datasets & Benchmarks with `AgentBlame-Bench` as the contribution.

### Phase 8 — External validity: wild traces and one closed API

- [ ] **8.1 `ctxblame wrap -- <cmd>`** (prerequisite): ephemeral proxy port and
  `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` injection.
- [ ] **8.2 Tier 2 wild steps.** 50–100 wire-captured steps from 2 harnesses
  (start with one open-model harness, e.g. OpenHands, then Claude Code) on a
  SWE-bench Verified subset, with **decision types beyond the test command**:
  which file to edit, whether to run a check before a risky command, which tool
  to use.
- [ ] **8.3 Ground-truth-free metrics** on held-out fresh replays: conditional
  flip rate of the blamed set (↑), precondition collateral damage (↓),
  leave-one-in member sufficiency (↑), flips vs. replays/tokens.
- [ ] **8.4 `ctxblame verify --replace-text`** and the single-shot fix study:
  editing the full minimal OR bundle vs. the top-1 LOO / surrogate chunk.
- [ ] **8.5 Closed API (needs explicit approval, est. $25–40 under `--budget`):**
  30 stratified steps on one Claude model with `cache_control` pinning and one
  OpenAI/DeepSeek model; real billed cost and cache-read share.

**Gate:** wild results reported with CIs; paid spend logged in the ledger.

### After the paper — `v0.3` adoption

`ctxblame import` for Claude Code / OpenCode transcripts (best effort, marked
reconstructed), `--chain` case studies, and release notes.

## 4. Order of work

Phase 5 first: 5.1 corrupts every Claude Code trace, and 5.3 is required
before any accuracy number can carry an error guarantee. Phases 6 and 7 can
overlap once the Phase 6 pilot fixes the case format. Phase 8 waits for the
Phase 7 venue decision, because it is the most expensive and its framing
depends on it.
