# SYSVIS

> Arrow-key interactive terminal system monitor with real-time insights.

```
  SYSVIS  System Monitor    OS  Windows 11    HOST  Vasu-Krishna    ⏱  00h 48m

   ❯  1. CPU            Cores, frequency, per-core usage, load average
      2. Memory         RAM & swap usage with pressure insights
      3. Disk           Partitions, free space, I/O throughput
      4. Network        Speed, interfaces, IP addresses, WiFi SSID
      5. Processes      Top CPU & memory consumers
      6. GPU            Utilisation, VRAM, temperature
      7. System Info    OS, kernel, uptime, installed applications
      8. Live Monitor   All key metrics updating in real time
      9. Health Report  A-F score per category with recommendations

  ↑ ↓ arrow keys to move,  Enter to open,  q to quit
```

---

## Install

```bash
pip install sysvis

# Optional: NVIDIA GPU support
pip install sysvis[gpu]
```

## Run

```bash
# Arrow-key menu (default)
sysvis

# Or as a module
python -m sysvis
```

## Navigate

| Key | Action |
|---|---|
| `↑` `↓` | Move selection |
| `Enter` | Open view |
| `q` / `Esc` | Go back / quit |

---

## Use as a library

```python
# Launch the interactive menu
import sysvis
sysvis.run()
```

```python
# Collect data silently in your own script
from sysvis import SystemCollector
import time

c = SystemCollector(interval=1.0)
time.sleep(1.5)  # wait for first sample

data = c.data
print(f"CPU:  {data['cpu'].percent_total:.1f}%")
print(f"RAM:  {data['memory'].ram_percent:.1f}%")
print(f"Host: {data['network'].hostname}")

c.stop()
```

```python
# Open a specific view directly
from sysvis import SystemCollector
from sysvis.views import cpu, memory, health
import time

c = SystemCollector()
time.sleep(1.5)

cpu(c)       # live CPU view — blocks until q
memory(c)    # live memory view
health(c)    # health report
c.stop()
```

```python
# Use dataclasses with type hints
from sysvis import SystemCollector, CPUMetrics, MemoryMetrics
import time

c = SystemCollector()
time.sleep(1.5)

cpu: CPUMetrics    = c.data["cpu"]
mem: MemoryMetrics = c.data["memory"]

print(cpu.cpu_name)
print(cpu.logical_cores)
print(mem.ram_total)
c.stop()
```

---

## Available views

| Function | Description |
|---|---|
| `cpu(collector)` | Live CPU — cores, frequency, per-core bars, sparkline |
| `memory(collector)` | Live RAM + swap bars and insights |
| `disk(collector)` | Partition table, I/O speed |
| `network(collector)` | Speeds, IPs, interfaces, sparklines |
| `processes(collector)` | Top processes by CPU |
| `gpu(collector)` | GPU util, VRAM, temperature (requires gputil) |
| `sysinfo(collector)` | OS info + installed apps list |
| `live(collector)` | Compact overview of all metrics |
| `health(collector)` | A–F score per category + recommendations |

---

## Data collected

```python
data = collector.data

data["cpu"].percent_total       # overall CPU %
data["cpu"].percent_per_core    # list of per-core %
data["cpu"].cpu_name            # CPU model name
data["cpu"].logical_cores       # number of logical cores
data["cpu"].freq_current        # current frequency MHz

data["memory"].ram_percent      # RAM usage %
data["memory"].ram_free         # free RAM in bytes
data["memory"].ram_total        # total RAM in bytes
data["memory"].swap_percent     # swap usage %

data["disk"].partitions         # list of dicts (mountpoint, used, free, total, percent)
data["disk"].read_speed         # bytes/sec
data["disk"].write_speed        # bytes/sec

data["network"].upload_speed    # bytes/sec
data["network"].download_speed  # bytes/sec
data["network"].local_ip        # local IP address
data["network"].hostname        # machine hostname
data["network"].wifi_ssid       # connected WiFi name
data["network"].ethernet_ip     # ethernet IP
data["network"].wifi_ip         # WiFi IP
data["network"].interfaces      # list of all interfaces

data["gpu"].available           # True if GPU detected
data["gpu"].gpus                # list of GPU dicts (load, mem, temp)

data["processes"].top_processes # list of top processes by CPU
data["processes"].total_processes
data["processes"].running
data["processes"].sleeping

data["system"].os_name          # e.g. Windows
data["system"].os_release       # e.g. 11
data["system"].hostname
data["system"].uptime_seconds
data["system"].installed_apps   # list of installed apps
data["system"].installed_apps_count
```

---

## Project structure

```
sysvis_lib/
├── sysvis/
│   ├── __init__.py          ← public API: SystemCollector, run()
│   ├── __main__.py          ← python -m sysvis
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── system.py        ← threaded non-blocking psutil collectors
│   └── views/
│       ├── __init__.py      ← exports all 9 view functions
│       ├── _helpers.py      ← bar, spark, hb, getch, clear …
│       ├── menu.py          ← arrow-key interactive menu
│       ├── cpu.py
│       ├── memory.py
│       ├── disk.py
│       ├── network.py
│       ├── processes.py
│       ├── gpu.py
│       ├── sysinfo.py
│       ├── live.py
│       └── health.py
├── pyproject.toml
├── setup.py
└── README.md
```

---

## Requirements

- Python 3.8+
- `rich >= 13`
- `psutil >= 5.9`
- `py-cpuinfo >= 9` — better CPU name detection
- `gputil` *(optional)* — NVIDIA GPU panel

---

## License

MIT
