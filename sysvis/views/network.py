"""
sysvis/views/network.py
-----------------------
Network insight view. Upload/download speeds, all interfaces,
IP addresses, WiFi SSID, traffic history.
"""

from rich.text import Text
from ._helpers import (
    con, hb,
    spark, section, row, insight, back_hint,
    wait_or_back,clear,
)


def network(collector):
    """Live network view."""
    hist_ul, hist_dl = [], []
    max_ul,  max_dl  = 1.0, 1.0

    while True:
        data   = collector.data
        n      = data["network"]
        max_ul = max(max_ul, n.upload_speed, 1)
        max_dl = max(max_dl, n.download_speed, 1)
        hist_ul.append(n.upload_speed   / max_ul * 100)
        hist_dl.append(n.download_speed / max_dl * 100)
        hist_ul = hist_ul[-60:]
        hist_dl = hist_dl[-60:]

        clear()
        con.print()
        con.print("  [bold bright_cyan]NETWORK[/]")
        con.print()

        # ── Live speeds ───────────────────────────────────────────────────────
        row("↑ Upload",   hb(n.upload_speed,   "B/s"), value_style="bold bright_yellow")
        row("↓ Download", hb(n.download_speed, "B/s"), value_style="bold bright_green")
        row("Sent total", hb(n.bytes_sent))
        row("Recv total", hb(n.bytes_recv))
        row("Packets ↑",  f"{n.packets_sent:,}")
        row("Packets ↓",  f"{n.packets_recv:,}")

        # ── Addresses ─────────────────────────────────────────────────────────
        section("Addresses")
        row("Hostname",    n.hostname)
        row("Local IP",    n.local_ip,          value_style="bright_cyan")
        row("Ethernet IP", n.ethernet_ip or "—")
        row("WiFi IP",     n.wifi_ip     or "—")
        row("WiFi SSID",   n.wifi_ssid   or "—")

        # ── Interfaces ────────────────────────────────────────────────────────
        section("Interfaces")
        for iface in n.interfaces[:10]:
            status = "[bright_green]UP[/]" if iface["is_up"] else "[bright_red]DOWN[/]"
            speed  = f"  {iface['speed']}Mb/s" if iface["speed"] else ""
            ipv4   = iface["ipv4"] or "—"
            con.print(
                f"  [cyan]{iface['name']:<24}[/]"
                f"  {status}"
                f"  [white]{ipv4:<16}[/]"
                f"  [grey50]{iface['mac'] or ''}[/]"
                f"[grey35]{speed}[/]"
            )

        # ── History ───────────────────────────────────────────────────────────
        section("Traffic History  (last 60s)")
        ul_line = Text(no_wrap=True)
        ul_line.append("  ↑ Upload    ", style="grey50")
        ul_line.append_text(spark(hist_ul, 50))
        con.print(ul_line)

        dl_line = Text(no_wrap=True)
        dl_line.append("  ↓ Download  ", style="grey50")
        dl_line.append_text(spark(hist_dl, 50))
        con.print(dl_line)

        # ── Insights ──────────────────────────────────────────────────────────
        section("Insights")
        tips = []
        if n.download_speed > 80 * 1024 * 1024:
            tips.append(f"⚡  High download: {hb(n.download_speed,'B/s')} — large transfer in progress.")
        if n.upload_speed > 20 * 1024 * 1024:
            tips.append(f"⚡  High upload: {hb(n.upload_speed,'B/s')} — check for backup or sync jobs.")
        down_ifaces = [i for i in n.interfaces
                       if not i["is_up"]
                       and i["name"].lower() not in ("lo", "loopback")]
        if down_ifaces:
            names = ", ".join(i["name"] for i in down_ifaces[:3])
            tips.append(f"⚠   Interface(s) DOWN: {names}")
        if not tips:
            tips.append("🟢  Network healthy — no issues detected.")
        for t in tips:
            insight(t)

        back_hint()

        if wait_or_back(1.0):
            break