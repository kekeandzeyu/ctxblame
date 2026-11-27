# ctxblame: which part of the context made the agent do that?

*v0.2 technical writeup, November 2026. Code, traces and every number below:
[github.com/kekeandzeyu/ctxblame](https://github.com/kekeandzeyu/ctxblame).*

A coding agent runs `python -m pytest` when your repository uses `tox`, or
deploys without checking the freeze calendar. Its request held 20k tokens:
system prompt, AGENTS.md, tool schemas, files it read, its own earlier calls.
Which of them made it do that?

`ctxblame` answers by experiment. It records the agent's LLM traffic through a
local proxy, replays one step with pieces of context removed, and reports the
smallest set of pieces whose removal changes the tool call, with confidence
intervals and random-removal controls. It needs no logprobs and no model
weights, so it works on closed models over the Anthropic Messages and OpenAI
Chat Completions APIs.

## Why this is not just leave-one-out

Three things we found on real agent traces (DeepSeek, Phases 0–2) make the
obvious approaches fail:

1. **Causes are redundant.** The test command is in AGENTS.md, in the bash
   tool's parameter example, and, after the first run, in the agent's own
   history. Removing any one changes nothing (20/20); removing all three
   drops the decision to 5–8/20. Leave-one-out calls every carrier
   irrelevant.
2. **Preconditions look like causes.** Remove the `edit_file` call before a
   test run and the agent goes back to editing instead of testing. An
   unconditional test of "does it still run `python -m pytest`" sees a flip
   and blames the edit. Our first engine did exactly that: 0% precision on
   one step, 60% on another.
3. **Where you remove matters more than how much, for cost.** Removing text
   from the system prompt invalidates the provider's prefix cache for the
   whole request: one 20k-token step cost $2.42 because every replay was
   billed uncached. (Also: DeepSeek restores removed reasoning server-side,
   keyed by tool-call id, unless the ids change. `ctxblame` renames them.)

## How it works

1. **Baseline.** Replay the step unchanged (10×). If the decision is a coin
   flip, stop: there is nothing stable to explain.
2. **Conditional blame, `P(A | E)`.** With `--key-arg` (what makes the call
   *this* call, e.g. `command~tox -e py312`) ctxblame also tracks the coarser
   action family `E` ("runs the tests"). A removal that stops the agent from
   acting at all is a **precondition**: it is reported separately and
   protected, and the search continues on `P(A | E)`.
3. **Suffix-first search.** Chunks are ordered tool schemas → system prompt →
   early history → tail history. The search removes from the tail first and
   widens toward the prefix only when it must, so most replays keep the
   cached prefix byte-identical. Within the chosen region, delta debugging
   (`ddmin`) finds a minimal removal that flips the decision.
4. **OR bundles.** A minimal removal with several members is checked
   leave-one-in: with all other members removed, keeping `c_i` alone must
   restore the decision. Members that fail are hitchhikers and are pruned.
   Each surviving member is refined to the lines that matter.
5. **Controls.** Every finding is re-tested with more replays and compared
   with random removals of the same size. If random removals flip it too, it
   is reported as "context the decision needs (not specific)", not as a cause.

Every test replays in batches of 5 until a Wilson interval is clearly above or
below half the baseline rate.

## Benchmark

To score attribution you need ground truth, so we plant it, and then check
that the model under test actually uses it. On open models served by vLLM
(one RTX 4090, $0 in API costs), we built:

- **Generated cases**: 8 tool conventions (tox, hatch, make, pnpm, uv, ruff,
  cargo, a script) planted in 5 places (system prompt, tool description, a
  file the agent read, the user's message, the agent's earlier calls), with 1–3
  redundant carriers, an optional edit precondition, and negatives where the
  decision is the model's habit and nothing in the context drives it.
- **Long prompts**: the same cases behind a ~30k-character agent manual.
- **Real traces**: 15 runs of a small coding agent driven by Qwen3-14B fixing
  a planted bug. Carriers are the AGENTS.md rule, the tool example and the
  agent's earlier test runs; the precondition is the edits since the last run.

An **oracle** keeps only valid cases: on the model under test, the base
decision is stable, removing all carriers flips it, each carrier alone
restores it, and removing the precondition stops the action. Everything is
run with 3 seeds; F1 is averaged over case × seed with a bootstrap CI over
cases.

Baselines: ctxblame without conditioning (`--given none`); leave-one-out
over chunks; asking the model which context made it choose; and
ContextCite-style attribution (a Lasso surrogate over 64 random ablations,
fit on the prompt log-probability of the call, our reimplementation using
vLLM's `prompt_logprobs`).

### Results

| F1 | Qwen3-8B gen (53) | Qwen3-14B gen (48) | Qwen3-14B thinking (55) | Llama-3.1-8B gen (46) | Qwen3-14B real (13) | Qwen3-14B long (38) |
|---|---:|---:|---:|---:|---:|---:|
| **ctxblame** | **94%** | **95%** | **95%** | **85%** | **92%** | **95%** |
| ctxblame `--given none` | 79% | 76% | 81% | 77% | 60% | – |
| ContextCite | 71% | 84% | 83% | 84% | 29% | – |
| self-explanation | 73% | 60% | 80% | 67% | 46% | – |
| leave-one-out | 34% | 39% | 34% | 36% | 0% | – |

(number of oracle-valid cases in parentheses)

Two properties no baseline has:

- **Preconditions kept apart from causes**: ctxblame 76–100% of precondition
  cases; every baseline 0%. Leave-one-out, ContextCite and unconditional
  ctxblame blame the edit in 91–100% of them.
- **"Nothing in the context did this"**: on negatives ctxblame is 97–100%
  correct; ContextCite 0% and self-explanation 0–27%, because they always name
  something.

On real traces the gap is widest (92% vs ≤60%): every carrier is backed up,
so leave-one-out finds nothing, and there is always an edit to blame.

### Cost

| Requests | Replays per case (suffix-first / flat) | Uncached input (suffix-first / flat) |
|---|---:|---:|
| short, 2–6k chars | 204 / 193 | same |
| real traces, 14–26k chars | 545 / 707 | −38% |
| long, ~35k chars | 275 / 376 | −34% |

The saving grows with the length of the request. We planned for 5–10× and
measured about 1.5×. On long prompts the suffix-first search is also more
accurate (95% vs 90% F1), because removals stay small. A blamed step takes
~200 replays on short requests and 300–550 on long ones. That's free on a local
GPU and cents on a cached API, but minutes and possibly dollars on a 60k-token
frontier-model session.

## What we got wrong, and what we don't know

- **ContextCite is better than we expected.** We assumed it would give
  redundant carriers ~0 weight, like leave-one-out. Its random multi-chunk
  ablations remove backups together, so it recalls 88–96% of carriers. It
  loses on preconditions and negatives, on precision in real traces (23%),
  and it needs logprobs, which closed thinking models don't expose.
- **Noisy models.** On Llama-3.1-8B, ctxblame ties ContextCite on F1. Llama's
  decision also moves when neutral lines ("Understood.", another tool's
  description) are removed together with the planted carriers, so they end
  up in OR bundles. Two stricter checks (confirming that the line clearly
  restores the decision, and that it still does when random other text is
  removed too) changed nothing: these lines pass them. They seem to be real
  interactions in that model, which a planted ground truth counts as false
  positives. Both checks ship as opt-in flags (`--strict-restore`,
  `--member-controls`).
- **One real failure.** When whether the agent tests at all hinges on
  scattered file contents it just read, not on an edit, ctxblame reports the
  precondition and finds no carriers.
- **Thin real-agent evidence.** 13 real cases from one task and one
  convention; the CI is 77–100%.
- **The upgraded engine is validated on open models only.** The DeepSeek
  findings above come from the first engine; we did not re-run the paid
  check.
- **Thinking.** With thinking on, ctxblame's accuracy is unchanged, but each
  replay is ~5× slower. Self-explanation benefits most from thinking (60% →
  80%) but still invents a cause for 73% of negatives.

## Try it

```sh
uvx --from git+https://github.com/kekeandzeyu/ctxblame@v0.2.0 ctxblame --help
ctxblame record --upstream https://api.deepseek.com      # then point your agent at it
ctxblame steps traces/<trace>.jsonl
ctxblame why traces/<trace>.jsonl --step 5 --key-arg 'command~^python -m pytest'
```

To reproduce the benchmark on your own GPU, see
[experiments/phase3/RESULTS.md](../experiments/phase3/RESULTS.md) and
`experiments/phase3/run_model.sh`.

## Related work

ContextCite (Cohen-Wang et al., NeurIPS 2024) attributes generated text to
context with a sparse linear surrogate over ablations and needs token
log-probabilities. Counterfactual Trace Auditing (2026) compares whole agent
trajectories with and without a skill. ctxblame sits in between: one step,
one discrete tool decision, no logprobs, with preconditions and redundancy
handled explicitly and the provider's prompt cache taken into account.
