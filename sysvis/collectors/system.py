"""
sysvis/collectors/system.py
----------------------------
Non-blocking threaded system metrics collector.
Runs all psutil calls in a background thread — the menu/views
never block waiting for data.

CPU primed with interval=0.5 once at startup, then sampled
with interval=None (0 ms cost) on every subsequent call.
"""

import os
import sys
import socket
import platform
import subprocess
import time
import threading
import psutil
from dataclasses import dataclass, field

try:
    import cpuinfo
    HAS_CPUINFO = True
except ImportError:
    HAS_CPUINFO = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class CPUMetrics:
    percent_total:    float = 0.0
    percent_per_core: list  = field(default_factory=list)
    freq_current:     float = 0.0
    freq_max:         float = 0.0
    physical_cores:   int   = 0
    logical_cores:    int   = 0
    cpu_name:         str   = ""
    load_avg_1:       float = 0.0
    load_avg_5:       float = 0.0
    load_avg_15:      float = 0.0


@dataclass
class MemoryMetrics:
    ram_total:    int   = 0
    ram_used:     int   = 0
    ram_free:     int   = 0
    ram_percent:  float = 0.0
    swap_total:   int   = 0
    swap_used:    int   = 0
    swap_percent: float = 0.0


@dataclass
class DiskMetrics:
    partitions:  list  = field(default_factory=list)
    read_bytes:  int   = 0
    write_bytes: int   = 0
    read_speed:  float = 0.0
    write_speed: float = 0.0


@dataclass
class NetworkMetrics:
    interfaces:     list  = field(default_factory=list)
    bytes_sent:     int   = 0
    bytes_recv:     int   = 0
    packets_sent:   int   = 0
    packets_recv:   int   = 0
    upload_speed:   float = 0.0
    download_speed: float = 0.0
    hostname:       str   = ""
    local_ip:       str   = ""
    wifi_ssid:      str   = ""
    wifi_ip:        str   = ""
    ethernet_ip:    str   = ""


@dataclass
class GPUMetrics:
    available: bool = False
    gpus:      list = field(default_factory=list)


@dataclass
class ProcessMetrics:
    top_processes:   list = field(default_factory=list)
    total_processes: int  = 0
    running:         int  = 0
    sleeping:        int  = 0


@dataclass
class SystemInfo:
    os_name:              str   = ""
    os_version:           str   = ""
    os_release:           str   = ""
    kernel:               str   = ""
    architecture:         str   = ""
    hostname:             str   = ""
    uptime_seconds:       float = 0.0
    installed_apps_count: int   = 0
    installed_apps:       list  = field(default_factory=list)


# ── Collector ─────────────────────────────────────────────────────────────────

class SystemCollector:
    """
    Continuously collects system metrics in a background thread.

    Usage::

        c = SystemCollector(interval=1.0)
        time.sleep(1.5)          # wait for first sample
        data = c.data            # always returns latest snapshot instantly
        c.stop()

    ``data`` keys: "cpu", "memory", "disk", "network",
                   "gpu", "processes", "system"
    """

    def __init__(self, interval: float = 1.0):
        self.interval    = interval
        self._lock       = threading.Lock()

        # Static values resolved once
        self._cpu_name       = self._get_cpu_name()
        self._physical_cores = psutil.cpu_count(logical=False) or 1
        self._logical_cores  = psutil.cpu_count(logical=True)  or 1
        self._hostname       = socket.gethostname()
        try:
            self._local_ip = socket.gethostbyname(self._hostname)
        except Exception:
            self._local_ip = "127.0.0.1"

        # Prime CPU sampler — must use a real interval once for accurate first read
        psutil.cpu_percent(interval=0.5)
        psutil.cpu_percent(interval=0.5, percpu=True)

        # I/O baselines
        self._prev_disk = psutil.disk_io_counters()
        self._prev_net  = psutil.net_io_counters()
        self._prev_ts   = time.monotonic()

        # EMA-smoothed speeds (alpha=0.35)
        self._ul  = 0.0
        self._dl  = 0.0
        self._rd  = 0.0
        self._wr  = 0.0
        self._EMA = 0.35

        # Caches for slow operations
        self._apps:         list       = []
        self._apps_ts:      float      = 0.0
        self._sys_cache:    SystemInfo = SystemInfo()
        self._sys_cache_ts: float      = 0.0
        self._wifi_ssid:    str        = "N/A"
        self._wifi_ssid_ts: float      = 0.0

        # First blocking snapshot, then hand off to background thread
        self._data: dict = self._collect()

        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def data(self) -> dict:
        """Return the latest snapshot — never blocks."""
        with self._lock:
            return self._data

    def stop(self):
        """Stop the background thread."""
        self._running = False

    # ── Background loop ───────────────────────────────────────────────────────

    def _loop(self):
        while self._running:
            t0       = time.monotonic()
            snapshot = self._collect()
            with self._lock:
                self._data = snapshot
            time.sleep(max(0.0, self.interval - (time.monotonic() - t0)))

    # ── Parallel collection ───────────────────────────────────────────────────

    def _collect(self) -> dict:
        now = time.monotonic()
        dt  = max(now - self._prev_ts, 0.001)
        self._prev_ts = now

        results: dict = {}

        def run(key, fn):
            try:
                results[key] = fn()
            except Exception:
                pass

        threads = [
            threading.Thread(target=run, args=(k, fn), daemon=True)
            for k, fn in [
                ("cpu",       self._collect_cpu),
                ("memory",    self._collect_memory),
                ("disk",      lambda: self._collect_disk(dt)),
                ("network",   lambda: self._collect_network(dt)),
                ("gpu",       self._collect_gpu),
                ("processes", self._collect_processes),
                ("system",    self._collect_system),
            ]
        ]
        for t in threads: t.start()
        for t in threads: t.join(timeout=3.0)

        # Fill any failed keys with empty dataclasses
        defaults = {
            "cpu": CPUMetrics(), "memory": MemoryMetrics(),
            "disk": DiskMetrics(), "network": NetworkMetrics(),
            "gpu": GPUMetrics(), "processes": ProcessMetrics(),
            "system": SystemInfo(),
        }
        for k, v in defaults.items():
            results.setdefault(k, v)
        return results

    # ── Individual collectors ─────────────────────────────────────────────────

    def _collect_cpu(self) -> CPUMetrics:
        m = CPUMetrics()
        m.cpu_name       = self._cpu_name
        m.physical_cores = self._physical_cores
        m.logical_cores  = self._logical_cores
        m.percent_total    = psutil.cpu_percent(interval=0.1)
        m.percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        freq = psutil.cpu_freq()
        if freq:
            m.freq_current = round(freq.current, 1)
            m.freq_max     = round(freq.max, 1)
        try:
            la = os.getloadavg()
            m.load_avg_1, m.load_avg_5, m.load_avg_15 = la
        except (AttributeError, OSError):
            pass  # not available on Windows
        return m

    def _collect_memory(self) -> MemoryMetrics:
        m  = MemoryMetrics()
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        m.ram_total, m.ram_used    = vm.total, vm.used
        m.ram_free,  m.ram_percent = vm.available, vm.percent
        m.swap_total, m.swap_used  = sw.total, sw.used
        m.swap_percent             = sw.percent
        return m

    def _collect_disk(self, dt: float) -> DiskMetrics:
        m = DiskMetrics()
        parts = []
        for p in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(p.mountpoint)
                parts.append({
                    "device": p.device, "mountpoint": p.mountpoint,
                    "fstype": p.fstype,  "total": u.total,
                    "used":   u.used,    "free":  u.free,
                    "percent": u.percent,
                })
            except (PermissionError, OSError):
                continue
        m.partitions = parts
        curr = psutil.disk_io_counters()
        if curr and self._prev_disk:
            self._rd = self._ema(self._rd,
                (curr.read_bytes  - self._prev_disk.read_bytes)  / dt)
            self._wr = self._ema(self._wr,
                (curr.write_bytes - self._prev_disk.write_bytes) / dt)
            m.read_bytes  = curr.read_bytes
            m.write_bytes = curr.write_bytes
        m.read_speed  = self._rd
        m.write_speed = self._wr
        self._prev_disk = curr
        return m

    def _collect_network(self, dt: float) -> NetworkMetrics:
        m = NetworkMetrics()
        m.hostname = self._hostname
        m.local_ip = self._local_ip
        curr = psutil.net_io_counters()
        self._ul = self._ema(self._ul,
            (curr.bytes_sent - self._prev_net.bytes_sent) / dt)
        self._dl = self._ema(self._dl,
            (curr.bytes_recv - self._prev_net.bytes_recv) / dt)
        m.upload_speed   = self._ul
        m.download_speed = self._dl
        m.bytes_sent     = curr.bytes_sent
        m.bytes_recv     = curr.bytes_recv
        m.packets_sent   = curr.packets_sent
        m.packets_recv   = curr.packets_recv
        self._prev_net   = curr

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        ifaces = []
        for name, addr_list in addrs.items():
            info = {"name": name, "ipv4": "", "ipv6": "",
                    "mac": "", "is_up": False, "speed": 0}
            for a in addr_list:
                if   a.family == socket.AF_INET:  info["ipv4"] = a.address
                elif a.family == socket.AF_INET6: info["ipv6"] = a.address.split("%")[0]
                elif a.family == psutil.AF_LINK:  info["mac"]  = a.address
            if name in stats:
                info["is_up"] = stats[name].isup
                info["speed"] = stats[name].speed
            ifaces.append(info)
            lo = name.lower()
            if any(k in lo for k in ("eth","en0","en1","enp","ethernet")):
                m.ethernet_ip = info["ipv4"]
            if any(k in lo for k in ("wlan","wi-fi","wifi","wlp","wlo")):
                m.wifi_ip = info["ipv4"]
        m.interfaces = ifaces

        now = time.monotonic()
        if now - self._wifi_ssid_ts > 15:
            self._wifi_ssid    = self._get_wifi_ssid()
            self._wifi_ssid_ts = now
        m.wifi_ssid = self._wifi_ssid
        return m

    def _collect_gpu(self) -> GPUMetrics:
        m = GPUMetrics()
        if not HAS_GPUTIL:
            return m
        try:
            gpus = GPUtil.getGPUs()
            m.available = bool(gpus)
            m.gpus = [{
                "id": g.id, "name": g.name,
                "load": g.load * 100,
                "mem_used": g.memoryUsed, "mem_total": g.memoryTotal,
                "mem_percent": (g.memoryUsed / g.memoryTotal * 100)
                               if g.memoryTotal else 0,
                "temperature": g.temperature,
            } for g in gpus]
        except Exception:
            pass
        return m

    def _collect_processes(self, top_n: int = 15) -> ProcessMetrics:
        m = ProcessMetrics()
        procs, running, sleeping = [], 0, 0
        for p in psutil.process_iter(
                ["pid","name","cpu_percent","memory_percent","status","username"]):
            try:
                info = p.info
                procs.append(info)
                s = info.get("status", "")
                if   s == "running":            running  += 1
                elif s in ("sleeping", "idle"): sleeping += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        m.total_processes = len(procs)
        m.running         = running
        m.sleeping        = sleeping
        procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
        m.top_processes = procs[:top_n]
        return m

    def _collect_system(self) -> SystemInfo:
        now = time.monotonic()
        if now - self._sys_cache_ts > 60:
            s               = SystemInfo()
            s.os_name       = platform.system()
            s.os_version    = platform.version()
            s.os_release    = platform.release()
            s.kernel        = platform.uname().version[:80]
            s.architecture  = platform.machine()
            s.hostname      = self._hostname
            if now - self._apps_ts > 60:
                self._apps    = self._get_installed_apps()
                self._apps_ts = now
            s.installed_apps       = self._apps
            s.installed_apps_count = len(self._apps)
            self._sys_cache        = s
            self._sys_cache_ts     = now
        self._sys_cache.uptime_seconds = time.time() - psutil.boot_time()
        return self._sys_cache

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _ema(self, prev: float, new: float) -> float:
        return self._EMA * new + (1 - self._EMA) * prev

    def _get_cpu_name(self) -> str:
        if HAS_CPUINFO:
            try:
                return cpuinfo.get_cpu_info().get("brand_raw", "") \
                       or platform.processor()
            except Exception:
                pass
        return platform.processor()

    def _get_wifi_ssid(self) -> str:
        try:
            if sys.platform == "win32":
                out = subprocess.check_output(
                    ["netsh","wlan","show","interfaces"],
                    stderr=subprocess.DEVNULL, timeout=3
                ).decode(errors="ignore")
                for line in out.splitlines():
                    if "SSID" in line and "BSSID" not in line:
                        return line.split(":",1)[-1].strip()
            elif sys.platform == "darwin":
                out = subprocess.check_output(
                    ["/System/Library/PrivateFrameworks/Apple80211.framework"
                     "/Versions/Current/Resources/airport","-I"],
                    stderr=subprocess.DEVNULL, timeout=3
                ).decode(errors="ignore")
                for line in out.splitlines():
                    if " SSID:" in line:
                        return line.split(":",1)[-1].strip()
            else:
                for cmd in [["iwgetid","-r"],
                             ["nmcli","-t","-f","active,ssid","dev","wifi"]]:
                    try:
                        out = subprocess.check_output(
                            cmd, stderr=subprocess.DEVNULL, timeout=3
                        ).decode(errors="ignore").strip()
                        if out:
                            return out.split("yes:")[-1].strip() \
                                   if "yes:" in out else out.splitlines()[0]
                    except FileNotFoundError:
                        continue
        except Exception:
            pass
        return "N/A"

    def _get_installed_apps(self) -> list:
        apps = []
        try:
            if sys.platform == "win32":
                import winreg
                keys = [
                    (winreg.HKEY_LOCAL_MACHINE,
                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE,
                     r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER,
                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                ]
                for hive, sub in keys:
                    try:
                        key = winreg.OpenKey(hive, sub)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                sk   = winreg.OpenKey(key, winreg.EnumKey(key, i))
                                name = winreg.QueryValueEx(sk,"DisplayName")[0]
                                ver  = ""
                                try: ver = winreg.QueryValueEx(sk,"DisplayVersion")[0]
                                except Exception: pass
                                if name: apps.append({"name": name, "version": ver})
                            except Exception: continue
                    except Exception: continue
            elif sys.platform == "darwin":
                out = subprocess.check_output(
                    ["ls","/Applications"],
                    stderr=subprocess.DEVNULL, timeout=5
                ).decode(errors="ignore")
                for line in out.strip().splitlines():
                    if line.endswith(".app"):
                        apps.append({"name": line[:-4], "version": ""})
            else:
                for cmd, parser in [
                    (["dpkg","--get-selections"],
                     lambda l: l.split()[0] if "install" in l else None),
                    (["rpm","-qa","--queryformat","%{NAME} %{VERSION}\n"],
                     lambda l: l.split()[0] if l.strip() else None),
                    (["pacman","-Q"],
                     lambda l: l.split()[0] if l.strip() else None),
                ]:
                    try:
                        out = subprocess.check_output(
                            cmd, stderr=subprocess.DEVNULL, timeout=10
                        ).decode(errors="ignore")
                        for line in out.strip().splitlines():
                            name = parser(line)
                            if name: apps.append({"name": name, "version": ""})
                        break
                    except (FileNotFoundError,
                            subprocess.CalledProcessError,
                            subprocess.TimeoutExpired):
                        continue
        except Exception:
            pass
        return apps