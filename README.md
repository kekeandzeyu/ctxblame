# ctxblame

"git blame" for LLM agent decisions: replay one recorded LLM request with
pieces of context removed and report which chunk caused the decision.
Works with any model: the evidence comes from replays, not from the model's
own explanation. Status: early; the blame engine works on the validation cases below, not yet on PyPI.

Two wire formats are supported, which covers most models: Anthropic Messages
(`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`).

## Record

```sh
# Anthropic format (Claude, or DeepSeek's Anthropic endpoint)
uv run ctxblame record --upstream https://api.deepseek.com/anthropic
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 your-agent ...

# OpenAI format (OpenAI, DeepSeek, Qwen, OpenRouter, vLLM, Ollama, ...)
uv run ctxblame record --upstream https://api.deepseek.com
OPENAI_BASE_URL=http://127.0.0.1:8787 your-agent ...
```

The proxy appends every `POST /v1/messages` or `POST /chat/completions`
exchange to one JSON-lines trace (`traces/<time>-<id>.jsonl`, or `--trace
FILE`), numbered in send order: the request body, and either the response
body or (for streams) every raw SSE event plus the reassembled message. Auth
headers are forwarded but never written to disk. `traces/` is git-ignored
because it holds your prompts.

```sh
uv run ctxblame steps traces/<trace>.jsonl          # one line per LLM call and its decision
```

## Replay

```sh
export DEEPSEEK_API_KEY=...        # or ANTHROPIC_API_KEY / OPENAI_API_KEY; see --api-key-env
uv run ctxblame replay traces/<trace>.jsonl --step 14 -n 10
```

Re-sends the recorded request unchanged N times (no tool is executed) and
reports how often the same decision comes back, with a 95% interval. "Same
decision" defaults to `--match intent`: what the call does, whichever tool
does it (`Read src/a.py` and `Bash cat src/a.py` are both `read src/a.py`).
`--match exact|args|name` and `--key-arg` are stricter or looser.
Every call is priced and logged to `.ctxblame/spend.jsonl`; `--budget`
(default $5) is a hard cap across runs.

## Ablation

```sh
uv run ctxblame replay T.jsonl --step 14 --list-units          # what can be removed
uv run ctxblame replay T.jsonl --step 14 -n 20 --remove pair:toolu_12
uv run ctxblame replay T.jsonl --step 14 -n 20 --remove-text "We use pnpm in this repo."
uv run ctxblame replay T.jsonl --step 14 -n 10 --remove-random 45 --seed 1 --protect "<the user's task>"
```

Removing a tool call always removes its result too (and the reverse), empty
messages are dropped and same-role neighbours merged, so the ablated request
stays valid. `--key-arg 'command~\bpnpm\b'` makes "same decision" mean "the
command matches this regex" instead of exact arguments. `--any-call` counts a reply as the same
decision when any of its parallel tool calls matches. `thinking:msg[i]`
removes one turn's reasoning (its calls get fresh ids, so a provider that
keeps reasoning server-side cannot restore it).

## Blame

```sh
uv run ctxblame why traces/<trace>.jsonl --step 14

# Conditional / contrastive blame (auto-enabled with --key-arg; --given none to disable)
uv run ctxblame why traces/<trace>.jsonl --step 5 --key-arg 'command~^python -m pytest'

# Run against a local or Google Colab vLLM/Ollama server at $0 API cost
uv run ctxblame why traces/<trace>.jsonl --step 5 --key-arg 'command~^python -m pytest' \
    --base-url http://127.0.0.1:8000/v1 --model Qwen/Qwen3-8B --max-tokens 2048 --no-thinking-param --free
```

```
Decision:  Bash({"command~\\bpnpm\\b": true})
Baseline:  10/10 replays (stable)
Given:     Bash (10/10 baseline; P(decision | given) = 10/10)
Chunks:    8 (3 tool desc, 1 system, 1 user, 2 assistant, 1 tool call)
Everything but the task removed: 0/10 (given 10/10)  -> the decision comes from the context

Cause 1 (removing it flips the decision: 1/20 (given 20/20)):
  - turn 0 user message sentence 3: 'We use pnpm in this repo, never npm or yarn.'
  controls (random same-size removals): 5/5 (given 5/5), 5/5 (given 5/5)

Tests: 16, replays: 160, cost $0.07
```

How it works:

1. **Baseline & Conditioning (`--given`).** Replay the step unchanged. If no
   decision comes back reliably it stops ("coin flip"); if the recorded call is
   unusual it explains the usual one instead. When `--key-arg` or `--given` is
   set, blame conditions on the coarser action family `E` (e.g. `run pytest` or
   tool `Bash`) and scores `P(decision | E)` separately from `P(E)`.
2. **Chunks & KV-Cache Tiers.** System-prompt paragraphs, earlier user and
   assistant text, each tool call with its result, each turn's reasoning, and
   tool descriptions are partitioned from prefix to suffix (`Tool Schemas →
   System Prompt → Early History → Tail History`). The task (the latest user
   message with text) is never removed.
3. **Suffix-First Stratified Search & Precondition Isolation.** Instead of
   mutating byte `0` upfront, search widens from tail history toward prefix
   tiers to preserve KV prompt-cache hits. If removing a subset collapses
   `P(E)` (e.g. removing an earlier `edit_file` makes the agent stop running
   tests altogether), that workflow precondition is isolated, reported under
   `Preconditions`, and auto-protected while choice search continues on
   `P(decision | E)`.
4. **Hitchhiker Pruning & Refinement.** Multi-member bundles are verified via a
   leave-one-in restoration check (`C \ {c_i}`): holding all other carriers
   removed must prove each `c_i` alone restores the decision (pruning noisy
   hitchhikers and distinguishing single necessary `AND` chunks from minimal
   `OR` hitting sets). Each surviving member is refined to the lines that
   matter.
5. **Check.** Each finding is confirmed with more replays, and compared with
   random removals of the same size. Findings that random removals reproduce
   too are reported as *context the decision needs (not specific)*, not as
   causes.

Each test replays in batches of 5 until the rate is clearly above or below
half the baseline rate (a flip needs at least 10 replays). By default a reply
counts as the same decision when *any* of its parallel calls matches
(`--first-call` to compare only the first). Removing reasoning gives those
calls fresh ids; a provider that then demands the reasoning makes it
"not removable", and the report says so. `--budget` caps the spend, `--free`
(or any unknown model on `localhost`/`127.0.0.1`) runs at `$0`, and the full
log of tests plus `cache_stats` is saved as JSON in `runs/`.

## Run at $0 on Google Colab (vLLM)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kekeandzeyu/ctxblame/blob/main/notebooks/colab_vllm.ipynb)

Open [notebooks/colab_vllm.ipynb](notebooks/colab_vllm.ipynb) on a Colab **L4**
or **A100** GPU to serve an open tool-calling model (`Qwen/Qwen3-8B` or
`Qwen3-14B`) via `vLLM --enable-prefix-caching` and run `ctxblame why` or the
Phase 3 attribution benchmark at **$0 API cost**.

## Experiments & Benchmarks

- **Phase 0** ([experiments/phase0](experiments/phase0/README.md)): five
  planted-cause scenarios, both wire formats, two DeepSeek models.
- **Phase 1** ([experiments/phase1](experiments/phase1/README.md)): planted
  causes in real agent traces with thinking on. Causes are usually redundant,
  the agent's own history takes over later in a run, and DeepSeek restores
  removed reasoning server-side unless the call ids change.
- **Phase 2** ([experiments/phase2/results/results.md](experiments/phase2/results/results.md)):
  end-to-end validation of the original `ddmin` engine, exposing precondition
  confounding (`step5`/`step7`), hitchhikers, and byte-0 cache invalidation.
- **Phase 3–4** ([experiments/phase3/RESULTS.md](experiments/phase3/RESULTS.md)):
  attribution benchmark on open models at $0 (Qwen3-8B, Qwen3-14B-FP8 with
  thinking off and on, Llama-3.1-8B; vLLM, 3 seeds, oracle-validated cases): generated cases (8 tool conventions
  × 5 carrier places, redundancy, preconditions, negatives), ~35k-char
  prompts, and 15 real recorded agent runs. ctxblame against
  `--given none`, ContextCite, leave-one-out and self-explanation:

  | F1 | Qwen3-8B gen | Qwen3-14B gen | Qwen3-14B gen, thinking on | Llama-3.1-8B gen | Qwen3-14B real traces | Qwen3-14B long prompts |
  |---|---:|---:|---:|---:|---:|---:|
  | **ctxblame** | **94%** | **95%** | **95%** | **85%** | **92%** | **95%** |
  | ctxblame `--given none` | 79% | 76% | 81% | 77% | 60% | – |
  | ContextCite | 71% | 84% | 83% | 84% | 29% | – |
  | self-explanation | 73% | 60% | 80% | 67% | 46% | – |
  | leave-one-out | 34% | 39% | 34% | 36% | 0% | – |

  On the noisier Llama-3.1-8B, ctxblame ties ContextCite on F1 but is still
  the only method that separates preconditions and gets negatives right.
  On long requests the suffix-first search needs 27% fewer replays and 34–38%
  less uncached input than a flat search; on short ones it saves nothing.
  ```sh
  uv run python experiments/phase3/benchmark.py --dry-run   # offline check ($0)
  ```

## Related Work & Limitations

### How `ctxblame` differs from prior work
- **Logprob-based context attribution ([ContextCite](https://arxiv.org/abs/2409.00729)):** Fits a sparse linear surrogate over random context ablations using token log-probabilities. That works well for single-turn text generation on open-logprob endpoints, whereas `ctxblame` targets **discrete black-box tool decisions** (`/v1/messages` and closed thinking models expose no input/output logprobs), handles **redundant `OR`-carriers** (where single-chunk leave-one-out effects are ~0 because `AGENTS.md`, tool schemas, and earlier turns back each other up), and separates **workflow preconditions from choice carriers** (`--given`). In our benchmark ContextCite does find redundant carriers (its random ablations remove backups together), but it blames workflow preconditions as causes, never answers "nothing in the context", and drops to 29% F1 on real agent traces (ctxblame: 92%).
- **Trajectory-level auditing (Counterfactual Trace Auditing, LangSmith / Braintrust playgrounds):** Whole-run audits re-execute entire multi-step sessions with or without a skill, while UI playgrounds rely on manual prompt editing. `ctxblame` automates exact **single-step request blame** with statistical stopping rules and KV-cache-aware search.

### Scope & practical limits
- **An MRI for stubborn bugs, not an every-turn linter:** Isolating minimal causes takes ~200 replays per blamed step on short requests and ~300–550 on long agent traces (`$0` on local/Colab `vLLM`, `~$0.05–$0.10` on DeepSeek/Flash with prefix caching, but up to several dollars and 1–2 minutes on 60k+ token frontier models). Run it on the specific turn where an agent went off the rails.
- **Upfront proxy capture (until `v0.3` log import):** `ctxblame` currently requires recording traffic through `ctxblame record` before the failure happens; retroactive import from existing local CLI transcripts is scheduled next (`v0.3`).
- **High-entropy / coin-flip turns:** If the unablated step already splits ~50/50 across decisions on replay, there is no stable decision for context ablation to explain (`ctxblame` detects this on baseline replay and stops early).

## Next Steps

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full technical audit, bottleneck analysis, and milestone details. Milestones 1–3 (`--given` conditional blame, `C \ {c_i}` hitchhiker pruning & AND/OR duality, KV-cache-stratified suffix-first search, and `$0` local/Colab vLLM support) are implemented and unit-tested.

### `v0.2` — Empirical Validation & Initial Release (In Progress)
1. ~~**Phase 3–4 benchmark on open models**~~ — done: see [experiments/phase3/RESULTS.md](experiments/phase3/RESULTS.md). Milestone 1's acceptance (all carriers, 100% precision, edits kept apart) holds on real Qwen3-14B agent traces.
2. **Robustness at $0:** a second model family (Llama-3.1-8B or Mistral), Qwen3 with thinking on, and cases where the carrier decides whether the agent acts at all (`gen-open`). The paid DeepSeek re-run of `experiments/phase2/run.py --only step5 step7` (~$1–$2) is now optional.
3. **Publish `v0.2`:** Commit benchmark tables, package `ctxblame` (`uvx ctxblame`) on PyPI, and publish the technical writeup (highlighting server-side reasoning-cache restoration, `OR`-carrier redundancy, and `--given` precondition isolation).

### `v0.3` — Zero-Setup Adoption & Prompt-Repair Workflow
1. **Retroactive transcript importers (`ctxblame import`):** Reconstruct replayable `/v1/messages` and `/chat/completions` requests directly from local session logs already saved by **Claude Code** (`~/.claude/projects/**/*.jsonl`), **OpenCode**, and **Harbor**—eliminating the need to run a proxy *before* a surprise bug occurs.
2. **One-command CLI wrapper (`ctxblame wrap -- claude`):** Auto-assign an ephemeral local proxy port and inject `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` in one command when full wire-level SSE capture is wanted.
3. **3-second counterfactual fix verification (`--replace-text` / `ctxblame verify`):** Once `ctxblame why` blames a specific line in `CLAUDE.md`, `AGENTS.md`, or a tool schema, replay that frozen step (`-n 10`) with the user's edited wording to verify the fix flips the tool call before launching a new full session.

## Tests

```sh
uv run pytest
```
