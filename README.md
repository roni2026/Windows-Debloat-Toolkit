# Windows Input Device Troubleshooting Toolkit

A command-line toolkit for diagnosing and fixing keyboard, mouse, and general hardware problems on Windows — built for technicians and anyone dealing with flaky input devices, written in pure Python with no external dependencies beyond the standard library.

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

## Running it

```bash
python kb_toolkit.py
```

or on Windows, just double-click `launch.bat`.

Requires Python 3.7+. Everything runs on the standard library and Windows APIs — the one optional piece is [smartmontools](https://www.smartmontools.org/wiki/Download) for `storage_checker`'s SMART health data. Without it, disk enumeration still works, just without the SMART attributes. Several modules need admin rights (remapping, some registry reads) — the toolkit checks for this and tells you when it's needed.

## Structure

Each module lives under `modules/` and follows the same pattern — a `run()` entry point, shared UI helpers and Windows API wrappers pulled from `modules/kb_utils.py`. `kb_toolkit.py` is just the menu that ties them together.
