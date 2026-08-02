"""
KB Toolkit - RAM Checker Module
Diagnoses installed memory modules, capacity, speed, and current load.
"""
import subprocess
import ctypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)

FORM_FACTORS = {
    "0": "Unknown", "1": "Other", "2": "SIP", "3": "DIP", "4": "ZIP",
    "5": "SOJ", "6": "Proprietary", "7": "SIMM", "8": "DIMM", "9": "TSOP",
    "10": "PGA", "11": "RIMM", "12": "SODIMM", "13": "SRIMM", "14": "SMD",
    "15": "SSMP", "16": "QFP", "17": "TQFP", "18": "SOIC", "19": "LCC",
    "20": "PLCC", "21": "BGA", "22": "FPBGA", "23": "LGA",
}

MEMORY_TYPES = {
    "0": "Unknown", "1": "Other", "2": "DRAM", "3": "Synchronous DRAM",
    "4": "Cache DRAM", "5": "EDO", "6": "EDRAM", "7": "VRAM", "8": "SRAM",
    "9": "RAM", "10": "ROM", "11": "Flash", "12": "EEPROM", "13": "FEPROM",
    "14": "EPROM", "15": "CDRAM", "16": "3DRAM", "17": "SDRAM", "18": "SGRAM",
    "19": "RDRAM", "20": "DDR", "21": "DDR2", "22": "DDR2 FB-DIMM",
    "24": "DDR3", "25": "FBD2", "26": "DDR4", "34": "DDR5",
}


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class RamChecker:
    def __init__(self):
        self.modules = []
        self.issues = []

    def run(self):
        print_banner("RAM DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_current_usage()
        self.check_physical_modules()
        self.check_memory_array()
        self.check_page_file()
        self.check_windows_memory_diagnostic()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=15
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def check_current_usage(self):
        print_section("Current Memory Usage")
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            used_gb = total_gb - avail_gb
            load = stat.dwMemoryLoad

            print(f"  Total Physical:  {Colors.WHITE}{total_gb:.2f} GB{Colors.END}")
            print(f"  In Use:          {Colors.WHITE}{used_gb:.2f} GB{Colors.END}")
            print(f"  Available:       {Colors.WHITE}{avail_gb:.2f} GB{Colors.END}")

            load_color = Colors.GREEN if load < 70 else (Colors.YELLOW if load < 90 else Colors.RED)
            print(f"  Memory Load:     {load_color}{load}%{Colors.END}")
            if load >= 90:
                self.issues.append(f"High memory load: {load}%")

            total_page_gb = stat.ullTotalPageFile / (1024 ** 3)
            avail_page_gb = stat.ullAvailPageFile / (1024 ** 3)
            print(f"  Page File Total: {Colors.GRAY}{total_page_gb:.2f} GB{Colors.END}")
            print(f"  Page File Free:  {Colors.GRAY}{avail_page_gb:.2f} GB{Colors.END}")
        except Exception as e:
            print_error(f"Could not read memory status: {e}")

    def check_physical_modules(self):
        print_section("Physical Memory Modules")
        stdout, stderr, rc = self._run_cmd(
            'wmic memorychip get BankLabel, DeviceLocator, Capacity, Speed, Manufacturer, '
            'PartNumber, SerialNumber, MemoryType, FormFactor, ConfiguredClockSpeed /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"WMI query failed: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_warning("No memory modules reported by WMI")
            return

        total_capacity = 0
        for i, mod in enumerate(entries, 1):
            bank = mod.get("BankLabel", "Unknown").strip()
            slot = mod.get("DeviceLocator", "Unknown").strip()
            capacity = mod.get("Capacity", "")
            speed = mod.get("Speed", "").strip()
            configured_speed = mod.get("ConfiguredClockSpeed", "").strip()
            manufacturer = mod.get("Manufacturer", "Unknown").strip()
            part_number = mod.get("PartNumber", "").strip()
            serial = mod.get("SerialNumber", "").strip()
            mem_type = MEMORY_TYPES.get(mod.get("MemoryType", "").strip(), "Unknown")
            form_factor = FORM_FACTORS.get(mod.get("FormFactor", "").strip(), "Unknown")

            cap_str = self._format_bytes(capacity) if capacity else "Empty"
            if capacity:
                try:
                    total_capacity += int(capacity)
                except ValueError:
                    pass

            print(f"{Colors.BOLD}Slot {i} ({slot}):{Colors.END} {Colors.WHITE}{cap_str}{Colors.END}")
            print(f"  Bank: {Colors.GRAY}{bank}{Colors.END}   Type: {Colors.CYAN}{mem_type}{Colors.END}   Form Factor: {Colors.GRAY}{form_factor}{Colors.END}")
            if speed:
                spd_line = f"  Rated Speed: {Colors.GRAY}{speed} MT/s{Colors.END}"
                if configured_speed and configured_speed != "0":
                    running_color = Colors.YELLOW if configured_speed != speed else Colors.GREEN
                    spd_line += f"   Running At: {running_color}{configured_speed} MT/s{Colors.END}"
                    if configured_speed != speed:
                        self.issues.append(
                            f"Slot {slot}: running below rated speed ({configured_speed} vs {speed} MT/s)"
                        )
                print(spd_line)
            if manufacturer and manufacturer.lower() != "unknown":
                print(f"  Manufacturer: {Colors.WHITE}{manufacturer}{Colors.END}   Part #: {Colors.GRAY}{part_number or 'N/A'}{Colors.END}")
            if serial:
                print(f"  Serial: {Colors.GRAY}{serial}{Colors.END}")

            self.modules.append(mod)

        if total_capacity:
            print(f"\n  {Colors.BOLD}Total Installed:{Colors.END} {Colors.WHITE}{self._format_bytes(str(total_capacity))}{Colors.END}")

        # Mixed-speed warning across populated modules
        speeds = {m.get("Speed", "").strip() for m in entries if m.get("Capacity")}
        speeds.discard("")
        if len(speeds) > 1:
            self.issues.append(f"Mismatched module speeds detected: {', '.join(sorted(speeds))} MT/s")

    def check_memory_array(self):
        print_section("Memory Array Capacity")
        stdout, _, rc = self._run_cmd(
            'wmic memphysical get MaxCapacity, MemoryDevices /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for arr in entries:
                max_cap = arr.get("MaxCapacity", "")
                slots = arr.get("MemoryDevices", "")
                if max_cap:
                    try:
                        max_gb = int(max_cap) / (1024 ** 2)
                        print(f"  Max Supported: {Colors.WHITE}{max_gb:.0f} GB{Colors.END}")
                    except ValueError:
                        pass
                if slots:
                    populated = len([m for m in self.modules if m.get("Capacity")])
                    print(f"  Slots: {Colors.GRAY}{populated} populated / {slots} total{Colors.END}")

    def check_page_file(self):
        print_section("Page File Configuration")
        stdout, _, rc = self._run_cmd(
            'wmic pagefile get Name, CurrentUsage, AllocatedBaseSize /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for pf in entries:
                    name = pf.get("Name", "Unknown")
                    size = pf.get("AllocatedBaseSize", "")
                    usage = pf.get("CurrentUsage", "")
                    print(f"  {Colors.WHITE}{name}{Colors.END}: {Colors.GRAY}{size} MB allocated, {usage} MB in use{Colors.END}")
            else:
                print_info("No dedicated page file entries (may be system-managed)")

    def check_windows_memory_diagnostic(self):
        print_section("Windows Memory Diagnostic Tool")
        path = r"C:\Windows\System32\MdSched.exe"
        if os.path.exists(path):
            print_success("Windows Memory Diagnostic (MdSched.exe) is available")
            print_info("Run 'mdsched.exe' and choose 'Restart now' to test RAM for errors")
        else:
            print_warning("MdSched.exe not found at the expected path")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        populated = [m for m in self.modules if m.get("Capacity")]
        if populated:
            print_success(f"Detected {len(populated)} populated memory module(s)")
        else:
            print_error("No populated memory modules detected!")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No critical issues detected")

        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")

    def _parse_wmic_list(self, text):
        entries = []
        current = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                if current:
                    entries.append(current)
                    current = {}
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                current[k.strip()] = v.strip()
        if current:
            entries.append(current)
        return entries

    def _format_bytes(self, size_str):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            return size_str
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


def main():
    checker = RamChecker()
    checker.run()

if __name__ == "__main__":
    main()
