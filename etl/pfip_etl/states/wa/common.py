from __future__ import annotations

import re


CORPORATE_SUFFIX_PATTERN = r"\b(LLC|INC|LTD|CORP|CO|COMPANY|PLL C|PLLC|LP|LLP)\b"


def normalize_vendor_name(name: str) -> str:
    cleaned = name.upper().strip()
    cleaned = cleaned.replace("&", " AND ")
    cleaned = re.sub(r"[^A-Z0-9\s]", " ", cleaned)
    cleaned = re.sub(CORPORATE_SUFFIX_PATTERN, " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def standardize_alias_tokens(name: str) -> str:
    standardized = normalize_vendor_name(name)
    tokens = standardized.split()
    rewritten: list[str] = []

    for index, token in enumerate(tokens):
        if token in {"WA", "WAS", "WASH", "WASHING"} and index == len(tokens) - 1:
            rewritten.append("WASHINGTON")
            continue
        if token == "HEALTH" and index + 1 < len(tokens) and tokens[index + 1] == "CARE":
            rewritten.append("HEALTHCARE")
            continue
        if token == "CARE" and index > 0 and tokens[index - 1] == "HEALTH":
            continue
        rewritten.append(token)

    # Washington's checkbook export sometimes truncates long organization names,
    # leaving a dangling single-letter token at the end.
    if len(rewritten) >= 4 and len(rewritten[-1]) == 1:
        rewritten = rewritten[:-1]

    standardized = " ".join(rewritten)
    standardized = re.sub(r"\s+", " ", standardized).strip()
    return standardized
