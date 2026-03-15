# SYSVIS

> Arrow-key interactive terminal system monitor with real-time insights.

```
  SYSVIS  System Monitor    OS  Windows 11    HOST  Vasu-Krishna    ⏱  00h 48m

   ❯  1. CPU            Cores, frequency, load average, per-core usage
      2. Memory         RAM & swap usage, pressure insights
      3. Disk           Partitions, free space, I/O throughput
      4. Network        Interfaces, speeds, IP & WiFi addresses
      5. Processes      Top CPU & memory consumers
      6. GPU            Utilisation, VRAM, temperature
      7. System Info    OS, kernel, uptime, installed applications
      8. Live Monitor   Real-time overview of all metrics
      9. Health Report  A-F grade per category + actionable recommendations

  ↑ ↓ arrow keys to move,  Enter to open,  q to quit
```

---

## Install

```bash
pip install -e .

# Optional: NVIDIA GPU support
pip install -e ".[gpu]"

# Development (includes pytest)
pip install -e ".[dev]"
```

## Run

```bash
sysvis                        # arrow-key menu (default)
sysvis --mode dashboard       # live all-panels dashboard
sysvis --mode dashboard -r 2  # dashboard, refresh every 2s
python -m sysvis              # same as sysvis
```

## Navigation

| Key | Action |
|---|---|
| `↑` `↓` | Move selection |
| `Enter` | Open view |
| `Esc` / `q` | Back to menu / quit |

## Use as a library

```python
# Launch the UI
import sysvis
sysvis.run()

# Collect data in your own script
from sysvis import SystemCollector
import time

c = SystemCollector(interval=1.0)
time.sleep(1.5)

data = c.data
print(f"CPU:  {data['cpu'].percent_total:.1f}%")
print(f"RAM:  {data['memory'].ram_percent:.1f}%")
print(f"Host: {data['network'].hostname}")
c.stop()

# Show a single view
from sysvis.views import health_report
health_report(c)
```

## Project structure

```
sysvis_lib/
├── sysvis/
│   ├── __init__.py          ← public API
│   ├── __main__.py          ← python -m sysvis
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── system.py        ← all psutil collectors (threaded)
│   ├── views/               ← one function per screen (public)
│   │   ├── __init__.py
│   │   ├── cpu.py  memory.py  disk.py  network.py
│   │   ├── processes.py  gpu.py  sysinfo.py
│   │   ├── live.py  health.py
│   └── ui/                  ← rendering internals
│       ├── _helpers.py      ← bar, spark, getch, hb …
│       ├── menu.py          ← arrow-key menu + view logic
│       └── dashboard.py     ← live dashboard
├── tests/
│   ├── test_collectors.py
│   └── test_views.py
├── examples/
│   ├── basic_usage.py
│   └── custom_view.py
├── docs/API.md
├── pyproject.toml
├── setup.py
└── README.md
```

## Requirements

- Python 3.8+
- `rich >= 13`
- `psutil >= 5.9`
- `py-cpuinfo >= 9` (optional — better CPU name detection)
- `gputil` (optional — NVIDIA GPU panel)

## Run tests

```bash
pytest tests/ -v
```