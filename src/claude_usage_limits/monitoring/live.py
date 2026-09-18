"""The live refresh loop (Tab to switch view, Ctrl+C to exit)."""

import os
import select
import signal
import sys
import time
from datetime import datetime

from rich.live import Live

from claude_usage_limits.core.fetcher import fetch_usage_text
from claude_usage_limits.core.parser import parse_usage
from claude_usage_limits.ui.layouts import build_dashboard

try:
    import termios
    import tty
except ImportError:  # not a POSIX terminal (e.g. Windows)
    termios = None
    tty = None



def run_loop(interval, console):
    state = {"data": {}, "error": None, "view": "24h", "last_fetch": 0.0, "fetched_at": None}

    def render():
        countdown = max(0, round(interval - (time.monotonic() - state["last_fetch"])))
        return build_dashboard(state["data"], state["error"], countdown, state["view"], state["fetched_at"])

    def refetch():
        text, error = fetch_usage_text()
        state["data"] = parse_usage(text) if text is not None else {}
        state["error"] = error
        state["last_fetch"] = time.monotonic()
        state["fetched_at"] = datetime.now()

    interactive = sys.stdin.isatty() and termios is not None
    old_settings = None
    if interactive:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    # A self-pipe registered via set_wakeup_fd: the signal trampoline writes a
    # byte to it directly, so a blocked select() wakes up because real data
    # arrived on a watched fd, rather than relying on EINTR interrupting the
    # syscall (which proved unreliable for a cbreak-mode tty in testing).
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_r, False)
    os.set_blocking(wake_w, False)
    old_wakeup_fd = signal.set_wakeup_fd(wake_w)
    old_sigint = signal.signal(signal.SIGINT, lambda signum, frame: None)

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            refetch()
            live.update(render(), refresh=True)
            last_tick = time.monotonic()

            while True:
                remaining = interval - (time.monotonic() - state["last_fetch"])
                if remaining <= 0:
                    refetch()
                    live.update(render(), refresh=True)
                    last_tick = time.monotonic()
                    continue

                watch = [wake_r] + ([sys.stdin] if interactive else [])
                poll_for = min(0.2, remaining)
                ready, _, _ = select.select(watch, [], [], poll_for)
                if wake_r in ready:
                    try:
                        os.read(wake_r, 1024)
                    except OSError:
                        pass
                    raise KeyboardInterrupt
                if interactive and sys.stdin in ready:
                    ch = sys.stdin.read(1)
                    if ch == "\t":
                        state["view"] = "7d" if state["view"] == "24h" else "24h"
                        live.update(render(), refresh=True)
                        last_tick = time.monotonic()

                now = time.monotonic()
                if now - last_tick >= 1.0:
                    live.update(render(), refresh=True)
                    last_tick = now
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.set_wakeup_fd(old_wakeup_fd if old_wakeup_fd != -1 else -1)
        os.close(wake_r)
        os.close(wake_w)
        if interactive and old_settings is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
