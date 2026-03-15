"""
sysvis — Arrow-key terminal system monitor with actionable insights.

Quick start
-----------
    import sysvis
    sysvis.run()                    # launches arrow-key menu

    # Use the collector directly:
    from sysvis import SystemCollector
    import time
    c = SystemCollector()
    time.sleep(1.5)
    print(c.data["cpu"].percent_total)
    c.stop()
"""

from .collectors.system import (
    SystemCollector,
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    GPUMetrics,
    ProcessMetrics,
    SystemInfo,
)

__version__ = "1.1.0"
__author__  = "sysvis contributors"

__all__ = [
    "SystemCollector",
    "CPUMetrics",
    "MemoryMetrics",
    "DiskMetrics",
    "NetworkMetrics",
    "GPUMetrics",
    "ProcessMetrics",
    "SystemInfo",
    "run",
]


def run():
    """Launch the arrow-key interactive menu."""
    from .views.menu import run as _run
    _run()