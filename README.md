# Windows Toolkit — Unified Debloat & Troubleshooting Suite

One repository. Two tools. Everything you need to clean up, optimize, and diagnose Windows.

- **GUI Mode (VampKit)** — Cyberpunk-styled WPF interface for debloating, privacy tweaks, gaming optimization, and system maintenance. Every change is reversible.
- **CLI Mode (Hardware Diagnostics)** — Python command-line suite for deep hardware troubleshooting: keyboard, mouse, storage, RAM, audio, network, display, battery, drivers, and more.

---

## Quick Start

**Double-click `Launch_Toolkit.bat`** to choose your mode:

```
[1] GUI Mode      - Debloat, Optimization & Maintenance
[2] CLI Mode      - Full Hardware Diagnostics
```

Or launch directly:
- `Launch_VampKit.bat` — GUI mode (auto-elevates to Administrator)
- `launch.bat` — CLI mode

---

## GUI Mode — Debloat & Optimization (VampKit)

Run `Launch_VampKit.bat` as Administrator. On first launch it compiles `VampKit.ps1` from the included source files in `src/` and `ui/` — no internet required.

| Tab | What it does |
|-----|--------------|
| **Auto-Optimize** | Safe high-impact defaults for any fresh install |
| **System Core** | Explorer tweaks, Start Menu cleanup, Fast Startup, visual effects |
| **Gaming & GPU** | HAGS, Game Bar/DVR, MPO, Nagle, VRR, Ultimate Performance plan |
| **Handheld** | Hot-Bag fix, BitLocker/encryption, Core Isolation, EPP power slicing |
| **Privacy Shield** | Telemetry, Copilot, Recall AI, ads, Cortana, location, OneDrive |
| **Advanced** | WSL, Hyper-V, NTFS/NIC overhead, foreground priority |
| **Maintenance** | SFC/DISM, WU reset, GPU cache, SSD trim, temp cleanup, driver audit |

**Safety:** Registry snapshot before every change. System Restore checkpoint before batch ops. BitLocker decryption banner. Expert Mode gate on risky tweaks. Hardware-aware GPU detection.

---

## CLI Mode — Hardware Diagnostics Toolkit

Requires Python 3.7+. Run `launch.bat` or `python kb_toolkit.py`.

**Input Devices**
- `kb_checker` — Keyboard drivers, connectivity, power management
- `kb_monitor` — Real-time key press monitoring, stuck-key detection
- `kb_remapper` — Scancode remapping, key disabling, stuck-key repair
- `mouse_checker` — PTP detection, drivers, connectivity, battery
- `mouse_monitor` — Cursor tracking, velocity, jitter detection
- `mouse_remapper` — Pointer speed, gestures, palm rejection

**Hardware**
- `storage_checker` — SMART disk health (requires smartmontools)
- `ram_checker` — Memory modules, capacity, speed, load
- `audio_checker` — Speakers, headphones, mics, audio services
- `hardware_checker` — WiFi, Bluetooth, thermals, ports, NFC, webcam
- `display_checker` — GPUs, monitors, resolution, TDR crash history
- `battery_checker` — Charge level + wear percentage via powercfg

**Diagnostics**
- `network_checker` — Adapters, gateway ping, DNS, traceroute
- `startup_checker` — Startup programs, logon tasks, boot time
- `eventlog_checker` — Decodes recent Critical/Error events in plain language
- `system_health_checker` — SFC/DISM, Windows Update, pending reboot
- `driver_checker` — Flags stale drivers by install date
- `report_generator` — Runs all checkers, exports HTML + text report

**Repair & Cleanup**
- `repair_toolkit` — Winsock reset, spooler reset, WU component reset, Explorer restart
- `optimizer` — Temp/cache/Recycle Bin cleanup, DNS flush

**Tweaks & Debloat** *(82 reversible tweaks — Apply / Revert / Check per tweak)*
- `debloat_privacy` — Telemetry, Copilot, Recall, ads, Cortana, OneDrive (25 tweaks)
- `gaming_tweaks` — HAGS, Game Bar, MPO, Nagle, Ultimate Perf, VRR, Game Mode (17 tweaks)
- `system_tweaks` — Classic menu, visual FX, dark theme, Fast Startup, Explorer (26 tweaks)
- `handheld_tweaks` — Hibernate, power button, USB suspend, Compact OS (10 tweaks)
- `advanced_tweaks` — Foreground priority, NTFS last-access, NIC power saving (4 tweaks)
- `reclaim_space` — Windows.old cleanup, WinSxS compaction

---

## Requirements

| Mode | Requirement |
|------|-------------|
| GUI | Windows 11 (24H2+), PowerShell 5.1+, Administrator |
| CLI | Windows 10/11, Python 3.7+ |
| CLI SMART | [smartmontools](https://www.smartmontools.org/) for full disk health |

---

## Structure

```
Windows-Debloat-Toolkit/
├── Launch_Toolkit.bat        ← Master launcher
├── Launch_VampKit.bat        ← GUI direct launcher
├── launch.bat                ← CLI direct launcher
├── BuildVampKit.ps1          ← Compiles VampKit.ps1 from src/ + ui/
├── kb_toolkit.py             ← CLI entry point
├── modules/                  ← 29 Python diagnostic/tweak modules
├── src/
│   ├── VampKit.ps1           ← GUI controller
│   ├── VampKitCore.ps1       ← Engine, registry helpers, job dispatcher
│   ├── VampKitDB.ps1         ← Tweak database (Apply/Revert/Check)
│   └── VampKitSnapshotTool.ps1 ← Registry snapshot recovery
└── ui/
    └── VampKit.xaml          ← WPF UI
```

---

## Disclaimer

MIT licensed. System-level changes carry some risk — keep backups. Every tweak uses documented registry and Group Policy values and can be individually reversed.
