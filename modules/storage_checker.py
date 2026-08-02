"""
KB Toolkit - Storage Device Checker Module
Diagnoses storage device health, drivers, and connectivity status.

Dependency: smartmontools (smartctl.exe) is required for SMART health data.
Download: https://www.smartmontools.org/wiki/Download
Install smartctl.exe and ensure it is on PATH (or place it next to this
toolkit in a "smartmontools\\bin" folder — both locations are auto-detected).
"""
import subprocess
import shutil
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)

SMARTCTL_CANDIDATES = [
    "smartctl",
    "smartctl.exe",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smartmontools", "bin", "smartctl.exe"),
    r"C:\Program Files\smartmontools\bin\smartctl.exe",
    r"C:\Program Files (x86)\smartmontools\bin\smartctl.exe",
]


class StorageChecker:
    def __init__(self):
        self.devices = []
        self.issues = []
        self.smartctl_path = None

    def run(self):
        print_banner("STORAGE DEVICE DIAGNOSTIC SUITE", Colors.BLUE)

        self._locate_smartctl()
        self.check_device_manager()
        self.check_disk_drives_wmi()
        self.check_smart_health()
        self.check_driver_details()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=20
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def _locate_smartctl(self):
        print_section("smartmontools Dependency Check")

        found = shutil.which("smartctl") or shutil.which("smartctl.exe")
        if not found:
            for candidate in SMARTCTL_CANDIDATES:
                if os.path.isfile(candidate):
                    found = candidate
                    break

        if found:
            self.smartctl_path = found
            print_success(f"smartctl found: {Colors.WHITE}{found}{Colors.END}")
            stdout, _, rc = self._run_cmd(f'"{found}" --version')
            if rc == 0 and stdout:
                first_line = stdout.splitlines()[0] if stdout.splitlines() else ""
                print(f"  {Colors.GRAY}{first_line}{Colors.END}")
        else:
            print_error("smartctl (smartmontools) was not found on this system")
            print_warning("SMART health checks will be skipped")
            print_info("Install from: https://www.smartmontools.org/wiki/Download")
            print_info("After installing, ensure smartctl.exe is on PATH, or drop it in:")
            print_info(r"  <toolkit_folder>\smartmontools\bin\smartctl.exe")
            self.issues.append("smartmontools not installed — SMART data unavailable")

    def check_device_manager(self):
        print_section("Device Manager - Disk Drive Enumeration")
        stdout, stderr, rc = self._run_cmd(
            'wmic diskdrive get Name, Model, Status, Availability, ConfigManagerErrorCode /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for i, dev in enumerate(entries, 1):
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    err_code = dev.get("ConfigManagerErrorCode", "")

                    print(f"{Colors.BOLD}Device {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
                    print(f"  Status: {self._color_status(status)}")
                    if err_code and err_code != "0":
                        print(f"  Error Code: {Colors.RED}{err_code}{Colors.END}")
                        self.issues.append(f"Device {name}: Error {err_code}")
                    else:
                        print_success("No configuration errors")
                    self.devices.append(dev)
            else:
                print_warning("No disk drives found via WMI")
        else:
            print_error(f"WMI query failed: {stderr[:100]}")

    def check_disk_drives_wmi(self):
        print_section("Disk Drive Details")
        stdout, _, rc = self._run_cmd(
            'wmic diskdrive get Model, InterfaceType, MediaType, Size, SerialNumber, FirmwareRevision /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for dev in entries:
                model = dev.get("Model", "Unknown")
                iface = dev.get("InterfaceType", "Unknown")
                media = dev.get("MediaType", "Unknown")
                size = dev.get("Size", "")
                serial = dev.get("SerialNumber", "").strip()
                fw = dev.get("FirmwareRevision", "").strip()

                size_str = self._format_bytes(size) if size else "Unknown"

                print(f"{Colors.WHITE}{model}{Colors.END}")
                print(f"  Interface: {Colors.CYAN}{iface}{Colors.END}   Media: {Colors.GRAY}{media}{Colors.END}")
                print(f"  Size: {Colors.GRAY}{size_str}{Colors.END}")
                if serial:
                    print(f"  Serial: {Colors.GRAY}{serial}{Colors.END}")
                if fw:
                    print(f"  Firmware: {Colors.GRAY}{fw}{Colors.END}")

    def check_smart_health(self):
        print_section("SMART Health Status (smartmontools)")

        if not self.smartctl_path:
            print_warning("Skipped — smartctl not available (see dependency check above)")
            return

        stdout, stderr, rc = self._run_cmd(f'"{self.smartctl_path}" --scan')
        if rc != 0 or not stdout.strip():
            print_warning("smartctl --scan returned no devices")
            if not is_admin():
                print_info("Try re-running the toolkit as Administrator for full SMART access")
            return

        scan_lines = [l for l in stdout.splitlines() if l.strip() and not l.strip().startswith("#")]
        if not scan_lines:
            print_warning("No scannable devices reported by smartctl")
            return

        for line in scan_lines:
            dev_path = line.split()[0]
            print(f"\n{Colors.BOLD}Drive: {Colors.WHITE}{dev_path}{Colors.END}")

            h_stdout, h_stderr, h_rc = self._run_cmd(f'"{self.smartctl_path}" -H "{dev_path}"')
            if h_rc in (0, 4) and h_stdout:
                overall = self._extract_value(h_stdout, "SMART overall-health self-assessment test result") \
                    or self._extract_value(h_stdout, "SMART Health Status")
                if overall:
                    ok = "PASS" in overall.upper() or "OK" in overall.upper()
                    color = Colors.GREEN if ok else Colors.RED
                    print(f"  Health: {color}{overall.strip()}{Colors.END}")
                    if not ok:
                        self.issues.append(f"{dev_path}: SMART health check FAILED ({overall.strip()})")
                else:
                    print_info("Health status line not found in smartctl output")
            else:
                print_warning(f"Could not read SMART health for {dev_path}")
                if h_stderr:
                    print(f"  {Colors.GRAY}{h_stderr.strip()[:150]}{Colors.END}")

            a_stdout, _, a_rc = self._run_cmd(f'"{self.smartctl_path}" -A "{dev_path}"')
            if a_rc == 0 and a_stdout:
                key_attrs = ["Reallocated_Sector_Ct", "Current_Pending_Sector", "Reallocated_Event_Count",
                             "Power_On_Hours", "Temperature_Celsius", "Wear_Leveling_Count",
                             "Media_Wearout_Indicator", "Percentage Used"]
                for line in a_stdout.splitlines():
                    for attr in key_attrs:
                        if attr in line:
                            parts = line.split()
                            if parts:
                                print(f"  {Colors.GRAY}{attr:26}{Colors.END}: {Colors.WHITE}{parts[-1]}{Colors.END}")

    def check_driver_details(self):
        print_section("Storage Driver / Service Status")
        for svc in ("disk", "partmgr", "volmgr", "storahci", "stornvme"):
            stdout, _, rc = self._run_cmd(f"sc query {svc}")
            if rc == 0:
                state = self._extract_value(stdout, "STATE")
                if state:
                    color = Colors.GREEN if "RUNNING" in state.upper() else Colors.YELLOW
                    print(f"  {Colors.GRAY}{svc:12}{Colors.END}: {color}{state.strip()}{Colors.END}")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.devices:
            print_success(f"Detected {len(self.devices)} storage device(s)")
        else:
            print_error("No storage devices detected!")

        if not self.smartctl_path:
            print_warning("smartmontools not installed — install it for full SMART diagnostics")

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

    def _extract_value(self, text, key):
        for line in text.splitlines():
            if key in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _color_status(self, status):
        s = status.lower() if status else ""
        if "ok" in s:
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif "error" in s or "failed" in s or "degraded" in s or "bad" in s:
            return f"{Colors.RED}{status}{Colors.END}"
        elif "warning" in s or "unknown" in s:
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"

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
    checker = StorageChecker()
    checker.run()

if __name__ == "__main__":
    main()
