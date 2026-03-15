"""
sysvis/views/memory.py
----------------------
Memory insight view. RAM + swap usage, pressure insights,
history sparkline. Updates every second.
"""

from ._helpers import (
    con, pcolor, hb,
    bar, bar_row, spark, section, row, insight, back_hint,
    wait_or_back,clear,
)


def memory(collector):
    """Live memory view."""
    hist_ram = []

    while True:
        data = collector.data
        m    = data["memory"]
        hist_ram.append(m.ram_percent)
        hist_ram = hist_ram[-60:]

        clear()
        con.print()
        con.print("  [bold bright_cyan]MEMORY[/]")
        con.print()

        # ── RAM ───────────────────────────────────────────────────────────────
        bar_row("RAM", m.ram_percent,
                extra=f"{hb(m.ram_used)} / {hb(m.ram_total)}  —  free {hb(m.ram_free)}")

        # ── SWAP ──────────────────────────────────────────────────────────────
        con.print()
        bar_row("SWAP", m.swap_percent,
                extra=f"{hb(m.swap_used)} / {hb(m.swap_total)}  —  free {hb(m.swap_total - m.swap_used)}")

        # ── History ───────────────────────────────────────────────────────────
        section("RAM History  (last 60s)")
        from rich.text import Text
        sp = Text(no_wrap=True)
        sp.append("  ")
        sp.append_text(spark(hist_ram, 55))
        sp.append(f"  now {m.ram_percent:.1f}%", style="grey50")
        con.print(sp)

        # ── Insights ──────────────────────────────────────────────────────────
        section("Insights")
        if m.ram_percent >= 85:
            insight(f"🔴  RAM at {m.ram_percent:.0f}% — only {hb(m.ram_free)} left.")
            insight("    → Close unused applications or add more RAM.")
        elif m.ram_percent >= 60:
            insight(f"🟡  RAM at {m.ram_percent:.0f}% — {hb(m.ram_free)} free. Monitor under load.")
        else:
            insight(f"🟢  RAM healthy — {hb(m.ram_free)} free of {hb(m.ram_total)}.")

        if m.swap_percent > 30:
            insight(f"🔴  Swap at {m.swap_percent:.0f}%"
                    " — system is paging to disk, performance degraded.")
            insight("    → This means RAM is insufficient for current workload.")
        elif m.swap_percent > 5:
            insight(f"🟡  Swap at {m.swap_percent:.0f}% — minor usage, watch RAM pressure.")
        elif m.swap_total > 0:
            insight("🟢  Swap idle — RAM is sufficient.")

        back_hint()

        if wait_or_back(1.0):
            break