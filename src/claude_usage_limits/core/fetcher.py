"""Run `claude -p "/usage"` and return its text."""

import json
import shutil
import subprocess


def fetch_usage_text():
    # Resolve the full path first: an npm install on Windows is `claude.cmd`,
    # which subprocess cannot find from the bare name.
    exe = shutil.which("claude")
    if exe is None:
        return None, "`claude` CLI not found on PATH."

    try:
        proc = subprocess.run(
            [exe, "-p", "/usage", "--output-format", "json"],
            capture_output=True,
            # claude prints UTF-8 whatever the locale is (cp1252 on Windows would garble the "·").
            encoding="utf-8",
            errors="replace",
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
