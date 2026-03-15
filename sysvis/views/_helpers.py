"""
sysvis/views/_helpers.py
------------------------
Shared utilities used by every view: formatting, colour, bars,
sparklines, keyboard input, and flicker-free screen clearing.
"""

import os
import sys
import time
from datetime import timedelta
from rich.text import Text
from rich.console import Console

con = Console(highlight=False, markup=True)


# ── Screen clear (no flicker) ─────────────────────────────────────────────────

def clear():
    """
    Overwrite screen in-place — no blank flash.
    Uses ANSI escape codes if supported (Windows Terminal, modern PowerShell),
    otherwise falls back to os.system("cls") on Windows.
    """
    if os.environ.get("TERM") or "WT_SESSION" in os.environ:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()
    else:
        os.system("cls")


# ── Colour ────────────────────────────────────────────────────────────────────

def pcolor(p: float) -> str:
    """Rich colour name for a severity percentage."""
    if p >= 85: return "bright_red"
    if p >= 60: return "bright_yellow"
    return "bright_green"


def status_icon(p: float) -> str:
    if p >= 85: return "🔴"
    if p >= 60: return "🟡"
    return "🟢"


# ── Formatters ────────────────────────────────────────────────────────────────

def hb(n: float, s: str = "B") -> str:
    """Human-readable bytes."""
    for u in ("", "K", "M", "G", "T"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {u}{s}"
        n /= 1024.0
    return f"{n:.1f} P{s}"


def uptime_str(sec: float) -> str:
    td = timedelta(seconds=int(sec))
    h, r = divmod(td.seconds, 3600)
    m, s = divmod(r, 60)
    return f"{td.days}d {h:02}h {m:02}m" if td.days else f"{h:02}h {m:02}m {s:02}s"


def trunc(s: str, n: int) -> str:
    return (s[:n - 1] + "…") if len(s) > n else s


# ── Visual elements ───────────────────────────────────────────────────────────

def bar(pct: float, w: int = 30) -> Text:
    """Coloured block bar."""
    pct = max(0.0, min(100.0, pct))
    n   = int(round(pct / 100 * w))
    t   = Text(no_wrap=True)
    t.append("█" * n,       style=pcolor(pct))
    t.append("░" * (w - n), style="grey23")
    return t


def spark(vals: list, w: int = 40) -> Text:
    """Mini sparkline from list of 0-100 floats."""
    chars  = " ▁▂▃▄▅▆▇█"
    recent = (vals or [])[-w:]
    t      = Text(no_wrap=True)
    for v in recent:
        t.append(chars[min(int(v / 100 * 8), 8)], style=pcolor(v))
    t.append("·" * max(0, w - len(recent)), style="grey23")
    return t


# ── Print helpers (clean text, no panels, no boxes) ──────────────────────────

def section(title: str):
    """Print a clean section heading."""
    con.print()
    con.print(f"  [bold bright_cyan]{title}[/]")
    con.print(f"  [grey23]{'─' * (len(title) + 2)}[/]")


def row(label: str, value, label_w: int = 18, value_style: str = "white"):
    """Print a single label: value line."""
    t = Text(no_wrap=True)
    t.append(f"  {label:<{label_w}}", style="cyan")
    if isinstance(value, Text):
        t.append_text(value)
    else:
        t.append(str(value), style=value_style)
    con.print(t)


def bar_row(label: str, pct: float, extra: str = "", label_w: int = 18):
    """Print   label   ████░░░░  73.4%  extra"""
    t = Text(no_wrap=True)
    t.append(f"  {label:<{label_w}}", style="cyan")
    t.append_text(bar(pct, 28))
    t.append(f"  {pct:.1f}%", style=f"bold {pcolor(pct)}")
    if extra:
        t.append(f"  {extra}", style="grey50")
    con.print(t)


def insight(msg: str):
    """Print an insight/tip line."""
    con.print(f"  [grey84]{msg}[/]")


def back_hint():
    con.print()
    con.print("  [grey35]← q or Esc to go back[/]")


# ── Keyboard ──────────────────────────────────────────────────────────────────

def getch() -> str:
    """
    Read one keypress. Returns:
    'UP', 'DOWN', 'ENTER', 'ESC', or lowercase char.
    """
    if sys.platform == "win32":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H": "UP", "P": "DOWN",
                    "K": "LEFT", "M": "RIGHT"}.get(ch2, "")
        if ch == "\r":   return "ENTER"
        if ch == "\x1b": return "ESC"
        if ch == "\x03": raise KeyboardInterrupt
        return ch.lower()
    else:
        import tty, termios
        fd  = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return {"A": "UP", "B": "DOWN",
                            "C": "RIGHT", "D": "LEFT"}.get(ch3, "")
                return "ESC"
            if ch in ("\r", "\n"): return "ENTER"
            if ch == "\x03":       raise KeyboardInterrupt
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def wait_or_back(timeout: float) -> bool:
    """
    Wait `timeout` seconds listening for q/Esc.
    Returns True if user wants to go back.
    """
    import select as _sel
    deadline = time.monotonic() + timeout
    if sys.platform == "win32":
        import msvcrt
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                if getch() in ("ESC", "q"): return True
            time.sleep(0.04)
    else:
        while time.monotonic() < deadline:
            if _sel.select([sys.stdin], [], [], 0.04)[0]:
                if getch() in ("ESC", "q"): return True
    return False