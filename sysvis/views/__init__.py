"""
sysvis.views — individual insight views (public API).

Each function takes a SystemCollector and runs until q/Esc.

Example::

    from sysvis import SystemCollector
    from sysvis.views import cpu, health
    import time

    c = SystemCollector()
    time.sleep(1.5)
    cpu(c)       # live CPU view
    health(c)    # health report
    c.stop()
"""

from .cpu       import cpu
from .memory    import memory
from .disk      import disk
from .network   import network
from .processes import processes
from .gpu       import gpu
from .sysinfo   import sysinfo
from .live      import live
from .health    import health

__all__ = [
    "cpu", "memory", "disk", "network",
    "processes", "gpu", "sysinfo", "live", "health",
]