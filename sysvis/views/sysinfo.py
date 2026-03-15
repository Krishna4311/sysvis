"""
sysvis/views/sysinfo.py
-----------------------
System information view. OS, kernel, uptime,
architecture and installed applications list.
Single render — press any key to go back.
"""

from ._helpers import (
    con, uptime_str, trunc,
    section, row, back_hint,
    getch,clear,
)


def sysinfo(collector):
    """System info view — static, press any key to return."""
    data = collector.data
    s    = data["system"]

    clear()
    con.print()
    con.print("  [bold bright_cyan]SYSTEM INFO[/]")
    con.print()

    # ── OS info ───────────────────────────────────────────────────────────────
    row("Operating System", f"{s.os_name} {s.os_release}")
    row("OS Version",       trunc(s.os_version, 60))
    row("Kernel",           trunc(s.kernel, 60))
    row("Architecture",     s.architecture)
    row("Hostname",         s.hostname)
    row("Uptime",           uptime_str(s.uptime_seconds))
    row("Installed Apps",   str(s.installed_apps_count),
        value_style="bold bright_cyan")

    # ── Apps list ─────────────────────────────────────────────────────────────
    section(f"Installed Applications  (showing 30 of {s.installed_apps_count})")

    con.print(
        f"  [bold cyan]{'#':>3}  {'Name':<50}  Version[/]"
    )
    con.print("  [grey23]" + "─" * 70 + "[/]")

    for i, app in enumerate(s.installed_apps[:30], 1):
        ver = trunc(app.get("version") or "—", 20)
        nm  = trunc(app["name"], 50)
        con.print(
            f"  [grey35]{i:>3}[/]  [white]{nm:<50}[/]  [grey50]{ver}[/]"
        )

    rem = s.installed_apps_count - 30
    if rem > 0:
        con.print(f"\n  [grey50]… and {rem} more installed.[/]")

    con.print()
    con.print("  [grey35]Press any key to go back[/]")
    getch()