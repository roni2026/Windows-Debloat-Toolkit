# Windows Toolkit

A command-line toolkit for diagnosing, fixing, and tuning Windows — hardware troubleshooting on one side, reversible debloat/performance tweaks on the other, written in pure Python with no external dependencies beyond the standard library.

## Why

Most keyboard/mouse troubleshooting on Windows means digging through Device Manager, obscure registry keys, and driver versions by hand. This toolkit wraps all of that into a single menu-driven tool: run a module, get a plain-language diagnosis, fix what can be fixed automatically.

## What's included

**Keyboard** — hardware/driver diagnostics (`kb_checker`), live key press monitoring with stuck-key detection (`kb_monitor`), and scancode remapping / key disabling / stuck-key repair (`kb_remapper`).

**Mouse & trackpad** — device diagnostics including precision touchpad detection (`mouse_checker`), real-time cursor/button/velocity tracking (`mouse_monitor`), and pointer speed/gesture/palm-rejection configuration (`mouse_remapper`).

**Storage & memory** — SMART-based disk health via `smartctl` (`storage_checker`) and installed RAM/speed/load reporting (`ram_checker`).

**Printers & scanners** — installed devices, spooler status, and driver checks (`printer_checker`, `scanner_checker`).

**Audio & general hardware** — audio devices and services (`audio_checker`), plus a broad sweep covering WiFi, Bluetooth, thermals, ports, battery, webcam and anything else reporting a device error (`hardware_checker`).

**System maintenance** — temp/cache cleanup, Recycle Bin, DNS flush, with a live progress UI (`optimizer`).

**Advanced diagnostics** — network adapters and connectivity (`network_checker`), startup programs and boot time (`startup_checker`), plain-language decoding of recent event log errors (`eventlog_checker`), and SFC/DISM/Windows Update wrappers (`system_health_checker`).

**Display, power & recovery** — GPU/monitor/driver-crash history (`display_checker`) and battery health with wear percentage (`battery_checker`).

## Tweaks & Debloat

The second half of the toolkit: 82 reversible registry/Group Policy/powercfg tweaks across five modules, each with an Apply, Revert, and live status Check, so you can always see what's actually turned on and undo anything individually. A System Restore checkpoint is created automatically before a batch of tweaks is applied (where System Protection allows it).

- **`debloat_privacy`** (25 tweaks) — telemetry, Copilot, Recall, Activity History, advertising ID, Cortana, Start menu ads, taskbar Widgets, Delivery Optimization P2P updates, location tracking, OneDrive auto-start, consumer features, error reporting, Shared Experiences, Edge first-run/ads, telemetry scheduled tasks, feedback prompts, program inventory, cloud clipboard, map downloads, app-launch tracking, typing insights, tailored experiences, and more
- **`gaming_tweaks`** (17 tweaks) — Hardware-Accelerated GPU Scheduling, Game Bar/DVR, Multiplane Overlay, fullscreen optimizations, Nagle's Algorithm, Ultimate Performance power plan, VRR, Game Mode, Xbox background services, power/network throttling, mouse acceleration, system responsiveness, NTFS cache size, PCIe ASPM, GPU crash-recovery timeout, and GPU task priority
- **`system_tweaks`** (26 tweaks) — classic right-click context menu, background app throttling, visual effects, transparency, dark theme, Fast Startup, taskbar alignment/grouping, Explorer defaults, hidden files, clock seconds, lock screen, search indexing, Remote Assistance, adaptive brightness, menu delay, shortcut arrows, detailed BSOD info, Aero Shake, Explorer sidebar cleanup, setup nag notifications, and snap layout flyout
- **`handheld_tweaks`** (10 tweaks) — Hibernate enable, power button → hibernate (fixes the "wakes up hot in the bag" issue), USB selective suspend, wake timers, Wi-Fi power saving, touch keyboard auto-show, Compact OS, reduced hibernation file size, aggressive CPU boost mode, reserved storage, plus a guided (read-only) Core Isolation / Memory Integrity check
- **`advanced_tweaks`** (4 tweaks) — foreground app priority boost, NTFS last-access timestamp, network adapter power saving, and system-wide reserved storage
- **`reclaim_space`** — finds and removes `Windows.old` / upgrade-staging leftovers, and can compact the WinSxS component store via `DISM /StartComponentCleanup /ResetBase`

Applied/reverted state is tracked in `logs/tweak_state.json`, and each module can print a live ON/OFF/unknown status for every tweak it manages before you touch anything. A few categories of tweak are deliberately left out — OEM vendor-software integrations (Armoury Crate/Legion Space/MSI Center-style hooks) and anything touching BitLocker/disk encryption — since those either need software this toolkit can't verify is installed, or carry real data-loss/lockout risk that isn't appropriate for an unattended toggle.

## Running it

```bash
python kb_toolkit.py
```

or on Windows, just double-click `launch.bat`.

Requires Python 3.7+. Everything runs on the standard library and Windows APIs — the one optional piece is [smartmontools](https://www.smartmontools.org/wiki/Download) for `storage_checker`'s SMART health data. Without it, disk enumeration still works, just without the SMART attributes. Several modules need admin rights (remapping, some registry reads) — the toolkit checks for this and tells you when it's needed.

## Structure

Each module lives under `modules/` and follows the same pattern — a `run()` entry point, shared UI helpers and Windows API wrappers pulled from `modules/kb_utils.py`. `kb_toolkit.py` is just the menu that ties them together.
