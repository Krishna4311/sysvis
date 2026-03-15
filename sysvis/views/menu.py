"""
sysvis/views/menu.py
--------------------
Arrow-key interactive menu.
↑↓ navigate   Enter select   q/Esc quit
"""

import time
from rich.console import Console

from ..collectors.system import SystemCollector
from ._helpers import getch, uptime_str, trunc, clear

from .cpu       import cpu
from .memory    import memory
from .disk      import disk
from .network   import network
from .processes import processes
from .gpu       import gpu
from .sysinfo   import sysinfo
from .live      import live
from .health    import health

con = Console()

MENU_ITEMS = [
    ("CPU",           "Cores, frequency, per-core usage, load average"),
    ("Memory",        "RAM & swap usage with pressure insights"),
    ("Disk",          "Partitions, free space, I/O throughput"),
    ("Network",       "Speed, interfaces, IP addresses, WiFi SSID"),
    ("Processes",     "Top CPU & memory consumers"),
    ("GPU",           "Utilisation, VRAM, temperature"),
    ("System Info",   "OS, kernel, uptime, installed applications"),
    ("Live Monitor",  "All key metrics updating in real time"),
    ("Health Report", "A-F score per category with recommendations"),
]

VIEW_FNS = [cpu, memory, disk, network, processes, gpu, sysinfo, live, health]


def _draw(selected: int, data: dict):
    clear()
    s = data["system"]
    n = data["network"]

    con.print()
    con.print(
        f"  [bold white on dark_cyan] SYSVIS [/]  "
        f"[grey50]{s.os_name} {s.os_release}  |  "
        f"{trunc(s.hostname, 20)}  |  "
        f"{uptime_str(s.uptime_seconds)}  |  "
        f"{n.local_ip}[/]"
    )
    con.print()

    for i, (label, desc) in enumerate(MENU_ITEMS):
        if i == selected:
            con.print(
                f"  [bold bright_cyan]❯  {i+1:2}.  {label:<18}[/]"
                f"  [bright_cyan]{desc}[/]"
            )
        else:
            con.print(
                f"  [grey35]   {i+1:2}.  [/][white]{label:<18}[/]"
                f"  [grey50]{desc}[/]"
            )

    con.print()
    con.print("  [grey35]↑ ↓  navigate    Enter  open    q  quit[/]")


def run():
    """Start the interactive menu."""
    collector = SystemCollector(interval=1.0)
    time.sleep(1.2)  # let first sample land

    selected = 0
    while True:
        _draw(selected, collector.data)
        key = getch()

        if key == "UP":
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == "DOWN":
            selected = (selected + 1) % len(MENU_ITEMS)
        elif key == "ENTER":
            try:
                VIEW_FNS[selected](collector)
            except KeyboardInterrupt:
                pass
        elif key in ("q", "ESC"):
            break

    collector.stop()
    clear()
    con.print("\n  [bold bright_cyan]SYSVIS[/]  [grey50]bye.[/]\n")