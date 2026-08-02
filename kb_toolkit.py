#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INPUT DEVICE TROUBLESHOOTING TOOLKIT                      ║
║                     Keyboard, Mouse & Trackpad Repair Suite                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

A professional command-line toolkit for Windows input device diagnostics,
monitoring, and remapping.

Keyboard Modules:
  • kb_checker   — Hardware/driver diagnostics and connectivity analysis
  • kb_monitor   — Real-time key press monitoring with stuck-key detection
  • kb_remapper  — Scancode remapping, key disabling, and stuck-key repair

Mouse & Trackpad Modules:
  • mouse_checker   — Pointing device diagnostics, PTP detection, driver analysis
  • mouse_monitor   — Real-time cursor tracking, velocity, jitter detection
  • mouse_remapper  — Pointer speed, button swap, trackpad gestures, palm rejection

Storage & Memory Modules:
  • storage_checker — Disk health via SMART (requires smartmontools/smartctl)
  • ram_checker     — Installed memory modules, capacity, speed, current load

Printer & Scanner Modules:
  • printer_checker — Installed printers, spooler service, ports, print queue
  • scanner_checker — Imaging devices, WIA service, TWAIN/driver detection

Audio & General Hardware Modules:
  • audio_checker    — Speakers, headphones, earphones, mics, audio services
  • hardware_checker — WiFi, Bluetooth, fan/thermal, trackpad, ports, NFC,
                        SIM/WWAN, card reader, battery, webcam, and a full
                        system-wide scan for any other device reporting errors

Optimization Module:
  • optimizer — Temp/Prefetch/thumbnail/WU-cache cleanup, Recycle Bin, DNS
                 flush, and a directory tree report — with a live progress
                 bar and spinner UI

Advanced Diagnostics Modules:
  • network_checker       — Adapters, gateway/internet ping, DNS, traceroute
  • startup_checker       — Startup programs, logon tasks, boot time, top processes
  • eventlog_checker      — Decodes recent Critical/Error events into plain language
  • system_health_checker — SFC/DISM wrappers, Windows Update status, pending reboot

Display, Power & Recovery Modules:
  • display_checker — GPUs, connected monitors, resolution/refresh rate,
                       display driver crash (TDR) history
  • battery_checker — Current charge/status plus a powercfg battery report
                       with design-vs-full-charge wear percentage
  • backup_checker  — System Restore points, File History, VSS, and legacy
                       Windows Backup status

Driver, Reporting & Repair Modules:
  • driver_checker    — Flags installed drivers by age (local heuristic,
                         not a live "latest version" check)
  • report_generator  — Runs all read-only checkers headlessly and exports
                         one consolidated text + HTML diagnostic report
  • repair_toolkit    — The fix-it counterpart: network/Winsock reset,
                         print spooler reset, Windows Update component
                         reset, Explorer restart, Search reindex, and more

Usage:
  python kb_toolkit.py              Launch interactive menu
  python kb_toolkit.py --check      Run keyboard check directly
  python kb_toolkit.py --monitor    Launch key monitor directly
  python kb_toolkit.py --remap      Launch key remapper directly
  python kb_toolkit.py --mcheck     Run mouse check directly
  python kb_toolkit.py --mmonitor   Launch mouse monitor directly
  python kb_toolkit.py --mremap     Open mouse settings directly
  python kb_toolkit.py --scheck     Run storage/SMART check directly
  python kb_toolkit.py --rcheck     Run RAM check directly
  python kb_toolkit.py --prcheck    Run printer check directly
  python kb_toolkit.py --sncheck    Run scanner check directly
  python kb_toolkit.py --acheck     Run audio device check directly
  python kb_toolkit.py --hwcheck    Run full hardware check directly
  python kb_toolkit.py --optimize   Run system optimization directly
  python kb_toolkit.py --netcheck   Run network diagnostics directly
  python kb_toolkit.py --startupcheck  Run startup/performance check directly
  python kb_toolkit.py --eventcheck    Run event log scan directly
  python kb_toolkit.py --syshealth     Run SFC/DISM/update health check directly
  python kb_toolkit.py --displaycheck  Run display/GPU check directly
  python kb_toolkit.py --batcheck      Run battery health check directly
  python kb_toolkit.py --backupcheck   Run backup/restore point check directly
  python kb_toolkit.py --drivercheck   Run driver age scan directly
  python kb_toolkit.py --report        Run one-click diagnostic report directly
  python kb_toolkit.py --repair        Open the reset/repair toolkit directly
  python kb_toolkit.py --admin      Restart as Administrator

Author: Input Device Toolkit
Version: 2.0.0
"""
import sys
import os
import argparse
import ctypes

# Add modules directory to path
MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
sys.path.insert(0, MODULES_DIR)

from kb_utils import (
    Colors, print_banner, print_success, print_error, 
    print_warning, print_info, is_admin, setup_logging
)

VERSION = "2.0.0"

class ToolkitApp:
    def __init__(self):
        self.log_file = None

    def run(self):
        parser = argparse.ArgumentParser(
            description="Input Device Troubleshooting Toolkit",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s                    Start interactive menu
  %(prog)s -c                 Run keyboard diagnostic
  %(prog)s -m                 Start keyboard monitor
  %(prog)s -r                 Open keyboard remapper
  %(prog)s --mcheck           Run mouse diagnostic
  %(prog)s --mmonitor         Start mouse monitor
  %(prog)s --mremap           Open mouse settings
  %(prog)s --admin            Elevate to Administrator
            """
        )
        parser.add_argument("-c", "--check", action="store_true", help="Run keyboard check")
        parser.add_argument("-m", "--monitor", action="store_true", help="Start keyboard monitor")
        parser.add_argument("-r", "--remap", action="store_true", help="Open keyboard remapper")
        parser.add_argument("--mcheck", action="store_true", help="Run mouse check")
        parser.add_argument("--mmonitor", action="store_true", help="Start mouse monitor")
        parser.add_argument("--mremap", action="store_true", help="Open mouse settings")
        parser.add_argument("--scheck", action="store_true", help="Run storage/SMART check")
        parser.add_argument("--rcheck", action="store_true", help="Run RAM check")
        parser.add_argument("--prcheck", action="store_true", help="Run printer check")
        parser.add_argument("--sncheck", action="store_true", help="Run scanner check")
        parser.add_argument("--acheck", action="store_true", help="Run audio device check")
        parser.add_argument("--hwcheck", action="store_true", help="Run full hardware check")
        parser.add_argument("--optimize", action="store_true", help="Run system optimization")
        parser.add_argument("--netcheck", action="store_true", help="Run network diagnostics")
        parser.add_argument("--startupcheck", action="store_true", help="Run startup/performance check")
        parser.add_argument("--eventcheck", action="store_true", help="Run event log scan")
        parser.add_argument("--syshealth", action="store_true", help="Run SFC/DISM/update health check")
        parser.add_argument("--displaycheck", action="store_true", help="Run display/GPU check")
        parser.add_argument("--batcheck", action="store_true", help="Run battery health check")
        parser.add_argument("--backupcheck", action="store_true", help="Run backup/restore point check")
        parser.add_argument("--drivercheck", action="store_true", help="Run driver age scan")
        parser.add_argument("--report", action="store_true", help="Run one-click diagnostic report")
        parser.add_argument("--repair", action="store_true", help="Open the reset/repair toolkit")
        parser.add_argument("--admin", action="store_true", help="Restart as Administrator")
        parser.add_argument("--version", action="store_true", help="Show version")

        args = parser.parse_args()

        if args.version:
            print(f"Input Device Troubleshooting Toolkit v{VERSION}")
            sys.exit(0)

        if args.admin:
            self._elevate_admin()
            sys.exit(0)

        # Setup logging
        try:
            self.log_file = setup_logging()
        except Exception:
            pass

        # Direct mode
        if args.check:
            self._run_module("kb_checker")
        elif args.monitor:
            self._run_module("kb_monitor")
        elif args.remap:
            self._run_module("kb_remapper")
        elif args.mcheck:
            self._run_module("mouse_checker")
        elif args.mmonitor:
            self._run_module("mouse_monitor")
        elif args.mremap:
            self._run_module("mouse_remapper")
        elif args.scheck:
            self._run_module("storage_checker")
        elif args.rcheck:
            self._run_module("ram_checker")
        elif args.prcheck:
            self._run_module("printer_checker")
        elif args.sncheck:
            self._run_module("scanner_checker")
        elif args.acheck:
            self._run_module("audio_checker")
        elif args.hwcheck:
            self._run_module("hardware_checker")
        elif args.optimize:
            self._run_module("optimizer")
        elif args.netcheck:
            self._run_module("network_checker")
        elif args.startupcheck:
            self._run_module("startup_checker")
        elif args.eventcheck:
            self._run_module("eventlog_checker")
        elif args.syshealth:
            self._run_module("system_health_checker")
        elif args.displaycheck:
            self._run_module("display_checker")
        elif args.batcheck:
            self._run_module("battery_checker")
        elif args.backupcheck:
            self._run_module("backup_checker")
        elif args.drivercheck:
            self._run_module("driver_checker")
        elif args.report:
            self._run_module("report_generator")
        elif args.repair:
            self._run_module("repair_toolkit")
        else:
            self._interactive_menu()

    def _interactive_menu(self):
        while True:
            os.system("cls" if os.name == "nt" else "clear")

            admin_status = f"{Colors.GREEN}[ADMIN]{Colors.END}" if is_admin() else f"{Colors.YELLOW}[USER]{Colors.END}"

            print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.END}
{Colors.CYAN}║{Colors.END}                                                                              {Colors.CYAN}║{Colors.END}
{Colors.CYAN}║{Colors.END}        {Colors.BOLD}{Colors.WHITE}INPUT DEVICE TROUBLESHOOTING TOOLKIT v{VERSION}{Colors.END}                   {Colors.CYAN}║{Colors.END}
{Colors.CYAN}║{Colors.END}                                                                              {Colors.CYAN}║{Colors.END}
{Colors.CYAN}║{Colors.END}      {Colors.GRAY}Full Laptop & Desktop Hardware Diagnostic Suite{Colors.END}               {Colors.CYAN}║{Colors.END}
{Colors.CYAN}║{Colors.END}                                                                              {Colors.CYAN}║{Colors.END}
{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}

  {Colors.GRAY}Privilege Level:{Colors.END} {admin_status}
  {Colors.GRAY}Log File:{Colors.END} {Colors.GRAY}{self.log_file or 'Not active'}{Colors.END}

  {Colors.BOLD}{Colors.BLUE}KEYBOARD{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}1.{Colors.END} Keyboard Checker    — Driver status, connectivity, power management    {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}2.{Colors.END} Key Monitor         — Real-time press detection & stuck-key alert      {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}3.{Colors.END} Key Remapper        — Disable/remap keys, fix stuck keys               {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.YELLOW}MOUSE & TRACKPAD{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}4.{Colors.END} Mouse Checker       — PTP detection, drivers, connectivity, battery  {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}5.{Colors.END} Mouse Monitor       — Cursor tracking, velocity, jitter detection    {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}6.{Colors.END} Mouse Settings      — Pointer speed, gestures, palm rejection        {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.MAGENTA}STORAGE & MEMORY{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}7.{Colors.END} Storage Checker     — Disk health via SMART (needs smartmontools)    {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}8.{Colors.END} RAM Checker         — Memory modules, capacity, speed, current load  {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.HEADER}PRINTER & SCANNER{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}9.{Colors.END} Printer Checker     — Spooler, drivers, ports, print queue           {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}10.{Colors.END} Scanner Checker    — WIA service, imaging devices, TWAIN            {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.CYAN}AUDIO & GENERAL HARDWARE{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}11.{Colors.END} Audio Checker      — Speakers, headphones, earphones, mics, services {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}12.{Colors.END} Full Hardware Scan — WiFi, Bluetooth, fan, ports, NFC, SIM & more    {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.GREEN}OPTIMIZATION{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}13.{Colors.END} System Optimizer   — Temp/Prefetch/cache cleanup, tree report        {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.YELLOW}ADVANCED DIAGNOSTICS{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}14.{Colors.END} Network Checker    — Adapters, gateway/internet ping, DNS, traceroute {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}15.{Colors.END} Startup & Perf     — Startup programs, logon tasks, boot time, top procs {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}16.{Colors.END} Event Log Scanner  — Decodes recent Critical/Error events            {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}17.{Colors.END} System Health      — SFC/DISM, Windows Update status, pending reboot {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.YELLOW}DISPLAY, POWER & RECOVERY{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}18.{Colors.END} Display/GPU Checker — GPUs, monitors, resolution, driver crash history{Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}19.{Colors.END} Battery Health      — Charge status + powercfg wear-level report      {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}20.{Colors.END} Backup & Restore    — Restore points, File History, VSS, wbadmin      {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.MAGENTA}DRIVERS, REPORTING & REPAIR{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}21.{Colors.END} Driver Age Scanner  — Flags stale drivers by age (local heuristic)    {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}22.{Colors.END} One-Click Report    — Runs all checkers, saves a combined report      {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}23.{Colors.END} Reset & Repair      — Network/spooler/WU reset, Explorer restart, more{Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.BOLD}{Colors.GREEN}SYSTEM TOOLS{Colors.END}
  {Colors.CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}A.{Colors.END} Elevate to Admin    — Restart toolkit with Administrator rights      {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}I.{Colors.END} System Info         — Show Windows version and input device info     {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}│{Colors.END} {Colors.CYAN}L.{Colors.END} View Logs           — Open latest diagnostic log file              {Colors.CYAN}│{Colors.END}
  {Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}

  {Colors.CYAN}0.{Colors.END} Exit
""")

            choice = input(f"  {Colors.CYAN}Select option: {Colors.END}").strip().lower()

            if choice == "1":
                self._run_module("kb_checker")
            elif choice == "2":
                self._run_module("kb_monitor")
            elif choice == "3":
                self._run_module("kb_remapper")
            elif choice == "4":
                self._run_module("mouse_checker")
            elif choice == "5":
                self._run_module("mouse_monitor")
            elif choice == "6":
                self._run_module("mouse_remapper")
            elif choice == "7":
                self._run_module("storage_checker")
            elif choice == "8":
                self._run_module("ram_checker")
            elif choice == "9":
                self._run_module("printer_checker")
            elif choice == "10":
                self._run_module("scanner_checker")
            elif choice == "11":
                self._run_module("audio_checker")
            elif choice == "12":
                self._run_module("hardware_checker")
            elif choice == "13":
                self._run_module("optimizer")
            elif choice == "14":
                self._run_module("network_checker")
            elif choice == "15":
                self._run_module("startup_checker")
            elif choice == "16":
                self._run_module("eventlog_checker")
            elif choice == "17":
                self._run_module("system_health_checker")
            elif choice == "18":
                self._run_module("display_checker")
            elif choice == "19":
                self._run_module("battery_checker")
            elif choice == "20":
                self._run_module("backup_checker")
            elif choice == "21":
                self._run_module("driver_checker")
            elif choice == "22":
                self._run_module("report_generator")
            elif choice == "23":
                self._run_module("repair_toolkit")
            elif choice == "a":
                self._elevate_admin()
                break
            elif choice == "i":
                self._show_system_info()
            elif choice == "l":
                self._open_logs()
            elif choice == "0":
                print(f"\n{Colors.GREEN}Goodbye!{Colors.END}")
                break
            else:
                print_error("Invalid option")
                input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")

    def _run_module(self, module_name):
        try:
            if module_name == "kb_checker":
                from kb_checker import KeyboardChecker
                KeyboardChecker().run()
            elif module_name == "kb_monitor":
                from kb_monitor import KeyMonitor
                KeyMonitor().run()
            elif module_name == "kb_remapper":
                from kb_remapper import KeyRemapper
                KeyRemapper().run()
            elif module_name == "mouse_checker":
                from mouse_checker import MouseChecker
                MouseChecker().run()
            elif module_name == "mouse_monitor":
                from mouse_monitor import MouseMonitor
                MouseMonitor().run()
            elif module_name == "mouse_remapper":
                from mouse_remapper import MouseRemapper
                MouseRemapper().run()
            elif module_name == "storage_checker":
                from storage_checker import StorageChecker
                StorageChecker().run()
            elif module_name == "ram_checker":
                from ram_checker import RamChecker
                RamChecker().run()
            elif module_name == "printer_checker":
                from printer_checker import PrinterChecker
                PrinterChecker().run()
            elif module_name == "scanner_checker":
                from scanner_checker import ScannerChecker
                ScannerChecker().run()
            elif module_name == "audio_checker":
                from audio_checker import AudioChecker
                AudioChecker().run()
            elif module_name == "hardware_checker":
                from hardware_checker import HardwareChecker
                HardwareChecker().run()
            elif module_name == "optimizer":
                from optimizer import SystemOptimizer
                SystemOptimizer().run()
            elif module_name == "network_checker":
                from network_checker import NetworkChecker
                NetworkChecker().run()
            elif module_name == "startup_checker":
                from startup_checker import StartupChecker
                StartupChecker().run()
            elif module_name == "eventlog_checker":
                from eventlog_checker import EventLogChecker
                EventLogChecker().run()
            elif module_name == "system_health_checker":
                from system_health_checker import SystemHealthChecker
                SystemHealthChecker().run()
            elif module_name == "display_checker":
                from display_checker import DisplayChecker
                DisplayChecker().run()
            elif module_name == "battery_checker":
                from battery_checker import BatteryChecker
                BatteryChecker().run()
            elif module_name == "backup_checker":
                from backup_checker import BackupChecker
                BackupChecker().run()
            elif module_name == "driver_checker":
                from driver_checker import DriverChecker
                DriverChecker().run()
            elif module_name == "report_generator":
                from report_generator import ReportGenerator
                ReportGenerator().run()
            elif module_name == "repair_toolkit":
                from repair_toolkit import RepairToolkit
                RepairToolkit().run()
        except ImportError as e:
            print_error(f"Failed to load module '{module_name}': {e}")
            print_info(f"Ensure '{module_name}.py' exists in: {MODULES_DIR}")
            input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")
        except Exception as e:
            print_error(f"Module error: {e}")
            input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")

    def _elevate_admin(self):
        if is_admin():
            print_success("Already running as Administrator")
            input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")
            return

        print_warning("Requesting Administrator elevation...")
        try:
            script = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
        except Exception as e:
            print_error(f"Elevation failed: {e}")
            print_info("Please right-click and 'Run as Administrator' manually")
            input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")

    def _show_system_info(self):
        print_banner("SYSTEM INFORMATION", Colors.CYAN)

        import platform
        print(f"{Colors.BOLD}Operating System:{Colors.END}")
        print(f"  {Colors.WHITE}{platform.platform()}{Colors.END}")
        print(f"  Version: {Colors.GRAY}{platform.version()}{Colors.END}")
        print(f"  Architecture: {Colors.GRAY}{platform.machine()}{Colors.END}")

        print(f"\n{Colors.BOLD}Python:{Colors.END}")
        print(f"  {Colors.WHITE}{platform.python_version()}{Colors.END}")
        print(f"  Executable: {Colors.GRAY}{sys.executable}{Colors.END}")

        # Keyboard layout
        try:
            klid = ctypes.windll.user32.GetKeyboardLayout(0)
            lid = klid & 0xFFFF
            print(f"\n{Colors.BOLD}Keyboard Layout:{Colors.END}")
            print(f"  Layout ID: {Colors.GRAY}0x{lid:04X}{Colors.END}")

            layouts = {
                0x0409: "US English", 0x0809: "UK English", 0x0407: "German",
                0x040C: "French", 0x0410: "Italian", 0x0A0A: "Spanish (Latin America)",
                0x040A: "Spanish (Spain)", 0x0411: "Japanese", 0x0412: "Korean",
                0x0804: "Chinese (Simplified)", 0x0404: "Chinese (Traditional)",
                0x0419: "Russian", 0x041D: "Swedish", 0x0413: "Dutch",
                0x0406: "Danish", 0x040B: "Finnish", 0x040E: "Hungarian",
                0x0415: "Polish", 0x0416: "Portuguese (Brazil)", 0x0816: "Portuguese (Portugal)",
                0x0408: "Greek", 0x0405: "Czech", 0x041A: "Croatian",
                0x041C: "Albanian", 0x041F: "Turkish", 0x0422: "Ukrainian",
                0x0429: "Farsi", 0x042A: "Vietnamese", 0x0439: "Hindi",
                0x043E: "Malay", 0x0449: "Tamil", 0x044E: "Marathi",
                0x0452: "Welsh", 0x048C: "Dari", 0x0491: "Scottish Gaelic",
            }
            layout_name = layouts.get(lid, f"Unknown (0x{lid:04X})")
            print(f"  Layout: {Colors.WHITE}{layout_name}{Colors.END}")

            ktype = ctypes.windll.user32.GetKeyboardType(0)
            ksubtype = ctypes.windll.user32.GetKeyboardType(1)
            type_names = {1: "IBM PC/XT", 2: "Olivetti", 3: "IBM PC/AT", 4: "IBM Enhanced", 5: "Nokia 1050", 6: "Nokia 9140", 7: "Japanese"}
            print(f"  Type: {Colors.GRAY}{type_names.get(ktype, f'Unknown ({ktype})')}{Colors.END}")
            print(f"  SubType: {Colors.GRAY}{ksubtype}{Colors.END}")
        except Exception as e:
            print_warning(f"Could not retrieve keyboard layout info: {e}")

        # Mouse info
        try:
            print(f"\n{Colors.BOLD}Mouse:{Colors.END}")
            buttons = ctypes.windll.user32.GetSystemMetrics(43)  # SM_CMOUSEBUTTONS
            swap = ctypes.windll.user32.GetSystemMetrics(23)     # SM_SWAPBUTTON
            print(f"  Buttons: {Colors.CYAN}{buttons}{Colors.END}")
            print(f"  Swapped: {Colors.YELLOW if swap else Colors.GREEN}{'Yes' if swap else 'No'}{Colors.END}")

            # Cursor size
            cx = ctypes.windll.user32.GetSystemMetrics(0)
            cy = ctypes.windll.user32.GetSystemMetrics(1)
            print(f"  Screen: {Colors.GRAY}{cx}x{cy}{Colors.END}")
        except Exception as e:
            print_warning(f"Could not retrieve mouse info: {e}")

        print(f"\n{Colors.BOLD}Admin Status:{Colors.END} {Colors.GREEN if is_admin() else Colors.RED}{'Yes' if is_admin() else 'No'}{Colors.END}")

        input(f"\n{Colors.GRAY}Press Enter to continue...{Colors.END}")

    def _open_logs(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if os.path.exists(log_dir):
            files = sorted([f for f in os.listdir(log_dir) if f.endswith(".log")], reverse=True)
            if files:
                latest = os.path.join(log_dir, files[0])
                print_info(f"Opening: {latest}")
                os.system(f'notepad "{latest}"')
            else:
                print_warning("No log files found")
        else:
            print_warning("Log directory does not exist yet")
        input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")


def main():
    app = ToolkitApp()
    app.run()

if __name__ == "__main__":
    main()
