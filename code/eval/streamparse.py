#!/usr/bin/env python3
"""Correct stream-json parsing for the eval harness.

stream-json emits each assistant message MULTIPLE times (streaming partials), every
copy carrying the SAME usage block and a progressively-more-complete content list.
Summing every copy inflated tokens ~3x and turn/tool counts ~2x. And summing
cache_read (context RE-READ each turn) as if it were context size inflated again.

`deduped_messages` collapses to one entry per message id (the copy with the most
tool_use blocks; usage is identical across copies). `metrics` then reports numbers
that mean something: real turns, peak context window, new tokens (cache_creation),
and price-weighted cost. Use these instead of summing raw per-event usage.
"""
from __future__ import annotations
import json

# Anthropic price multiples relative to base input: cache_read 0.1, cache_write 1.25, output 5.
CR, CW, OUT = 0.1, 1.25, 5.0


def deduped_messages(raw: str):
    """Return (messages, answer). messages = ordered list of {"usage", "tools"} (one per
    message id, the most-complete copy). answer = the final result text."""
    by, order, answer = {}, [], ""
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            m = ev.get("message", {})
            mid = m.get("id")
            tools = [b.get("name", "") for b in m.get("content", []) if b.get("type") == "tool_use"]
            tool_inputs = [(b.get("name", ""), b.get("input", {}) or {})
                           for b in m.get("content", []) if b.get("type") == "tool_use"]
            if mid not in by:
                order.append(mid)
            # keep the copy with the most tool_use blocks (the completed one)
            if mid not in by or len(tools) > len(by[mid]["tools"]):
                by[mid] = {"usage": m.get("usage", {}) or {}, "tools": tools, "inputs": tool_inputs}
        elif t == "result":
            answer = ev.get("result", "") or ""
    return [by[mid] for mid in order], answer


def metrics(messages: list) -> dict:
    """Corrected token/turn metrics from deduped messages."""
    def g(u, k):
        return u.get(k, 0)
    if not messages:
        return {"turns": 0, "peak_ctx": 0, "new_tok": 0, "out_tok": 0, "cost_wt": 0}
    turns = sum(1 for m in messages if m["tools"])
    peak = max(g(m["usage"], "input_tokens") + g(m["usage"], "cache_read_input_tokens")
               + g(m["usage"], "cache_creation_input_tokens") for m in messages)
    new = sum(g(m["usage"], "cache_creation_input_tokens") for m in messages)
    out = sum(g(m["usage"], "output_tokens") for m in messages)
    cost = sum(g(m["usage"], "input_tokens") + CR * g(m["usage"], "cache_read_input_tokens")
               + CW * g(m["usage"], "cache_creation_input_tokens") + OUT * g(m["usage"], "output_tokens")
               for m in messages)
    return {"turns": turns, "peak_ctx": peak, "new_tok": new, "out_tok": out, "cost_wt": round(cost)}
