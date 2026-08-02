# Input Device Troubleshooting Toolkit v2.0.0

A professional, modular command-line toolkit for Windows keyboard, mouse, and trackpad diagnostics, real-time monitoring, and configuration. Built for technicians, power users, and anyone dealing with faulty input devices.

---

## Features

### Keyboard Modules

#### 1. Keyboard Checker (`kb_checker`)
Comprehensive hardware and driver diagnostics:
- **Device Manager Enumeration** — Lists all keyboard devices via WMI with status and error codes
- **Driver Analysis** — Inspects `kbdclass.sys`, `kbdhid.sys`, `i8042prt.sys` versions and modification dates
- **HID Service Status** — Verifies KbdHid and KbdClass services are running
- **USB Connectivity** — Checks USB root hubs and PnP keyboard entities
- **Power Management** — Detects wake-armed devices and USB selective suspend settings
- **Filter Drivers** — Reports upper/lower filter drivers that may interfere
- **Error Code Translation** — Converts ConfigManagerErrorCode to human-readable descriptions

#### 2. Key Monitor (`kb_monitor`)
Real-time key press visualization:
- **Live Display** — Shows all currently pressed keys with hold duration
- **Stuck Key Detection** — Alerts when a key is held longer than 3 seconds
- **Scancode/VK Display** — Toggle between virtual-key codes and scancodes
- **Mouse Button Monitoring** — Optional LMB/RMB/MMB tracking
- **Event Logging** — Optional file logging of all key events
- **Statistics** — Session duration, total presses, stuck events

#### 3. Key Remapper (`kb_remapper`)
Advanced key management for faulty hardware:
- **Registry Scancode Map** — Persistent, system-wide remapping (requires admin + reboot)
- **Key Disabling** — Completely turn off problematic keys
- **Quick Stuck-Key Fix** — Auto-detects stuck keys and offers instant disable/remap
- **Session Hook Remapper** — Temporary remapping without reboot (experimental)
- **Backup/Restore** — Save and restore mapping configurations
- **Scancode Reference** — Built-in lookup table for all common keys

### Mouse & Trackpad Modules

#### 4. Mouse Checker (`mouse_checker`)
Comprehensive pointing device diagnostics:
- **Device Enumeration** — Lists all mice and trackpads via WMI with vendor detection
- **Precision Touchpad (PTP) Detection** — Identifies PTP vs legacy Synaptics/Elan/Alps
- **Driver Analysis** — Inspects `mouclass.sys`, `mouhid.sys`, vendor-specific drivers
- **HID Services** — Checks MouHid, MouClass, TabletInputService status
- **USB Connectivity** — USB hub status and wake-armed detection
- **Pointer Settings** — Reads registry for speed, acceleration, button swap, double-click
- **Trackpad Registry** — PTP settings, legacy driver detection, disable status
- **Power Management** — USB selective suspend settings
- **Wireless Status** — Battery info and Bluetooth mouse detection
- **Raw Input** — Multiple device conflict detection
- **Filter Drivers** — Upper/lower filter analysis

#### 5. Mouse Monitor (`mouse_monitor`)
Real-time cursor and button tracking:
- **Cursor Position** — Live X/Y coordinates with screen percentage
- **Button States** — LMB, RMB, MMB, X1, X2 press detection
- **Velocity Tracking** — Current, average, and peak cursor velocity
- **Distance Tracking** — Total pixels traveled
- **Jitter Detection** — Detects cursor teleportation (palm rejection issues, wireless interference)
- **Click History** — Recent click events with timestamps and positions
- **Cursor Trail** — ASCII visualization of recent movement path
- **Event Logging** — Optional click logging to file

#### 6. Mouse Settings (`mouse_remapper`)
Pointer behavior and trackpad configuration:
- **Pointer Speed** — Adjust sensitivity (1-20 scale)
- **Enhance Precision** — Toggle Windows mouse acceleration
- **Button Swap** — Left/right handed mode
- **Double-Click Speed** — Adjust timing (200-900ms)
- **Scroll Lines** — Wheel sensitivity (0-100 lines)
- **SnapTo** — Auto-move to default button in dialogs
- **Mouse Trails** — Visual cursor trail effect
- **Hide While Typing** — Vanish cursor during typing
- **Trackpad Enable/Disable** — Toggle PTP or legacy trackpad
- **Gestures** — Tap-to-click, two-finger scroll, three/four-finger tap, edge gestures
- **Palm Rejection** — Adjust cursor speed for better palm rejection
- **Natural Scrolling** — Content-follows-finger mode
- **Backup/Restore** — Save and restore all settings
- **Reset Defaults** — One-click restore to Windows defaults

### Storage & Memory Modules

#### 7. Storage Checker (`storage_checker`)
Disk enumeration and health diagnostics:
- **Dependency Check** — Auto-detects `smartctl.exe` (from **smartmontools**) on PATH or in a local `smartmontools\bin` folder
- **Device Manager Enumeration** — Lists all disk drives via WMI with status and error codes
- **Drive Details** — Model, interface (SATA/NVMe/USB), media type, size, serial, firmware
- **SMART Health Status** — Overall pass/fail health assessment per drive (requires smartmontools)
- **Key SMART Attributes** — Reallocated sectors, pending sectors, power-on hours, temperature, wear leveling / percentage used
- **Driver/Service Status** — Checks disk, partmgr, volmgr, storahci, stornvme services
- Runs WMI-only diagnostics even without smartmontools installed; SMART data is skipped gracefully with an install prompt

> **Requires smartmontools.** Download from https://www.smartmontools.org/wiki/Download, then either add `smartctl.exe` to PATH or place it at `<toolkit_folder>\smartmontools\bin\smartctl.exe`.

#### 8. RAM Checker (`ram_checker`)
Installed memory diagnostics:
- **Current Usage** — Total/used/available physical memory and live memory-load percentage
- **Physical Modules** — Per-slot capacity, bank/slot label, memory type (DDR3/DDR4/DDR5...), form factor
- **Speed Analysis** — Rated vs. currently-configured clock speed, flags underclocked or mismatched modules
- **Manufacturer Info** — Manufacturer, part number, serial number per stick
- **Memory Array** — Max supported capacity and populated vs. total slots
- **Page File** — Allocated size and current usage
- **Windows Memory Diagnostic** — Checks for `MdSched.exe` and points to it for a full RAM error-scan

### Printer & Scanner Modules

#### 9. Printer Checker (`printer_checker`)
Installed printer and spooler diagnostics:
- **Spooler Service** — Confirms the Print Spooler service is running, reports startup type, and gives the fix command if it's stopped
- **Installed Printers** — Lists all printers via WMI, flags which is default, local vs. network/shared, and offline status
- **Driver & Port Details** — Driver name, port name, and location per printer; flags missing driver info
- **Print Queue** — Lists pending jobs with owner and status, flags jobs stuck in error/paused/offline states
- **TCP/IP Ports** — Lists network printer ports with host address

#### 10. Scanner Checker (`scanner_checker`)
Imaging device and WIA diagnostics:
- **WIA Service** — Checks the Windows Image Acquisition service (`stisvc`) state and startup type
- **Imaging Device Enumeration** — WMI scan for scanner/imaging-class devices with status and error codes
- **Device Manager Class** — Reads the Imaging Devices registry class for installed driver entries
- **WIA/TWAIN Driver Files** — Checks for `wiaservc.dll`, `wiascanner.dll`, and `twain_32.dll`
- **Windows Scan App** — Detects whether the built-in Windows Scan app is installed
- Notes that multi-function printers often scan through the printer's own software rather than a dedicated WIA device

### Audio & General Hardware Modules

#### 11. Audio Checker (`audio_checker`)
Playback, recording, and audio subsystem diagnostics — internal speakers, headphones, earphones, external speakers, and microphones:
- **Audio Services** — Windows Audio, Audio Endpoint Builder, Multimedia Class Scheduler status
- **Sound Device Enumeration** — WMI list of all audio devices with status and error codes
- **Device Classification** — Auto-categorizes each device as Headphones/Earphones, Internal Speakers, External Speakers, Bluetooth Audio, HDMI/DisplayPort Audio, or Microphone based on its name
- **Playback Devices** — Resolves named output endpoints (speakers/headphones) from the audio render registry
- **Recording Devices** — Resolves named microphone endpoints from the audio capture registry
- **Driver Files** — Checks HD Audio Bus, USB Audio Class, and Bluetooth A2DP driver presence
- Works the same way on laptops (internal speakers, built-in mic) and desktops (external speakers, HDMI audio)

#### 12. Full Hardware Scan (`hardware_checker`)
A broad, "check everything" sweep across laptop and desktop components:
- **System Overview** — Manufacturer, model, chassis type (laptop vs. desktop), BIOS version
- **Battery** — Charge level and status (skipped automatically on desktops with no battery)
- **Wi-Fi** — Adapter presence, enabled state, live connection state and signal strength
- **Bluetooth** — Support service status plus all paired/installed Bluetooth devices
- **Fan / Thermal** — Fan telemetry and ACPI thermal zone temperatures where the firmware exposes them
- **Trackpad** — Presence and status (points to Mouse Checker/Settings for deeper gesture diagnostics)
- **Ports & Controllers** — USB controllers, Thunderbolt controller, connected displays
- **NFC / Smart Card Reader** — Detects NFC or smart card hardware if present
- **Mobile Broadband / SIM (WWAN)** — Detects LTE/5G modems and SIM-capable hardware
- **Memory Card Reader** — SD/MMC card reader detection
- **Webcam** — Built-in or external camera detection
- **Full Problem-Device Scan** — A catch-all sweep of *every* device Windows knows about, flagging anything with a driver/configuration error — this is what surfaces hardware issues outside the categories above ("anything else")

### Optimization Module

#### 13. System Optimizer (`optimizer`)
Safe, Windows-regenerated cache/temp cleanup with a live progress-bar and spinner UI:
- **User Temp** (`%TEMP%`) and **System Temp** (`C:\Windows\Temp`) — scans first to show file count/size, then deletes with a per-file progress bar
- **Prefetch Cache** — clears `*.pf` files (Windows rebuilds these automatically)
- **Thumbnail Cache** — clears `thumbcache_*.db` under Explorer's cache folder
- **Windows Error Reporting Queue** — clears queued/archived crash reports
- **Recycle Bin** — emptied via `Clear-RecycleBin`
- **Windows Update Download Cache** — stops `wuauserv`/`bits`, clears `SoftwareDistribution\Download`, restarts the services
- **DNS Resolver Cache** — `ipconfig /flushdns`
- **Directory Tree Report** — runs the `tree` command against the temp folder after cleanup and saves the full output to `logs/directory_tree_report.txt`
- Tasks needing elevation are clearly marked `[admin]` in the picker and auto-skipped (with an explanation) when not running elevated
- Every run ends with a summary: total space freed, files removed, files skipped (in use), and a completed/errored task list

Pick specific tasks by number, or `a` for all available (admin-gated ones auto-excluded if not elevated).

### Advanced Diagnostics Modules

#### 14. Network Checker (`network_checker`)
The "why is my internet broken" checklist:
- **Adapters** — parses `ipconfig /all` per adapter: connected/disconnected, IPv4, DHCP, gateway, DNS
- **Link Speed** — flags wired adapters negotiated below 100 Mbps
- **Gateway Connectivity** — pings the default gateway, reports packet loss/latency
- **Internet Connectivity** — pings Google DNS and Cloudflare DNS
- **DNS Resolution** — resolves several well-known domains via Python's own resolver (independent of external tools)
- **Traceroute** — a capped 10-hop `tracert` to 8.8.8.8, flags all-hops-timeout patterns (possible ICMP/firewall blocking)

#### 15. Startup & Performance Checker (`startup_checker`)
- **Last Boot** — boot timestamp plus last recorded boot duration (from the Diagnostics-Performance event log), flags slow boots
- **Startup Programs** — every registry/folder-based startup entry with its location and scope (all users vs. current user)
- **Logon Scheduled Tasks** — enabled scheduled tasks that trigger at logon (often missed by Task Manager's Startup tab)
- **Top Processes by Memory** — top 10 processes by working set size
- **Top Processes by CPU** — top 10 by instantaneous CPU%, color-coded by severity

#### 16. Event Log Scanner (`eventlog_checker`)
- **Log Health** — record count and % full for the System and Application logs
- **Critical/Error Scan** — queries both logs for the last 7 days, grouped by provider + event ID with occurrence counts
- **Plain-Language Decoding** — a built-in dictionary translates common event IDs (unexpected shutdown/Kernel-Power 41, disk errors, service crashes, application crashes/hangs, BSOD) into a one-line explanation instead of leaving you to Google the ID
- **Known Pattern Flags** — a dedicated summary of any matched high-signal patterns, with the most recent occurrence timestamp
- Only scans Critical/Error level — Warning-level noise is intentionally excluded

#### 17. System Health (`system_health_checker`)
SFC/DISM wrappers plus Windows Update status, presented as a task picker since some checks are slow:
- **DISM CheckHealth** — quick, read-only component store flag check
- **DISM ScanHealth** — deeper scan (a few minutes), reports whether corruption is repairable and points to `RestoreHealth`
- **SFC /scannow** — verifies and repairs protected system files (10-20+ minutes); result text is parsed into a clear outcome (healthy / repaired / unrepairable / incomplete) instead of leaving you to read raw sfc output
- **Windows Update Status** — `wuauserv`/`bits` service state plus the 5 most recently installed updates
- **Pending Reboot Check** — checks the three common registry locations Windows uses to flag a pending restart

Long-running steps (DISM ScanHealth, SFC) use an animated spinner since Windows doesn't expose a parseable live percentage for either.

### Display, Power & Recovery Modules

#### 18. Display/GPU Checker (`display_checker`)
- **Graphics Adapters** — name, driver version/date, video memory, status; flags multiple adapters as likely hybrid graphics (integrated + discrete)
- **Connected Monitors** — friendly name and serial via the WMI monitor namespace, with a Desktop Monitor fallback if that namespace is unavailable
- **Current Resolution & Refresh Rate** — per active adapter, flags sub-60Hz refresh
- **Display Driver Crash History (TDR)** — scans the last 14 days of the System log for "driver stopped responding and recovered" events and flags repeated crashes as a likely driver/thermal issue

#### 19. Battery Health (`battery_checker`)
- **Current Status** — charge %, charging/discharging state, per battery (skips cleanly on desktops with no battery detected)
- **`powercfg /batteryreport`** — generates the report to `logs/battery_report.html`, then parses Design Capacity vs. Full Charge Capacity to compute a battery health percentage and wear %, plus cycle count if Windows reports one
- Flags health below 80% (noticeable loss) and below 60% (consider replacement)

#### 20. Backup & Restore (`backup_checker`)
Answers "if I break something, can I undo it?":
- **System Restore** — service status, availability check, and the 10 most recent restore points with date/description/type
- **System Protection by Drive** — `vssadmin list shadowstorage` to confirm which volumes actually have protection turned on
- **File History** — service state and configuration status (not configured / configured / active)
- **VSS Service** — Volume Shadow Copy service state (normally Stopped until needed — the module notes this isn't itself a problem)
- **Legacy Windows Backup** — `wbadmin get versions` for scheduled/legacy backup images, where available
- If no restore points exist, points directly to Control Panel > System Protection to turn it on

### Drivers, Reporting & Repair Modules

#### 21. Driver Age Scanner (`driver_checker`)
- Enumerates every signed driver via WMI (`Win32_PnPSignedDriver`) and computes age from its driver date
- **This is a local heuristic, not a live "newer version available" check** — the module says so up front, since there's no internet/vendor database lookup involved
- Flags drivers 24+ months old, more urgently 48+ months old, with priority given to device classes people actually troubleshoot (Display, Net, Storage, Media, Keyboard, Mouse, USB, Bluetooth)
- Summary flags stale drivers in priority classes specifically, rather than burying them under printer/virtual-adapter noise

#### 22. One-Click Diagnostic Report (`report_generator`)
Runs the toolkit's 15 read-only checker modules — Keyboard, Mouse, Storage, RAM, Printer, Scanner, Audio, Full Hardware Scan, Network, Startup & Performance, Event Log, Display/GPU, Battery, Backup & Restore, Driver Age — back-to-back, headlessly:
- Pick specific checks or run all
- Each checker's output is captured, ANSI color codes stripped, and progress-bar/spinner artifacts collapsed to their final state for a clean report
- Every checker's `issues` list is pulled out and consolidated into a single "Issues Found Across All Checks" section at the top of the report
- Saves both a plain-text report and a styled dark-themed HTML report to `logs/diagnostic_report_<timestamp>.{txt,html}`, with an option to open the HTML version immediately
- **Deliberately excludes** Optimizer, System Health, Repair Toolkit (they take action, not just observe) and the monitor/remapper tools (they need live interactive input) — this is a read-only snapshot

#### 23. Reset & Repair Toolkit (`repair_toolkit`)
The fix-it counterpart to the checker modules — a task picker (no "run all", since these are targeted fixes, not a routine sweep):
- **Restart Windows Explorer** — kills and restarts `explorer.exe` for taskbar/icon glitches (no admin needed)
- **Reset Network Stack** — `netsh winsock reset` + `netsh int ip reset` (admin, needs reboot)
- **Release/Renew IP + Flush DNS** — full `ipconfig` repair sequence, no reboot needed
- **Reset Print Spooler** — stops the service, clears stuck jobs from the spool folder, restarts it (admin)
- **Reset Windows Update Components** — stops `wuauserv`/`cryptSvc`/`bits`/`msiserver`, renames `SoftwareDistribution` and `catroot2` to `.bak` so Windows rebuilds them, restarts the services (admin) — the deeper classic fix, beyond the Optimizer's cache-only clear
- **Rebuild Windows Search Index** — clears the index database and lets Windows reindex from scratch (admin)
- **Reset Microsoft Store Cache** — runs `wsreset.exe` (no admin needed)
- The three most disruptive actions (Winsock reset, Windows Update component reset, Search reindex) require an explicit `y/N` confirmation in addition to being selected, on top of the admin-gating used elsewhere

---

## Project Structure

```
kb_toolkit/
│
├── kb_toolkit.py          # Main launcher & interactive menu
├── launch.bat             # CMD launcher (double-click to run)
├── launch.ps1             # PowerShell launcher
├── requirements.txt       # Dependencies (smartmontools noted for storage_checker)
│
├── modules/
│   ├── kb_utils.py        # Shared utilities, colors, constants
│   ├── kb_checker.py      # Keyboard diagnostic engine
│   ├── kb_monitor.py      # Keyboard real-time monitor
│   ├── kb_remapper.py     # Keyboard remapping & disabling
│   ├── mouse_utils.py     # Mouse shared utilities
│   ├── mouse_checker.py   # Mouse diagnostic engine
│   ├── mouse_monitor.py   # Mouse real-time monitor
│   ├── mouse_remapper.py  # Mouse settings & trackpad config
│   ├── storage_checker.py # Disk/SMART diagnostic engine (needs smartmontools)
│   ├── ram_checker.py     # RAM module diagnostic engine
│   ├── printer_checker.py # Printer/spooler diagnostic engine
│   ├── scanner_checker.py # Scanner/WIA diagnostic engine
│   ├── audio_checker.py   # Speakers/headphones/mic diagnostic engine
│   ├── hardware_checker.py # WiFi/Bluetooth/fan/ports/NFC/SIM/etc. full scan
│   ├── optimizer.py       # Temp/Prefetch/cache cleanup with progress-bar UI
│   ├── network_checker.py # Adapters, ping/gateway/DNS, traceroute
│   ├── startup_checker.py # Startup programs, logon tasks, boot time, top processes
│   ├── eventlog_checker.py # Decodes recent Critical/Error events
│   ├── system_health_checker.py # SFC/DISM, Windows Update status, pending reboot
│   ├── display_checker.py # GPUs, monitors, resolution, driver crash history
│   ├── battery_checker.py # Battery charge status + powercfg wear report
│   ├── backup_checker.py  # System Restore points, File History, VSS, wbadmin
│   ├── driver_checker.py  # Flags stale drivers by age (local heuristic)
│   ├── report_generator.py # Runs all checkers, exports combined text+HTML report
│   └── repair_toolkit.py  # Network/spooler/WU reset, Explorer restart, and more
│
├── smartmontools/         # Optional local copy: smartmontools/bin/smartctl.exe
├── logs/                  # Auto-generated diagnostic logs (+ directory_tree_report.txt)
└── backups/               # Auto-generated setting backups
```

---

## Installation

1. **Extract** the toolkit to any folder (e.g., `C:\Tools\kb_toolkit`)
2. **No installation required** — Pure Python standard library
3. **Python 3.7+** must be installed and in PATH
4. **Windows 10/11** required (uses Windows-specific APIs)
5. **Optional, for full storage diagnostics:** install [smartmontools](https://www.smartmontools.org/wiki/Download) and put `smartctl.exe` on PATH, or in `<toolkit_folder>\smartmontools\bin\`. Without it, `storage_checker` still runs but skips SMART health data.

### Optional: Add to PATH
```cmd
setx PATH "%PATH%;C:\Tools\kb_toolkit"
```

---

## Usage

### Interactive Menu (Recommended)
```cmd
cd kb_toolkit
python kb_toolkit.py
```
Or simply double-click `launch.bat`

### Direct Module Access
```cmd
# Keyboard modules
python kb_toolkit.py --check       # Keyboard diagnostics
python kb_toolkit.py --monitor     # Keyboard monitor
python kb_toolkit.py --remap       # Keyboard remapper

# Mouse modules
python kb_toolkit.py --mcheck      # Mouse diagnostics
python kb_toolkit.py --mmonitor    # Mouse monitor
python kb_toolkit.py --mremap      # Mouse settings

# Storage & memory modules
python kb_toolkit.py --scheck      # Storage/SMART diagnostics (needs smartmontools)
python kb_toolkit.py --rcheck      # RAM diagnostics

# Printer & scanner modules
python kb_toolkit.py --prcheck     # Printer diagnostics
python kb_toolkit.py --sncheck     # Scanner diagnostics

# Audio & general hardware modules
python kb_toolkit.py --acheck      # Audio device diagnostics
python kb_toolkit.py --hwcheck     # Full hardware scan (WiFi, BT, fan, ports, NFC, SIM...)

# Optimization
python kb_toolkit.py --optimize    # Temp/Prefetch/cache cleanup + tree report

# Advanced diagnostics
python kb_toolkit.py --netcheck      # Network diagnostics (adapters, ping, DNS, traceroute)
python kb_toolkit.py --startupcheck  # Startup programs, logon tasks, boot time, top processes
python kb_toolkit.py --eventcheck    # Event log scan (decoded Critical/Error events)
python kb_toolkit.py --syshealth     # SFC/DISM, Windows Update status, pending reboot

# Display, power & recovery
python kb_toolkit.py --displaycheck  # GPUs, monitors, resolution, driver crash history
python kb_toolkit.py --batcheck      # Battery health (charge status + powercfg report)
python kb_toolkit.py --backupcheck   # System Restore points, File History, VSS status

# Drivers, reporting & repair
python kb_toolkit.py --drivercheck   # Driver age scan (local heuristic, no internet lookup)
python kb_toolkit.py --report        # One-click diagnostic report (all checkers, combined output)
python kb_toolkit.py --repair        # Reset/repair toolkit (network, spooler, WU, Explorer, Search)

# System
python kb_toolkit.py --admin       # Restart as Administrator
```

### PowerShell
```powershell
.\launch.ps1                    # Interactive menu
.\launch.ps1 -Check             # Keyboard diagnostics
.\launch.ps1 -MCheck            # Mouse diagnostics
.\launch.ps1 -MMonitor          # Mouse monitor
.\launch.ps1 -MRemap            # Mouse settings
.\launch.ps1 -Admin             # Elevate
```

---

## Module Details

### Keyboard Checker
Launches a comprehensive diagnostic that checks:
1. WMI keyboard device enumeration with ConfigManager error codes
2. Raw input device registry parameters
3. Driver file integrity and versions
4. Service status (KbdHid, KbdClass)
5. USB PnP device status
6. Power management settings
7. Upper/Lower filter drivers

**Output**: Color-coded results with summary of issues found.

### Key Monitor
Launches a full-screen real-time display:
- **Green** = Key just pressed
- **Yellow** = Key held >1 second
- **Red background** = Stuck key detected (>3 seconds)
- **Controls** (while running):
  - `S` — Toggle scancode display
  - `V` — Toggle VK code display
  - `M` — Toggle mouse button monitoring
  - `L` — Toggle event logging to file
  - `R` — Reset statistics
  - `Q` or `ESC` — Quit

### Key Remapper

#### Registry-Based (Persistent)
Requires Administrator privileges and a reboot.

**To disable a stuck key:**
1. Select `2. Disable key completely`
2. Enter key name (e.g., `A`, `F1`, `CAPS`) or hex scancode
3. Select `5. Apply registry changes`
4. Reboot when prompted

**To remap a key:**
1. Select `1. Remap key → another key`
2. Enter source and target keys
3. Apply and reboot

**Quick Fix for Stuck Keys:**
1. Select `9. Quick stuck-key fix`
2. Do not touch keyboard during 5-second detection
3. Toolkit auto-detects keys held down
4. Choose disable/remap option

#### Session Hook (Temporary)
No reboot required, but only active while toolkit is running.
- Select `10. Session hook remapper`
- Add mappings or disable keys
- Start the hook
- Keys are remapped/disabled immediately

### Mouse Checker
Comprehensive pointing device analysis:
1. WMI pointing device enumeration with vendor detection
2. Precision Touchpad (PTP) vs legacy detection
3. Driver file versions and integrity
4. HID service status
5. USB connectivity and power management
6. Pointer settings from registry
7. Trackpad-specific settings (PTP gestures, legacy drivers)
8. Wireless mouse battery detection
9. Multiple device conflict detection
10. Filter driver analysis

### Mouse Monitor
Real-time cursor tracking:
- **Cursor Position** — Live coordinates with screen bounds
- **Button States** — All 5 buttons with press indicators
- **Velocity** — Current, average, and peak speed
- **Distance** — Total travel distance in pixels
- **Jitter Detection** — Counts cursor teleport events
- **Click History** — Last 5 clicks with position
- **Trail** — ASCII path visualization
- **Controls** (while running):
  - `T` — Toggle cursor trail
  - `V` — Toggle velocity tracking
  - `J` — Toggle jitter detection
  - `L` — Toggle event logging
  - `R` — Reset statistics
  - `Q` or `ESC` — Quit

### Mouse Settings

**Pointer & Button Settings:**
- Adjust pointer speed (1-20)
- Toggle enhance pointer precision (acceleration)
- Swap left/right buttons
- Adjust double-click speed (200-900ms)
- Adjust scroll wheel lines
- Toggle SnapTo default button
- Toggle mouse trails
- Toggle hide pointer while typing

**Trackpad Settings:**
- Enable/disable trackpad (PTP requires admin)
- Configure gestures (tap-to-click, two-finger scroll, etc.)
- Adjust palm rejection sensitivity
- Toggle natural scrolling

**Management:**
- Backup current settings to JSON
- Restore from backup
- Reset all to Windows defaults
- View current settings summary

### Storage Checker
Disk enumeration and SMART health analysis:
1. Locates `smartctl.exe` (PATH, then local `smartmontools\bin`) — this is the toolkit's dependency on **smartmontools**
2. WMI disk drive enumeration with status/error codes
3. Model, interface, media type, size, serial, firmware per drive
4. `smartctl --scan` to find all scannable devices
5. `smartctl -H` for overall SMART pass/fail health
6. `smartctl -A` for key attributes (reallocated sectors, pending sectors, power-on hours, temperature, wear indicators)
7. Storage-related service status (disk, partmgr, volmgr, storahci, stornvme)
- If smartmontools isn't installed, WMI-based enumeration still runs and the summary flags the missing dependency instead of failing.

### RAM Checker
Installed memory diagnostics:
1. Live memory load via `GlobalMemoryStatusEx` — total/used/available physical memory and page file stats
2. Per-slot module details via WMI `Win32_PhysicalMemory` — bank, slot, capacity, type (DDR3/4/5), form factor
3. Rated vs. configured clock speed comparison, flags underclocked or mismatched-speed kits
4. Manufacturer, part number, and serial number per module
5. Memory array max capacity and populated vs. total slots
6. Page file allocation and usage
7. Points to Windows Memory Diagnostic (`mdsched.exe`) for a full hardware error scan

### Printer Checker
Printer and spooler diagnostics:
1. Print Spooler service status and startup type, with the `net start spooler` fix if stopped
2. WMI printer enumeration — default printer, local vs. network/shared, offline flag
3. Driver name and port per printer, flags printers with no driver reported
4. Pending print queue jobs with owner/status, flags jobs stuck in error/paused/offline
5. TCP/IP printer ports with host address

### Scanner Checker
Imaging device and WIA diagnostics:
1. WIA service (`stisvc`) state and startup type (on-demand start is normal for many scanners)
2. WMI enumeration of scanner/imaging-class PnP devices with status and error codes
3. Imaging Devices registry class driver entries
4. Presence of WIA/TWAIN driver files (`wiaservc.dll`, `wiascanner.dll`, `twain_32.dll`)
5. Whether the built-in Windows Scan app is installed
- Multi-function printers frequently expose scanning through their own bundled software rather than a dedicated WIA device — the summary notes this rather than treating it as an error

### Audio Checker
Speaker/headphone/mic diagnostics:
1. Windows Audio, Audio Endpoint Builder, and MMCSS service status
2. WMI sound device enumeration with status/error codes
3. Automatic classification of each device (headphones, internal speakers, external speakers, Bluetooth audio, HDMI/DisplayPort audio, microphone) based on its reported name
4. Named playback and recording endpoints resolved from the audio render/capture registry keys
5. HD Audio Bus / USB Audio Class / Bluetooth A2DP driver file presence
- Note: per-app/system volume and mute level aren't exposed through built-in WMI/PowerShell, so the module flags this limitation rather than guessing — check the Volume Mixer directly for mute state

### Full Hardware Scan
A single pass across the components most often asked about, plus a catch-all:
1. System/BIOS overview and chassis type (laptop vs. desktop) — used to skip battery/trackpad checks that don't apply
2. Battery charge and status (skipped cleanly on desktops)
3. Wi-Fi adapter status plus live `netsh wlan` connection state and signal
4. Bluetooth service and all Bluetooth-named devices
5. Fan and ACPI thermal zone data where firmware exposes it (many OEMs don't report fan speed to Windows at all — the module says so instead of showing a false negative)
6. Trackpad presence (delegates deep diagnostics to Mouse Checker)
7. USB controllers, Thunderbolt controller, connected displays
8. NFC / smart card reader, WWAN/SIM modem, memory card reader, webcam — each reported present/absent rather than assumed
9. **Full problem-device scan** — queries every PnP device on the system for a non-zero `ConfigManagerErrorCode`, so any hardware with a driver or configuration problem is caught even if it isn't one of the named categories above

### System Optimizer
Scan-then-clean flow, one task at a time, each with its own progress bar:
1. Presents a numbered task picker; admin-only tasks are labeled `[admin]` and greyed out with a reason if not elevated
2. For each selected task, scans the target folder first (file count + total size) before touching anything
3. Deletes with a live `[████████░░░░] 62.4%` progress bar, tallying bytes freed and files skipped (locked/in-use files are skipped, not force-closed)
4. Service-dependent tasks (Windows Update cache, Recycle Bin, DNS flush) use an animated spinner while the external command runs
5. Runs a `tree` report against the temp folder afterward, previews it in the terminal, and saves the full listing to `logs/directory_tree_report.txt`
6. Closes with a summary: tasks completed, total space freed, files removed/skipped, and any errors

**What it touches:** `%TEMP%`, `C:\Windows\Temp`, `C:\Windows\Prefetch`, the Explorer thumbnail cache, the WER report queue, the Recycle Bin, `C:\Windows\SoftwareDistribution\Download`, and the DNS resolver cache. It never touches Program Files, user documents, or the registry.

### Display/GPU Checker
1. Enumerates graphics adapters (driver version/date, video memory, status) and flags multiple adapters as likely hybrid graphics
2. Resolves connected monitor friendly names/serials via the WMI monitor namespace, falling back to Desktop Monitor enumeration if unavailable
3. Reports current resolution and refresh rate per adapter, flagging sub-60Hz
4. Scans the last 14 days of System log events from the `Display` provider for driver-stopped-responding (TDR) events and flags repeat crashes

### Battery Health
1. Reads current charge %, charging state, and per-battery status via WMI (cleanly skips desktops)
2. Runs `powercfg /batteryreport`, saving the HTML report to `logs/battery_report.html`
3. Parses Design Capacity and Full Charge Capacity out of the report to compute a battery health percentage and wear %, plus cycle count if available
4. Flags health under 80% and, more urgently, under 60%

### Backup & Restore
1. Checks the Software Shadow Copy Provider service and confirms System Restore availability
2. Lists the 10 most recent restore points (date, description, type)
3. Cross-checks `vssadmin list shadowstorage` to confirm which drives actually have System Protection turned on — a restore point existing doesn't guarantee every drive is covered
4. File History service state and configuration status
5. VSS service state (explains that "Stopped" is normal/expected when idle)
6. Legacy `wbadmin get versions` for scheduled/image backups, where the feature is installed
7. If nothing is protected, points directly to where to turn on System Protection

### Driver Age Scanner
1. Queries `Win32_PnPSignedDriver` for every installed driver's date, version, manufacturer, and device class
2. Computes age in months from each driver's date to today
3. Sorts stale drivers (24+ months) with priority device classes (Display, Net, Storage, Media, input devices, Bluetooth, USB) surfaced first, then by age
4. Flags anything 48+ months old in a priority class as a specific issue in the summary
5. Explicitly states this is a local staleness heuristic, not a check against any online "latest driver" database

### One-Click Diagnostic Report
1. Presents a picker over the toolkit's 15 read-only checkers; pick specific ones or run all
2. For each selected checker: imports it, monkey-patches its `prompt_continue()` to a no-op so it doesn't block waiting for Enter, and runs it with stdout captured
3. Captured output has ANSI color codes stripped and carriage-return progress-bar/spinner frames collapsed down to their final state, so the saved report reads cleanly
4. Each checker's `self.issues` list is pulled and merged into one "Issues Found Across All Checks" section up front
5. Writes both a plain-text and a styled HTML report to `logs/diagnostic_report_<timestamp>.{txt,html}`, and offers to open the HTML version
6. A checker that errors out is caught individually and noted, without stopping the rest of the report

### Reset & Repair Toolkit
1. Task picker (numbers only, no "run all") since these are targeted fixes for specific symptoms, not a routine sweep
2. Admin-gated tasks are labeled `[admin]`; the three most disruptive (Winsock reset, Windows Update component reset, Search reindex) are also labeled `[confirm]` and require a separate `y/N` before running
3. Each task prints what it's doing via the shared spinner UI, then a clear success/failure line
4. Windows Update component reset renames (not deletes) `SoftwareDistribution`/`catroot2` to `.bak`, so Windows rebuilds clean folders automatically — nothing is destroyed outright
5. Closes with a completed/error task list and a reminder to reboot if the network stack was reset

---

## Admin Privileges

Some features require Administrator rights:

| Feature | Admin Required |
|---------|---------------|
| Registry key remap/disable | ✅ Yes |
| Clearing registry mappings | ✅ Yes |
| Trackpad enable/disable (PTP) | ✅ Yes |
| View some driver details | ✅ Yes |
| System Temp / Prefetch / Windows Update cache cleanup | ✅ Yes |
| SFC /scannow, DISM ScanHealth | ✅ Yes |
| Full shadow-storage/System Protection details (`vssadmin`) | ✅ Yes (partial results without) |
| Winsock/TCP-IP reset, Print Spooler reset, WU component reset, Search reindex | ✅ Yes |
| Key/mouse monitor | ❌ No |
| Session hook | ❌ No |
| Pointer speed adjustment | ❌ No |
| User Temp / thumbnail / WER / Recycle Bin / DNS cleanup | ❌ No |
| DISM CheckHealth, network/event log/startup diagnostics | ❌ No |
| Display/GPU check, battery health report, driver age scan | ❌ No |
| Explorer restart, Store cache reset, IP release/renew | ❌ No |
| Most diagnostics | ❌ No |

**To elevate:** Press `A` in the main menu, or run:
```cmd
python kb_toolkit.py --admin
```

---

## Scancode Reference

Common scancodes used by the keyboard remapper:

| Key | Scancode | Key | Scancode | Key | Scancode |
|-----|----------|-----|----------|-----|----------|
| ESC | 0x01 | A | 0x1E | SPACE | 0x39 |
| 1-0 | 0x02-0x0B | S | 0x1F | CAPS | 0x3A |
| Q | 0x10 | D | 0x20 | F1-F12 | 0x3B-0x58 |
| W | 0x11 | F | 0x21 | ENTER | 0x1C |
| E | 0x12 | Z | 0x2C | BACK | 0x0E |
| R | 0x13 | X | 0x2D | TAB | 0x0F |
| T | 0x14 | C | 0x2E | LSHIFT | 0x2A |
| Y | 0x15 | V | 0x2F | LCTRL | 0x1D |
| U | 0x16 | B | 0x30 | LALT | 0x38 |
| I | 0x17 | N | 0x31 | LWIN | 0x15B |
| O | 0x18 | M | 0x32 | RWIN | 0x15C |
| P | 0x19 | COMMA | 0x33 | APPS | 0x15D |

Use the built-in reference table (option 11 in remapper) for the full list.

---

## Troubleshooting

### "No keyboard/mouse devices detected"
- Device may be connected via a non-standard controller
- Check physical connection and try a different USB port
- Run as Administrator for deeper inspection

### "Failed to apply registry changes"
- You must run as Administrator to modify the scancode map
- Use option `A` in the main menu to elevate

### "Hook failed to start"
- Some antivirus software blocks low-level input hooks
- Try the registry-based method instead

### Monitor shows keys/buttons I'm not pressing
- This indicates a **hardware fault** — the switch is stuck
- Use Quick Stuck-Key Fix (keyboard) or check for wireless interference (mouse)

### Trackpad not responding to enable/disable
- Legacy trackpads require Fn+key combination or Device Manager
- PTP changes require Administrator and reboot

### Changes not taking effect after reboot
- Ensure you selected `Apply registry changes` before rebooting
- Check that the registry value exists:
  ```cmd
  reg query "HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layout" /v "Scancode Map"
  ```

---

## Safety Notes

- **Always backup before remapping** — Use option 7 (keyboard) or 13 (mouse)
- **Registry changes require reboot** — Save your work before rebooting
- **Disabling critical keys** — Be careful disabling ESC, ENTER, or modifier keys
- **Hook mode is session-only** — If you disable a key via hook and close the toolkit, the key will work again
- **Mouse trails may impact performance** — Disable if you notice cursor lag

---

## Advanced: Manual Registry Editing

### Keyboard Scancode Map
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layout
Value: Scancode Map (REG_BINARY)
```

Format:
```
00 00 00 00 00 00 00 00   ; Header
02 00 00 00               ; Count (mappings + 1)
XX XX YY YY               ; Mapping (Target:Source)
00 00 00 00               ; Null terminator
```

Example: Map CAPS (0x3A) to ESC (0x01)
```
00 00 00 00 00 00 00 00 02 00 00 00 01 00 3A 00 00 00 00 00
```

### Mouse Settings
```
HKEY_CURRENT_USER\Control Panel\Mouse
```

Key values:
- `MouseSensitivity` — 1-20 (10=default)
- `MouseSpeed` — 0 or 1 (enhance precision)
- `SwapMouseButtons` — 0 or 1
- `DoubleClickSpeed` — 200-900ms
- `WheelScrollLines` — 0-100

---

## Adding Future Modules

The main file (`kb_toolkit.py`) dynamically imports from `modules/`. To add a new troubleshooting tool:

1. Create `modules/your_module.py`
2. Add a `run()` method or `main()` function
3. Wire it into `kb_toolkit.py` in the `_run_module()` and menu methods

For a long-running or file-heavy task, `modules/kb_utils.py` now also provides:
- `print_progress_bar(current, total, prefix, suffix)` — in-place `[████░░░░] 62%` bar
- `Spinner("message")` — animated spinner, usable as a context manager, for indeterminate-length steps
- `print_task_header(step, total, title)`, `print_stat(label, value)`, `print_divider()` — consistent step/summary formatting
- `format_bytes(size)` — shared human-readable byte formatter

`optimizer.py` is a full example of all of these in use.

The toolkit is **pure Python standard library** — no pip installs needed. Just Python 3.7+ on Windows 10/11.

---

## License

MIT License — Free for personal and commercial use.

---

## Changelog

### v2.0.0
- Added Mouse & Trackpad diagnostic suite
- Added Mouse Checker with PTP detection and vendor identification
- Added Mouse Monitor with velocity tracking and jitter detection
- Added Mouse Settings with pointer speed, gestures, palm rejection
- Updated main menu with unified keyboard + mouse interface
- Added PowerShell launcher parameters for mouse modules

### v1.0.0
- Initial release
- Keyboard diagnostic engine
- Real-time key monitor with stuck-key detection
- Registry and session-based key remapper
- Admin elevation helper
- Logging and backup system
