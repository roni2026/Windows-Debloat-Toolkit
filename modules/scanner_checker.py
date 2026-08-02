"""
KB Toolkit - Scanner Checker Module
Diagnoses installed scanners/imaging devices, WIA service health, and drivers.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)

# Windows PnP "Imaging devices" class GUID (scanners/cameras)
IMAGE_CLASS_GUID = "{6bdd1fc6-810f-11d0-bec7-08002be2092f}"


class ScannerChecker:
    def __init__(self):
        self.devices = []
        self.issues = []

    def run(self):
        print_banner("SCANNER DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_wia_service()
        self.check_imaging_devices()
        self.check_device_manager_class()
        self.check_driver_details()
        self.check_scan_shortcuts()

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

    def check_wia_service(self):
        print_section("Windows Image Acquisition (WIA) Service")
        stdout, stderr, rc = self._run_cmd("sc query stisvc")
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state and "RUNNING" in state.upper():
                print_success(f"WIA service is {Colors.GREEN}{state.strip()}{Colors.END}")
            elif state:
                print_warning(f"WIA service state: {state.strip()}")
                print_info("WIA starts on-demand for many scanners — this may be normal when idle")
            else:
                print_warning("Could not determine WIA service state")
        else:
            print_error(f"Could not query stisvc: {stderr[:100]}")

        stdout, _, rc = self._run_cmd("sc qc stisvc")
        if rc == 0:
            start_type = self._extract_value(stdout, "START_TYPE")
            if start_type:
                print(f"  Startup Type: {Colors.GRAY}{start_type.strip()}{Colors.END}")

    def check_imaging_devices(self):
        print_section("Imaging Device Enumeration (WMI)")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "PNPClass=\'Image\' OR Name LIKE \'%Scanner%\' OR Name LIKE \'%WIA%\'" '
            'get Name, Status, Manufacturer, PNPDeviceID, ConfigManagerErrorCode /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"WMI query failed: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_warning("No scanner/imaging devices found via WMI")
            print_info("Multi-function printers often expose scanning via the printer driver instead")
            return

        for i, dev in enumerate(entries, 1):
            name = dev.get("Name", "Unknown")
            status = dev.get("Status", "Unknown")
            manufacturer = dev.get("Manufacturer", "").strip()
            err_code = dev.get("ConfigManagerErrorCode", "")

            print(f"{Colors.BOLD}Device {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
            if manufacturer:
                print(f"  Manufacturer: {Colors.GRAY}{manufacturer}{Colors.END}")
            print(f"  Status: {self._color_status(status)}")
            if err_code and err_code != "0":
                print(f"  Error Code: {Colors.RED}{err_code}{Colors.END}")
                self.issues.append(f"{name}: Error {err_code}")

            self.devices.append(dev)

    def check_device_manager_class(self):
        print_section("Device Manager - Imaging Devices Class")
        stdout, _, rc = self._run_cmd(
            f'reg query "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Class\\{IMAGE_CLASS_GUID}" /s 2>nul '
            f'| findstr /i "DriverDesc DriverDate DriverVersion"'
        )
        if rc == 0 and stdout.strip():
            print_info("Imaging class driver entries found:")
            for line in stdout.splitlines()[:15]:
                if line.strip():
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")
        else:
            print_warning("No imaging class registry entries found (no scanner installed, or driver uses a different class)")

    def check_driver_details(self):
        print_section("WIA / TWAIN Driver Files")
        driver_paths = [
            ("WIA Service DLL", r"C:\Windows\System32\wiaservc.dll"),
            ("Scanner API DLL", r"C:\Windows\System32\wiascanner.dll"),
        ]
        for name, path in driver_paths:
            if os.path.exists(path):
                print_success(f"{name} present")
            else:
                print_info(f"{name} not found at default path (may be relocated or N/A on this SKU)")

        # Check for TWAIN data source manager, common with third-party scanner software
        twain_path = r"C:\Windows\twain_32.dll"
        if os.path.exists(twain_path):
            print_success("TWAIN Data Source Manager (twain_32.dll) present")
        else:
            print_info("TWAIN Data Source Manager not found (only needed by legacy TWAIN scan apps)")

    def check_scan_shortcuts(self):
        print_section("Windows Scan App")
        stdout, _, rc = self._run_cmd(
            'powershell -NoProfile -Command "Get-AppxPackage -Name Microsoft.WindowsScan | Select-Object -ExpandProperty PackageFullName"'
        )
        if rc == 0 and stdout.strip():
            print_success(f"Windows Scan app installed: {Colors.GRAY}{stdout.strip().splitlines()[0]}{Colors.END}")
        else:
            print_info("Windows Scan app not detected (scanning may rely on manufacturer software instead)")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.devices:
            print_success(f"Detected {len(self.devices)} imaging/scanner device(s)")
        else:
            print_warning("No dedicated scanner devices detected (check multi-function printer software)")

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
        if "ok" in s or "running" in s:
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif "error" in s or "failed" in s or "degraded" in s:
            return f"{Colors.RED}{status}{Colors.END}"
        elif "warning" in s or "unknown" in s:
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    checker = ScannerChecker()
    checker.run()

if __name__ == "__main__":
    main()
