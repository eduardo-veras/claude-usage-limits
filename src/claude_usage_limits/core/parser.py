"""Parse the text output of /usage into a dict."""

import re

from claude_usage_limits.utils.time_utils import WINDOW_SECONDS, time_to_reset

HEADER_RE = {
    "session": re.compile(r"Current session:\s*(\d+)%\s*used\s*·\s*resets\s*(.+)"),
    "week": re.compile(r"Current week \(all models\):\s*(\d+)%\s*used\s*·\s*resets\s*(.+)"),
    "fable": re.compile(r"Current week \(Fable\):\s*(\d+)%\s*used\s*·\s*resets\s*(.+)"),
}

FACTOR_LINE_RE = re.compile(r"^(\d+)% of your usage (.+)$")
TOP_LINE_RE = re.compile(r"^Top ([\w /-]+?):\s*(.+)$")
TOP_ITEM_RE = re.compile(r"^(.+?)\s+(\d+)%$")
BLOCK_HEADER_RE = re.compile(r"Last (24h|7d) · (\d+) requests · (\d+) sessions")



def parse_contrib_block(breakdown_text, which):
    """which is '24h' or '7d'. Returns {requests, sessions, factors, tops} or None."""
    lines = breakdown_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = BLOCK_HEADER_RE.match(line.strip())
        if m and m.group(1) == which:
            start = i
            requests, sessions = int(m.group(2)), int(m.group(3))
            break
    if start is None:
        return None

    factors, tops = [], []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if BLOCK_HEADER_RE.match(stripped):
            break
        fm = FACTOR_LINE_RE.match(stripped)
        if fm:
            factors.append((int(fm.group(1)), fm.group(2)))
            continue
        tm = TOP_LINE_RE.match(stripped)
        if tm:
            items = []
            for piece in tm.group(2).split(", "):
                im = TOP_ITEM_RE.match(piece.strip())
                if im:
                    items.append((im.group(1), int(im.group(2))))
            tops.append((tm.group(1), items))

    return {"requests": requests, "sessions": sessions, "factors": factors, "tops": tops}


def parse_usage(text):
    data = {"session": None, "week": None, "fable": None, "breakdown": ""}
    for key, pattern in HEADER_RE.items():
        m = pattern.search(text)
        if m:
            pct = int(m.group(1))
            resets = m.group(2).strip()
            eta, elapsed_frac, remaining = time_to_reset(resets, WINDOW_SECONDS[key])
            data[key] = {
                "pct": pct,
                "resets": resets,
                "eta": eta,
                "elapsed_frac": elapsed_frac,
                "remaining": remaining,
            }

    marker = "What's contributing to your limits usage?"
    idx = text.find(marker)
    if idx != -1:
        data["breakdown"] = text[idx:].strip()
        data["contrib"] = {
            "24h": parse_contrib_block(data["breakdown"], "24h"),
            "7d": parse_contrib_block(data["breakdown"], "7d"),
        }

    return data
