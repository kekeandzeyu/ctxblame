"""ContextCite-style baseline (Cohen-Wang et al., 2024) on a vLLM server.

Needs token log-probabilities, so it only runs where we host the model (vLLM).
For one case:

1. Render the request and the target reply (the recorded tool call) with the
   model's chat template via vLLM's ``/tokenize``; the reply tokens are the
   suffix after the generation prompt.
2. Draw ``n_ablations`` random masks over the coarse chunks (each kept with
   p = 0.5), apply each mask with ``apply_chunks`` (same structure-preserving
   removal as ctxblame), and score log p(reply | ablated prompt) with one
   prefill each (``/v1/completions`` with ``prompt_logprobs``).
3. Fit a Lasso linear surrogate  logp ~ w . mask + b  and report the chunks
   with w_i >= ``rel`` * max(w) (and w_i > 0) as the cause set.

A linear surrogate gives each of k redundant carriers only part of the effect
(the reply survives while any backup is present), which is the failure mode
ctxblame's set search is built for; this baseline measures it directly.
"""

from __future__ import annotations

import asyncio
import random
import time

import numpy as np
from aiohttp import ClientSession, ClientTimeout

from ctxblame.ablate import AblationError
from ctxblame.blame import apply_chunks, chunk_request


def lasso(X: np.ndarray, y: np.ndarray, alpha: float, iters: int = 2000) -> np.ndarray:
    """Coordinate-descent Lasso with intercept (columns standardized internally)."""
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    yc = y - y.mean()
    n, p = Z.shape
    w = np.zeros(p)
    r = yc.copy()
    col = (Z ** 2).sum(0) / n
    for _ in range(iters):
        w_old = w.copy()
        for j in range(p):
            if col[j] == 0:
                continue
            r += Z[:, j] * w[j]
            rho = Z[:, j] @ r / n
            w[j] = np.sign(rho) * max(abs(rho) - alpha, 0.0) / col[j]
            r -= Z[:, j] * w[j]
        if np.max(np.abs(w - w_old)) < 1e-6:
            break
    return w / sd


def _oai_tools(body: dict) -> list | None:
    return body.get("tools")


async def _tokenize(session: ClientSession, base: str, model: str, messages: list, tools, gen_prompt: bool,
                    extra: dict) -> list[int]:
    req = {"model": model, "messages": messages, "add_generation_prompt": gen_prompt,
           "add_special_tokens": False}
    if tools:
        req["tools"] = tools
    if extra.get("chat_template_kwargs"):
        req["chat_template_kwargs"] = extra["chat_template_kwargs"]
    root = base[:-3] if base.endswith("/v1") else base
    async with session.post(root + "/tokenize", json=req) as r:
        j = await r.json()
        if r.status != 200:
            raise RuntimeError(f"/tokenize {r.status}: {str(j)[:300]}")
        return j["tokens"]


async def _logprob(session: ClientSession, base: str, model: str, prompt: list[int], reply: list[int]) -> float:
    req = {"model": model, "prompt": prompt + reply, "max_tokens": 1, "prompt_logprobs": 0, "temperature": 0}
    async with session.post(base + "/completions", json=req) as r:
        j = await r.json()
        if r.status != 200:
            raise RuntimeError(f"/completions {r.status}: {str(j)[:300]}")
    plp = j["choices"][0]["prompt_logprobs"]
    total = 0.0
    for pos, tok in zip(range(len(prompt), len(prompt) + len(reply)), reply):
        d = plp[pos] or {}
        e = d.get(str(tok)) or d.get(tok)
        if e is None:  # should not happen with prompt_logprobs=0 (the actual token is always included)
            raise RuntimeError("missing prompt logprob")
        total += e["logprob"] if isinstance(e, dict) else float(e)
    return total


async def contextcite(step, base: str, model: str, protect=(), n_ablations: int = 64, seed: int = 0,
                      rel: float = 0.25, alpha: float = 0.01, extra_body: dict | None = None,
                      concurrency: int = 32) -> dict:
    t0 = time.monotonic()
    extra = extra_body or {}
    fmt, body = step.fmt, step.body
    if fmt != "openai":
        raise ValueError("contextcite baseline supports OpenAI-format cases only")
    chunks = [c for c in chunk_request(fmt, body, protect) if c.kind != "thinking"]
    resp_msg = step.response["choices"][0]["message"]
    reply_msg = {"role": "assistant", "content": resp_msg.get("content") or "",
                 "tool_calls": resp_msg.get("tool_calls")}
    rng = random.Random(seed)
    masks = [[rng.random() < 0.5 for _ in chunks] for _ in range(n_ablations)]
    masks[0] = [True] * len(chunks)  # the full context
    sem = asyncio.Semaphore(concurrency)
    async with ClientSession(timeout=ClientTimeout(total=600)) as session:
        async def score(mask) -> float | None:
            removed = [c for c, keep in zip(chunks, mask) if not keep]
            try:
                b = apply_chunks(fmt, body, removed) if removed else body
            except AblationError:
                return None
            async with sem:
                p = await _tokenize(session, base, model, b["messages"], _oai_tools(b), True, extra)
                full = await _tokenize(session, base, model, b["messages"] + [reply_msg], _oai_tools(b), False,
                                       extra)
                if full[:len(p)] != p:  # template re-renders earlier turns: fall back to common prefix
                    k = 0
                    while k < min(len(p), len(full)) and p[k] == full[k]:
                        k += 1
                    p = full[:k]
                reply = full[len(p):]
                return await _logprob(session, base, model, p, reply)

        ys = await asyncio.gather(*(score(m) for m in masks))
    rows = [(m, y) for m, y in zip(masks, ys) if y is not None]
    X = np.array([[1.0 if k else 0.0 for k in m] for m, _ in rows])
    y = np.array([v for _, v in rows])
    w = lasso(X, y, alpha) if len(rows) > 2 else np.zeros(len(chunks))
    top = float(w.max()) if len(w) else 0.0
    picked = [i for i, wi in enumerate(w) if wi > 0 and wi >= rel * top]
    picked.sort(key=lambda i: -w[i])
    causes = [{"relation": "contextcite",
               "members": [{"id": chunks[i].id, "kind": chunks[i].kind, "label": chunks[i].label,
                            "text": chunks[i].text, "weight": float(w[i])} for i in picked],
               "specific": True}] if picked else []
    return {"result": "causes" if causes else "not_in_context", "causes": causes, "preconditions": [],
            "weights": {chunks[i].id: float(w[i]) for i in range(len(chunks))},
            "full_logprob": ys[0], "replays": len(rows), "cost": 0.0,
            "seconds": round(time.monotonic() - t0, 2), "cache_stats": {}}
