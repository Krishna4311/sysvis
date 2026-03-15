"""
sysvis/views/processes.py
-------------------------
Top processes by CPU. Shows PID, name, CPU%, MEM%,
status and user. Insights flag runaway processes.
"""

from rich.text import Text
from ._helpers import (
    con, pcolor, hb, trunc,
    bar, section, row, insight, back_hint,
    wait_or_back,clear,
)


def processes(collector):
    """Live top-processes view."""
    while True:
        data    = collector.data
        pr      = data["processes"]
        logical = data["cpu"].logical_cores or 1

        clear()
        con.print()
        con.print("  [bold bright_cyan]PROCESSES[/]")
        con.print()

        # ── Summary ───────────────────────────────────────────────────────────
        con.print(
            f"  [cyan]Total[/]  [white]{pr.total_processes}[/]"
            f"    [cyan]Running[/]  [bright_green]{pr.running}[/]"
            f"    [cyan]Sleeping[/]  [grey50]{pr.sleeping}[/]"
        )
        con.print()

        # ── Table header ──────────────────────────────────────────────────────
        con.print(
            f"  [bold cyan]{'PID':>7}  {'Name':<30}  {'CPU%':>7}  "
            f"{'CPU Bar':<16}  {'MEM%':>6}  {'Status':<10}  User[/]"
        )
        con.print("  [grey23]" + "─" * 90 + "[/]")

        # ── Rows ──────────────────────────────────────────────────────────────
        for p in pr.top_processes:
            raw = p.get("cpu_percent") or 0.0
            cpu = min(raw / logical, 100.0)
            mem = p.get("memory_percent") or 0.0
            st  = p.get("status") or "?"
            usr = trunc((p.get("username") or "?").split("\\")[-1], 12)
            nm  = trunc(p.get("name") or "?", 30)

            line = Text(no_wrap=True)
            line.append(f"  {p.get('pid','?'):>7}  ", style="grey50")
            line.append(f"{nm:<30}  ",                style="white")
            line.append(f"{cpu:6.1f}%  ",             style=f"bold {pcolor(cpu)}")
            line.append_text(bar(cpu, 12))
            line.append(f"  {mem:5.2f}%  ",           style=pcolor(min(mem * 4, 100)))
            line.append(f"{st:<10}  ",
                        style="bright_green" if st == "running" else "grey50")
            line.append(usr,                          style="grey35")
            con.print(line)

        # ── Insights ──────────────────────────────────────────────────────────
        section("Insights")
        tips = []
        top = pr.top_processes
        if top:
            worst = top[0]
            norm  = min((worst.get("cpu_percent") or 0) / logical, 100.0)
            if norm > 50:
                tips.append(
                    f"⚡  '{worst.get('name')}' using {norm:.0f}% CPU "
                    f"(PID {worst.get('pid')}).")
                tips.append("    → Consider closing it if not needed.")
        heavy = sorted(top, key=lambda x: x.get("memory_percent") or 0,
                       reverse=True)
        if heavy and (heavy[0].get("memory_percent") or 0) > 5:
            tips.append(
                f"🧠  '{heavy[0].get('name')}' using "
                f"{heavy[0].get('memory_percent'):.1f}% RAM.")
        if not tips:
            tips.append("🟢  No runaway processes detected.")
        for t in tips:
            insight(t)

        back_hint()

        if wait_or_back(1.0):
            break