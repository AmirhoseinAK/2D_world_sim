"""Extract JSON from LLM output."""
from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict | None:
    """Return the first JSON object found in the text, or None."""
    if not text:
        return None
    text = text.strip()

    # 1) fenced block ```json ... ```
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        obj = _try_load(m.group(1).strip())
        if obj is not None:
            return obj

    # 2) balanced {...} block
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                obj = _try_load(text[start:i + 1])
                if obj is not None:
                    return obj
                start = None

    return None


def _try_load(s: str) -> dict | None:
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None