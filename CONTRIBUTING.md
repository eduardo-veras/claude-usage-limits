# Contributing

Thanks for helping out. This is a small project, so the process is light.

## Setup

You need [uv](https://docs.astral.sh/uv/) and, to run the tool for real,
[Claude Code](https://claude.com/claude-code) logged in.

```bash
git clone https://github.com/eduardo-veras/claude-usage-limits
cd claude-usage-limits
uv run --extra test pytest          # run the tests
uv run claude-usage-limits --once   # run from source
```

The code layout is described in the [README](README.md#development).

## Pull requests

- Fork, branch, and open a PR against `main`. CI runs the tests on Linux,
  macOS and Windows; the `tests-passed` check must be green to merge.
- Add or update a test for any behaviour change. Tests must not call the real
  `claude` CLI: use sample text like `SAMPLE` in the test file, or patch
  `fetch_usage_text`.
- Keep runtime dependencies to `rich`. Open an issue first if you think a new
  one is justified.
- The maintainer approves CI runs on PRs from forks by hand, so checks may not
  start right away.

## When `/usage` changes

The parser depends on the wording Claude Code prints for `/usage`, and that can
change between releases. If a row shows "no data":

1. Run `claude -p "/usage"` and copy the output (redact project names if you like).
2. Open an issue with that output and your `claude --version`.

A PR that updates the regexes in `core/parser.py` plus the `SAMPLE` text in the
tests is even better.

## Themes and terminals

If colours are unreadable or glyphs misalign in your terminal, open an issue
with a screenshot, the terminal name, and the `--theme` you used. `--ascii` is
the fallback for terminals that cannot render emoji or block characters.

## Security

Please report vulnerabilities privately; see [SECURITY.md](SECURITY.md).
