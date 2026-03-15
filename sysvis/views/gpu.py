"""
sysvis/views/gpu.py
-------------------
GPU insight view. Utilisation, VRAM, temperature.
Requires:  pip install gputil
"""

from ._helpers import (
    con, pcolor, hb,
    bar, bar_row, section, row, insight, back_hint,
    wait_or_back,clear,
)


def gpu(collector):
    """Live GPU view."""
    while True:
        data = collector.data
        g    = data["gpu"]

        clear()
        con.print()
        con.print("  [bold bright_cyan]GPU[/]")
        con.print()

        if not g.available:
            con.print("  [grey50]No GPU detected.[/]")
            con.print()
            con.print("  [grey35]Install NVIDIA support:  "
                      "[bright_cyan]pip install gputil[/][/]")
        else:
            for gi in g.gpus:
                tmp = gi["temperature"]
                con.print(
                    f"  [bold bright_cyan]GPU {gi['id']}[/]"
                    f"  [white]{gi['name']}[/]"
                )
                con.print()
                bar_row("Utilisation", gi["load"])
                bar_row("VRAM",        gi["mem_percent"],
                        extra=f"{hb(gi['mem_used']*1024**2)}"
                              f" / {hb(gi['mem_total']*1024**2)}")

                temp_style = ("bright_red"    if tmp > 85
                              else "bright_yellow" if tmp > 70
                              else "bright_green")
                row("Temperature", f"{tmp}°C", value_style=f"bold {temp_style}")

                section("Insights")
                if tmp > 85:
                    insight("🔴  GPU critically hot — check fan and cooling.")
                    insight("    → Reduce workload or improve airflow.")
                elif tmp > 70:
                    insight("🟡  GPU running warm — normal under heavy load.")
                else:
                    insight("🟢  GPU temperature healthy.")

                if gi["mem_percent"] > 90:
                    insight("🔴  VRAM nearly full — reduce GPU workload or lower resolution.")
                elif gi["mem_percent"] > 70:
                    insight("🟡  VRAM moderately used — monitor during heavy tasks.")
                else:
                    insight("🟢  VRAM usage healthy.")

        back_hint()

        if wait_or_back(1.0):
            break