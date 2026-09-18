# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report them privately through GitHub: open the
[Security tab](https://github.com/eduardo-veras/claude-usage-limits/security/advisories/new)
and choose **Report a vulnerability**. You should get a first reply within a
week.

## Scope

This tool runs the `claude` CLI found on your `PATH` and parses its text
output. It never reads, stores or transmits Claude credentials and makes no
network requests of its own. Reports that are especially useful:

- ways crafted `/usage` output could make the tool execute code or write files
- problems in how the `claude` executable is located and launched
- vulnerable dependencies

## Supported versions

Only the latest release (or `main`, until there is a release) receives fixes.
