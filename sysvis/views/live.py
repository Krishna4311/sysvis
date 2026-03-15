"""
sysvis/views/live.py
--------------------
Live monitor — compact overview of all key metrics
on one screen. Updates every second.
"""

import time
from rich.text import Text
from ._helpers import (
    con, pcolor, hb, trunc,
    bar, bar_row, spark, section, insight, back_hint,
    wait_or_back,clear,
)


def live(collector):
    """Live all-metrics overview."""
    hist_cpu, hist_mem = [], []

    while True:
        data    = collector.data
        cpu     = data["cpu"]
        mem     = data["memory"]
        disk    = data["disk"]
        net     = data["network"]
        pr      = data["processes"]
        logical = cpu.logical_cores or 1
        total   = min(cpu.percent_total, 100.0)
        now     = time.strftime("%H:%M:%S")

        hist_cpu.append(total)
        hist_mem.append(mem.ram_percent)
        hist_cpu = hist_cpu[-50:]
        hist_mem = hist_mem[-50:]

        clear()
        con.print()
        con.print(f"  [bold bright_cyan]LIVE MONITOR[/]  [grey50]{now}[/]")
        con.print()

        # ── CPU + RAM ─────────────────────────────────────────────────────────
        bar_row("CPU", total,
                extra=f"{cpu.physical_cores}P/{cpu.logical_cores}L  "
                      f"{cpu.freq_current:.0f} MHz")
        bar_row("RAM", mem.ram_percent,
                extra=f"{hb(mem.ram_used)} / {hb(mem.ram_total)}  "
                      f"free {hb(mem.ram_free)}")

        # ── Swap (only if in use) ─────────────────────────────────────────────
        if mem.swap_percent > 0:
            bar_row("SWAP", mem.swap_percent,
                    extra=f"{hb(mem.swap_used)} / {hb(mem.swap_total)}")

        # ── Network ───────────────────────────────────────────────────────────
        con.print()
        from ._helpers import row
        row("↑ Upload",   hb(net.upload_speed,   "B/s"), value_style="bold bright_yellow")
        row("↓ Download", hb(net.download_speed, "B/s"), value_style="bold bright_green")

        # ── Disk ──────────────────────────────────────────────────────────────
        con.print()
        row("Disk Write", hb(disk.write_speed, "B/s"), value_style="bright_yellow")
        row("Disk Read",  hb(disk.read_speed,  "B/s"), value_style="bright_green")
        for p in disk.partitions[:3]:
            bar_row(p["mountpoint"], p["percent"],
                    extra=f"free {hb(p['free'])}", label_w=10)

        # ── History ───────────────────────────────────────────────────────────
        section("History  (last 50s)")
        cpu_sp = Text(no_wrap=True)
        cpu_sp.append("  CPU  ", style="grey50")
        cpu_sp.append_text(spark(hist_cpu, 50))
        cpu_sp.append(f"  {total:.1f}%", style="grey50")
        con.print(cpu_sp)

        mem_sp = Text(no_wrap=True)
        mem_sp.append("  RAM  ", style="grey50")
        mem_sp.append_text(spark(hist_mem, 50))
        mem_sp.append(f"  {mem.ram_percent:.1f}%", style="grey50")
        con.print(mem_sp)

        # ── Top 5 processes ───────────────────────────────────────────────────
        section("Top Processes")
        for p in pr.top_processes[:5]:
            c  = min((p.get("cpu_percent") or 0) / logical, 100.0)
            m  = p.get("memory_percent") or 0.0
            nm = trunc(p.get("name") or "?", 28)
            con.print(
                f"  [grey50]{p.get('pid','?'):>6}[/]  "
                f"[white]{nm:<28}[/]  "
                f"[{pcolor(c)}]{c:5.1f}%[/]  "
                f"[grey50]mem {m:.1f}%[/]"
            )

        back_hint()

        if wait_or_back(1.0):
            break