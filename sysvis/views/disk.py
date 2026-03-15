"""
sysvis/views/disk.py
--------------------
Disk insight view. Per-partition usage, I/O speeds,
alerts for low space.
"""

from ._helpers import (
    con, pcolor, hb,
    bar, bar_row, section, row, insight, back_hint,
    wait_or_back,clear,
)



def disk(collector):
    """Live disk view."""
    while True:
        data = collector.data
        d    = data["disk"]

        clear()
        con.print()
        con.print("  [bold bright_cyan]DISK[/]")
        con.print()

        # ── Partitions ────────────────────────────────────────────────────────
        if not d.partitions:
            con.print("  [grey50]No partitions detected.[/]")
        else:
            for p in d.partitions:
                bar_row(
                    p["mountpoint"],
                    p["percent"],
                    extra=f"{hb(p['used'])} / {hb(p['total'])}  —  free {hb(p['free'])}  ({p['fstype']})",
                )

        # ── I/O Speed ─────────────────────────────────────────────────────────
        section("Disk I/O")
        row("Write speed",   hb(d.write_speed, "B/s"), value_style="bright_yellow")
        row("Read speed",    hb(d.read_speed,  "B/s"), value_style="bright_green")
        row("Total written", hb(d.write_bytes))
        row("Total read",    hb(d.read_bytes))

        # ── Insights ──────────────────────────────────────────────────────────
        section("Insights")
        has_issue = False
        for p in d.partitions:
            if p["percent"] >= 90:
                insight(f"🔴  {p['mountpoint']} at {p['percent']:.0f}%"
                        f" — only {hb(p['free'])} remaining.")
                insight("    → Delete files, empty trash, or expand storage.")
                has_issue = True
            elif p["percent"] >= 75:
                insight(f"🟡  {p['mountpoint']} at {p['percent']:.0f}%"
                        f" — {hb(p['free'])} remaining. Consider cleanup.")
                has_issue = True

        if d.write_speed > 200 * 1024 * 1024:
            insight(f"⚡  Very high write: {hb(d.write_speed,'B/s')}"
                    " — large file operation in progress.")
        elif d.write_speed > 50 * 1024 * 1024:
            insight(f"ℹ   Write activity: {hb(d.write_speed,'B/s')} — normal for backups/installs.")

        if not has_issue:
            insight("🟢  All partitions have healthy free space.")

        back_hint()

        if wait_or_back(1.0):
            break