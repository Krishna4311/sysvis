"""
sysvis/views/cpu.py
-------------------
CPU insight view. Shows usage, per-core breakdown,
frequency, load averages, history and recommendations.
Updates every second. Press q/Esc to go back.
"""

from rich.text import Text
from ._helpers import (
    con, clear, pcolor, hb,
    bar, bar_row, spark, section, row, insight, back_hint,
    wait_or_back,
)


def cpu(collector):
    """Live CPU view — press q/Esc to go back."""
    hist = []

    while True:
        data    = collector.data
        c       = data["cpu"]
        logical = c.logical_cores or 1

        # Windows reports cpu_percent as sum across all cores (can exceed 100)
        # divide back to get a true 0-100 reading
        raw = c.percent_total
        total = min(raw / logical, 100.0) if raw > 100 else raw

        hist.append(total)
        hist = hist[-60:]

        clear()

        # ── Header ────────────────────────────────────────────────────────────
        con.print()
        con.print(
            f"  [bold bright_cyan]CPU[/]  "
            f"[grey50]{c.cpu_name or 'Unknown'}[/]"
        )
        con.print()

        # ── Overall usage ─────────────────────────────────────────────────────
        bar_row(
            "Overall Usage", total,
            extra=f"({c.physical_cores}P / {c.logical_cores}L cores)",
        )

        con.print()
        row("Frequency",
            f"{c.freq_current:.0f} MHz  (max {c.freq_max:.0f} MHz)")
        row("Load avg",
            f"1m {c.load_avg_1:.2f}   "
            f"5m {c.load_avg_5:.2f}   "
            f"15m {c.load_avg_15:.2f}")

        # ── Per-core breakdown ────────────────────────────────────────────────
        if c.percent_per_core:
            section("Per-Core Usage")
            for i, pct in enumerate(c.percent_per_core):
                # normalise per-core too
                pct = min(pct / logical, 100.0) if pct > 100 else pct
                bar_row(f"Core {i}", pct)

        # ── History ───────────────────────────────────────────────────────────
        section("History  (last 60s)")
        sp = Text(no_wrap=True)
        sp.append("  ")
        sp.append_text(spark(hist, 55))
        sp.append(f"  now {total:.1f}%", style="grey50")
        con.print(sp)

        # ── Insights ──────────────────────────────────────────────────────────
        section("Insights")
        if total >= 85:
            insight(f"🔴  CPU at {total:.0f}% — critically loaded.")
            insight("    → Open Processes view to find the culprit.")
        elif total >= 60:
            insight(f"🟡  CPU at {total:.0f}% — elevated but manageable.")
        else:
            insight(f"🟢  CPU healthy at {total:.0f}% — no action needed.")

        if c.load_avg_1 > 0 and c.load_avg_1 > c.logical_cores:
            insight(
                f"⚠   Load avg ({c.load_avg_1:.1f}) exceeds "
                f"core count ({c.logical_cores}) — tasks queuing up."
            )

        per_core_norm = [
            min(p / logical, 100.0) if p > 100 else p
            for p in c.percent_per_core
        ]
        hottest = max(per_core_norm, default=0)
        if hottest > 90:
            idx = per_core_norm.index(hottest)
            insight(
                f"⚡  Core {idx} at {hottest:.0f}% "
                "— single-threaded bottleneck detected."
            )

        back_hint()

        if wait_or_back(1.0):
            break