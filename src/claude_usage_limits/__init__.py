"""Terminal dashboard for Claude account-wide usage limits (session/weekly/Fable).

Shells out to `claude -p "/usage"` (the officially authenticated client, so no
tokens or cookies are handled here), parses the text, and renders it as a
rich.Live dashboard that redraws in place. Press Tab while it's running to
switch the contributing-factors panel between the last-24h and last-7d views.

Look and feel inspired by Claude Monitor
(github.com/Maciek-roboblog/Claude-Code-Usage-Monitor).
"""

__version__ = "0.1.0"
