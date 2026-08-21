# Windows Toolkit — Unified Debloat & Troubleshooting Suite

A combined toolkit that brings two tools into one repository:

- **GUI Mode (Project Ronin)** — A cyberpunk-styled WPF interface for debloating, privacy tweaks, gaming optimization, and system maintenance. Every change is reversible via registry snapshots.
- **CLI Mode (Hardware Diagnostics)** — A Python-based command-line suite for deep hardware troubleshooting: keyboard, mouse, storage, RAM, audio, network, display, battery, drivers, and more.

---

## Quick Start

**Double-click `Launch_Toolkit.bat`** — it asks which mode you want:

```
[1] GUI Mode      - Debloat, Optimization & Maintenance (Project Ronin)
[2] CLI Mode      - Full Hardware Diagnostics (Python toolkit)
```

Or use the dedicated launchers:
- `Launch_Ronin.bat` — opens the GUI directly (auto-elevates to admin)
- `launch.bat` — opens the CLI diagnostic toolkit directly

---

## GUI Mode — Project Ronin (Debloat & Optimization)

A graphical Windows 11 optimization suite. Run `Launch_Ronin.bat` as Administrator.

> **First run:** The launcher auto-downloads the Ronin source files from GitHub and builds
> the self-contained `Ronin.ps1` monolith. You can also run manually:
> - `Get-RoninSource.ps1` — downloads src/ and ui/ from Project Ronin
> - `BuildRonin.ps1` — compiles the standalone monolith from those files

### Modules

| Tab | Purpose |
|-----|---------|
| **Auto-Optimize** | Safe high-impact defaults for any new install |
| **System Core** | Explorer tweaks, Start Menu cleanup, Fast Startup, visual effects |
| **Gaming & GPU** | HAGS, Game Bar/DVR, MPO, Nagle's Algorithm, VRR, Ultimate Performance plan |
| **Handheld** | Hot-Bag fix, BitLocker/encryption, Core Isolation, EPP power slicing |
| **Privacy Shield** | Telemetry, Copilot, Recall AI, advertising ID, Cortana, location, OneDrive |
| **Advanced** | WSL, Hyper-V, NTFS/NIC overhead, foreground priority boost |
| **Maintenance** | SFC/DISM, WU reset, GPU cache clear, SSD trim, temp cleanup, driver audit |

### Safety Features
- Registry snapshot before every change — restore any value via `src/RoninSnapshotTool.ps1`
- System Restore checkpoint before batch operations
- BitLocker live-decryption banner (warns before reboot mid-decrypt)
- Expert Mode gate on destructive operations
- Hardware-aware: disables GPU tweaks that don't apply to your installed GPU

---

## CLI Mode — Hardware Diagnostics Toolkit

A Python command-line toolkit for diagnosing and fixing hardware issues. Requires Python 3.7+.

```bash
python kb_toolkit.py
# or double-click launch.bat
```

### Modules

**Input Devices**
- `kb_checker` — Keyboard driver status, connectivity, power management
- `kb_monitor` — Real-time key press monitoring, stuck-key detection
- `kb_remapper` — Scancode remapping, key disabling, stuck-key repair
- `mouse_checker` — PTP detection, drivers, connectivity, battery
- `mouse_monitor` — Cursor tracking, velocity, jitter detection
- `mouse_remapper` — Pointer speed, gestures, palm rejection

**Hardware**
- `storage_checker` — SMART-based disk health (requires smartmontools)
- `ram_checker` — Memory modules, capacity, speed, load
- `audio_checker` — Speakers, headphones, mics, audio services
- `hardware_checker` — WiFi, Bluetooth, thermals, ports, NFC, webcam, full device scan
- `display_checker` — GPUs, monitors, resolution, TDR crash history
- `battery_checker` — Charge status, wear percentage via powercfg

**Diagnostics**
- `network_checker` — Adapters, gateway ping, DNS, traceroute
- `startup_checker` — Startup programs, logon tasks, boot time, top processes
- `eventlog_checker` — Decodes recent Critical/Error events into plain language
- `system_health_checker` — SFC/DISM wrappers, Windows Update status, pending reboot
- `driver_checker` — Flags stale drivers by install date
- `report_generator` — Runs all read-only checkers, exports combined HTML + text report

**Repair & Cleanup**
- `repair_toolkit` — Network/Winsock reset, print spooler reset, WU component reset, Explorer restart
- `optimizer` — Temp/Prefetch/thumbnail/WU-cache cleanup, Recycle Bin, DNS flush

**Tweaks & Debloat** *(82 reversible tweaks, each with Apply/Revert/Check)*
- `debloat_privacy` — Telemetry, Copilot, Recall, ads, Cortana, location, OneDrive (25 tweaks)
- `gaming_tweaks` — HAGS, Game Bar/DVR, MPO, Nagle, Ultimate Perf plan, VRR, Game Mode (17 tweaks)
- `system_tweaks` — Classic context menu, visual FX, dark theme, Fast Startup, Explorer (26 tweaks)
- `handheld_tweaks` — Hibernate, power button, USB suspend, wake timers, Compact OS (10 tweaks)
- `advanced_tweaks` — Foreground priority, NTFS last-access, NIC power saving (4 tweaks)
- `reclaim_space` — Windows.old cleanup, WinSxS component store compaction

All tweaks write to registry/Group Policy only. State tracked in `logs/tweak_state.json`. System Restore checkpoint created before batch apply.

---

## Requirements

| Mode | Requirement |
|------|-------------|
| GUI | Windows 11 (24H2+), PowerShell 5.1+, Administrator, internet (first run only) |
| CLI | Windows 10/11, Python 3.7+, no extra packages |
| CLI (SMART) | [smartmontools](https://www.smartmontools.org/) for full disk health data |

---

## Repository Structure

```
Windows-Debloat-Toolkit/
├── Launch_Toolkit.bat        <- Master launcher (choose GUI or CLI)
├── Launch_Ronin.bat          <- GUI mode direct launcher
├── launch.bat                <- CLI mode direct launcher
├── Get-RoninSource.ps1       <- Downloads Ronin src/ + ui/ from GitHub
├── BuildRonin.ps1            <- Compiles standalone Ronin.ps1 monolith
├── kb_toolkit.py             <- CLI toolkit entry point
├── requirements.txt          <- Python optional dependencies
├── modules/                  <- Python diagnostic/tweak modules (29 modules)
├── src/                      <- Project Ronin PowerShell source (after Get-RoninSource)
│   ├── Ronin.ps1             <- UI controller
│   ├── RoninCore.ps1         <- Core engine, registry helpers, job dispatcher
│   ├── RoninDB.ps1           <- Tweak database (all Apply/Revert/Check logic)
│   └── RoninSnapshotTool.ps1 <- Standalone registry snapshot recovery
└── ui/
    └── Ronin.xaml            <- WPF UI definition
```

---

## Disclaimer

Open-source, MIT licensed. System-level changes carry some risk — keep backups of anything you cannot afford to lose. Every tweak uses officially documented registry and Group Policy values and can be individually reversed.
