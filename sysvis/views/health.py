"""
sysvis/views/health.py
----------------------
Health report — A-F grade per category with
specific actionable recommendations.
Single render — press any key to go back.

Colour logic:
  bars use bar_score() — green=good(high score), red=bad(low score)
  this is OPPOSITE to regular bar() which is green=low, red=high
"""

from rich.text import Text
from ._helpers import (
    con, pcolor_score, bar_score, hb, uptime_str,
    section, row, insight,
    getch, clear,
)


def health(collector):
    """System health report — one-shot, press any key to return."""
    data    = collector.data
    cpu     = data["cpu"]
    mem     = data["memory"]
    disk    = data["disk"]
    pr      = data["processes"]
    s       = data["system"]
    logical = cpu.logical_cores or 1
    cpu_pct = min(cpu.percent_total, 100.0)

    # ── Score each category 0-100 (higher = healthier) ────────────────────────
    def score(val, bad, ok):
        """
        val = current value (e.g. CPU %)
        bad = threshold where score = 0   (e.g. 85%)
        ok  = threshold where score = 50  (e.g. 60%)
        below ok = score climbs to 100
        """
        if val >= bad: return 0
        if val >= ok:  return int(50 * (bad - val) / (bad - ok))
        return int(50 + 50 * (ok - val) / ok)

    cpu_score  = score(cpu_pct,          85, 60)
    ram_score  = score(mem.ram_percent,  85, 60)
    swap_score = score(mem.swap_percent, 50, 20)
    worst_disk = max((p["percent"] for p in disk.partitions), default=0)
    disk_score = score(worst_disk,       90, 75)
    overall    = int((cpu_score + ram_score + swap_score + disk_score) / 4)

    def grade(sc):
        if sc >= 80: return ("A", "bright_green",  "Excellent")
        if sc >= 60: return ("B", "bright_green",  "Good")
        if sc >= 40: return ("C", "bright_yellow", "Fair")
        if sc >= 20: return ("D", "bright_red",    "Poor")
        return              ("F", "bright_red",    "Critical")

    clear()
    con.print()
    con.print("  [bold bright_cyan]HEALTH REPORT[/]")
    con.print()

    # ── Overall score ─────────────────────────────────────────────────────────
    ov_g, ov_c, ov_label = grade(overall)
    ov_line = Text(no_wrap=True)
    ov_line.append("  Overall Score  ", style="cyan")
    ov_line.append_text(bar_score(overall, 30))
    ov_line.append(f"  {overall}/100  Grade: ", style="grey50")
    ov_line.append(f"{ov_g}  {ov_label}", style=f"bold {ov_c}")
    con.print(ov_line)
    con.print()

    # ── Per-category scores ───────────────────────────────────────────────────
    for label, sc in [("CPU",  cpu_score),
                      ("RAM",  ram_score),
                      ("Swap", swap_score),
                      ("Disk", disk_score)]:
        g, c, lbl = grade(sc)
        line = Text(no_wrap=True)
        line.append(f"  {label:<6}", style="cyan")
        line.append_text(bar_score(sc, 22))
        line.append(f"  {sc:>3}/100  {g}  {lbl}", style=f"bold {c}")
        con.print(line)

    # ── Recommendations ───────────────────────────────────────────────────────
    section("Recommendations")

    recs = []

    # CPU
    if cpu_pct >= 85:
        recs.append(("🔴", "CPU",
                     f"CPU at {cpu_pct:.0f}% — critically loaded. "
                     "Open Processes view to find the hog."))
    elif cpu_pct >= 60:
        recs.append(("🟡", "CPU",
                     f"CPU at {cpu_pct:.0f}% — elevated under current workload."))
    else:
        recs.append(("🟢", "CPU", f"CPU healthy at {cpu_pct:.0f}%."))

    # RAM
    if mem.ram_percent >= 85:
        recs.append(("🔴", "RAM",
                     f"RAM at {mem.ram_percent:.0f}% "
                     f"({hb(mem.ram_free)} free) — close apps or add RAM."))
    elif mem.ram_percent >= 60:
        recs.append(("🟡", "RAM",
                     f"RAM at {mem.ram_percent:.0f}% — {hb(mem.ram_free)} free. "
                     "Monitor under heavier loads."))
    else:
        recs.append(("🟢", "RAM",
                     f"RAM healthy — {hb(mem.ram_free)} free of {hb(mem.ram_total)}."))

    # Swap
    if mem.swap_percent > 30:
        recs.append(("🔴", "SWAP",
                     f"Swap at {mem.swap_percent:.0f}% — disk paging, "
                     "performance is degraded. Add more RAM."))
    elif mem.swap_percent > 5:
        recs.append(("🟡", "SWAP",
                     f"Swap at {mem.swap_percent:.0f}% — minor usage, watch RAM."))
    else:
        recs.append(("🟢", "SWAP", "Swap idle — RAM is sufficient."))

    # Disk
    for p in disk.partitions:
        if p["percent"] >= 90:
            recs.append(("🔴", "DISK",
                         f"{p['mountpoint']} at {p['percent']:.0f}% — "
                         f"only {hb(p['free'])} left. Delete files immediately."))
        elif p["percent"] >= 75:
            recs.append(("🟡", "DISK",
                         f"{p['mountpoint']} at {p['percent']:.0f}% — "
                         f"{hb(p['free'])} remaining. Clean up soon."))
        else:
            recs.append(("🟢", "DISK",
                         f"{p['mountpoint']} healthy — "
                         f"{hb(p['free'])} free of {hb(p['total'])}."))

    # Top process
    if pr.top_processes:
        top   = pr.top_processes[0]
        top_c = min((top.get("cpu_percent") or 0) / logical, 100.0)
        if top_c > 20:
            recs.append(("⚡", "PROC",
                         f"'{top.get('name')}' (PID {top.get('pid')}) "
                         f"using {top_c:.0f}% CPU."))

    for icon, cat, msg in recs:
        con.print(
            f"  {icon}  [bold cyan]{cat:<6}[/]  [grey84]{msg}[/]"
        )

    # ── Summary ───────────────────────────────────────────────────────────────
    con.print()
    con.print(
        f"  [grey50]System: {s.os_name} {s.os_release}  |  "
        f"Uptime: {uptime_str(s.uptime_seconds)}  |  "
        f"Apps: {s.installed_apps_count}[/]"
    )
    con.print()
    con.print("  [grey35]Press any key to go back[/]")
    getch()