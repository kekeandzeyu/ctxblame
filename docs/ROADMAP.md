# ctxblame — Technical Audit, Bug Diagnosis & Algorithmic Roadmap

## 1. Technical Audit: Idea Novelty vs. Algorithmic Novelty

### What Already Works Well
* **Idea & Positioning:** Model-agnostic `"git blame"` for black-box multi-turn agent tool calls over both Anthropic Messages (`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`), requiring no token logprobs or white-box weights.
* **Solid Systems Pieces:**
  * Streaming/non-streaming recording proxy (`src/ctxblame/proxy.py`, `sse.py`) that strips auth headers on disk.
  * Sequential replay tester with Wilson confidence intervals (`decide()` in `src/ctxblame/blame.py#L322-L332`) and a hard USD spend ledger (`src/ctxblame/pricing.py`).
  * Structure-preserving JSON ablation (`apply_chunks` in `src/ctxblame/blame.py#L236-L288`, `ablate.py`) that pairs `tool_use` + `tool_result` removals and rotates `tool_use` IDs when stripping `thinking` blocks.
* **Three Empirical Findings Already Demonstrated (`experiments/phase1/README.md`):**
  1. **Undocumented server-side reasoning cache:** On DeepSeek's Anthropic endpoint in thinking mode, removing both an `AGENTS.md` rule and earlier `thinking` text still produced the rule-driven call `17/20` times—until `tool_use` IDs were rotated, proving the server cached and restored reasoning keyed by call ID.
  2. **Redundant multi-carrier backup is the norm:** Rules in `AGENTS.md`, examples in tool parameter schemas, and the agent's own earlier tool calls act as OR-backups. Single-chunk leave-one-out methods (e.g. linear logprob surrogates like `ContextCite`) assign near-zero weight to each carrier because the remaining backups hold the decision at `~100%`.
  3. **Self-reinforcing history:** By step 5–7 of a run, deleting a rule from `AGENTS.md` has zero effect (`20/20`) because the agent copies its own step-1 tool invocation.

### Where Current Technical Novelty Stops (and Breaks)
Under the hood, `src/ctxblame/blame.py#L405-L429` currently runs **Zeller's classical 1999 `ddmin` algorithm** against an unconditional target rate `P(target)`. Phase 2 validation (`experiments/phase2/results/results.md`) exposed two concrete algorithmic failures of unconditional `ddmin` on multi-turn agent traces:

1. **Bug 1 — Workflow Precondition vs. Choice Confounding (`0%` precision on `step7`, `60%` on `step5`):**
   * In `p1/pytest/anthropic/step7`, `ctxblame` found **`0/3` planted carriers (`0%` precision)** and blamed `turn 6 edit_file({"path": "src/ctxblame/formats.py", ...})` (`0/20`).
   * In `p1/pytest/openai/step5`, precision dropped to **`60%`**, lumping `turn 4 edit_file(...)` together with the actual `pytest` style carriers.
   * **Root cause:** Removing `edit_file` makes the agent *go back and edit the file* instead of running tests at all. Because `Tester` scores unconditional `P(bash command matches python -m pytest -q)`, *not running tests* looks identical to *switching test runners* (`0/20` matches). `ddmin` immediately locks onto `edit_file` (a single-chunk flip!) and stops, completely missing the 3 redundant carriers that actually controlled `python -m pytest -q` vs. `uv run pytest`.
2. **Bug 2 — Immediate Byte-0 Prefix-Cache Invalidation (`$2.42` on one step):**
   * `everything = await test(frozenset(remaining))` (`src/ctxblame/blame.py#L460`) and complement slices (`comp`, `src/ctxblame/blame.py#L421`) strip `tools` and `system` at offset `0` right at the start of search.
   * Mutating byte `0` invalidates the provider's KV prefix cache across the entire 20k+ token request (`$1.32/M` uncached vs. `$0.044/M` cached on `deepseek-v4-pro`; `$0.30/M` vs. `$0.006/M` on `deepseek-flash`), costing `$2.417` on `p1/pytest/openai/step5` alone.

---

## 2. Algorithmic Upgrade Plan (Making `ctxblame` Technically Novel)

### Milestone 1: Conditional / Contrastive Blame (`P(A | E)` via `--given`) — Implemented (`65d1387`)
Separate **Stage Preconditions** (*why take action family `E` now?*) from **Choice Carriers** (*given `E`, why choose variant `A` over alternatives?*):
* Introduce conditioning matcher `E` (`--given <spec>`, defaulting when `--key-arg` is used to *"calls the same tool / intent category"*, e.g. *"runs any `pytest` command"* while target `A` is *"uses `python -m pytest -q`"*).
* Track `(k_target, k_given, n_ok)` in `Outcome`:
  * **Precondition collapse:** If removing subset `S` drops `k_given / n_ok` significantly below baseline `P(E)`, `S` contains a **workflow precondition** (such as `turn 6 edit_file`). Isolate and auto-protect that precondition (reporting it separately under `Preconditions`), rather than reporting it as a cause of `A`.
  * **Choice flip:** Score `ddmin` flips on the conditional Wilson interval of `k_target / k_given` while `P(E)` remains intact.
* **Acceptance test:** Verified locally via end-to-end HTTP simulation (`tests/test_blame_cli.py`); pending live re-run on `p1/pytest/openai/step5` and `p1/pytest/anthropic/step7` to confirm `3/3` planted carriers with `100%` precision.

### Milestone 2: Explicit AND-Preconditions vs. OR-Carriers (Minimal Hitting-Set Duality) — Implemented (`ba1b402`)
Formalize multi-carrier attribution beyond single-subset `ddmin`:
* **AND-context (necessary chunks):** Chunks whose individual removal collapses `P(E)` or `P(A | E)`.
* **OR-carrier bundles (minimal hitting sets):** Minimal sets $C = \{c_1, \dots, c_m\}$ where removing *all* $c \in C$ flips $P(A \mid E)$ below threshold, **and** holding $C \setminus \{c_i\}$ removed proves each $c_i$ alone restores $P(A \mid E)$ (filtering out hitchhiking non-carriers that `ddmin` kept by chance).

### Milestone 3: KV-Cache-Stratified Suffix-First Search (5–10× Cost Reduction) — Implemented (`ba1b402`)
Make prefix-cache economics a first-class primitive in search ordering:
1. Partition chunks by byte offset into tiers: `Tier 3: Tail History` → `Tier 2: Early History` → `Tier 1: System Prompt` → `Tier 0: Tool Schemas`.
2. Probe suffix tiers first while keeping bytes `0 .. tier_start` **byte-identical**, preserving 70%–95% KV cache hit rates (`30×–50×` cheaper input tokens on DeepSeek, `10×` on Anthropic).
3. Only include earlier prefix tiers when suffix-only removal fails to flip `P(A | E)` (which naturally signals an upstream redundant carrier in `system` or `tools`, and narrows search to `suffix_suspects ∪ prefix_tier`).
4. Replace upfront `everything = test(all_chunks)` with incremental suffix-widening (`tail` → `history + system` → `all`), avoiding unnecessary byte-0 cache misses when tail context alone drives the step.

---

## 3. Low-Cost Validation Plan (Colab `$0` + ~$1–$2 Final Check)

| Step | Status | Scope | Compute / Pricing Strategy | Est. Spend |
| :--- | :--- | :--- | :--- | :--- |
| **0. Colab / Self-Hosted Support** | Done (`65d1387`, `6389eb2`) | `--free`, `--model`, `--max-tokens`, `--no-thinking-param`, optional local API key, `notebooks/colab_vllm.ipynb`. | Local tests + Colab `vLLM`. | **$0** |
| **1–3. Core Algorithmic Upgrades** | Done (`65d1387`, `ba1b402`) | Conditional `--given`, `C \ {c_i}` hitchhiker pruning & AND/OR duality, KV-cache-stratified suffix-first search, 99 unit/CLI tests. | Local mock models. | **$0** |
| **4. Phase 3 Attribution Benchmark** | Script ready (`6389eb2`); run on Colab next | Run `experiments/phase3/benchmark.py` (12 cases: `ctxblame` vs. `ctxblame_uncond` vs. `loo` vs. `self_explain`) + record fresh traces & live vLLM prefix-cache hit metrics. | Colab L4 / A100 (`Qwen/Qwen3-8B` or `Qwen3-14B`) via `vLLM --enable-prefix-caching`. | **$0** |
| **5. Final DeepSeek Regression & `v0.2` Release** | Pending | Re-run `experiments/phase2/run.py --only step5 step7` off-peak to update `experiments/phase2/results/results.md`; publish `uvx ctxblame` (`v0.2`) + writeup. | DeepSeek API off-peak (50% discount). | **~$1–$2** |
