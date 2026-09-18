"""Run `claude -p "/usage"` and return its text."""

import json
import subprocess


def fetch_usage_text():
    try:
        proc = subprocess.run(
            ["claude", "-p", "/usage", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        return None, "`claude` CLI not found on PATH."
    except subprocess.TimeoutExpired:
        return None, "`claude -p \"/usage\"` timed out."

    if proc.returncode != 0:
        return None, f"claude exited {proc.returncode}: {proc.stderr.strip()}"

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, f"could not parse claude's JSON output: {proc.stdout.strip()[:200]!r}"

    return payload.get("result", ""), None
