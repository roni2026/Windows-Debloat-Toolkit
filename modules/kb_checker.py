"""
KB Toolkit - Keyboard Checker Module
Diagnoses keyboard hardware, drivers, and connectivity status.
"""
import subprocess
import re
import ctypes
import ctypes.wintypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, 
    print_error, print_warning, print_info, is_admin, prompt_continue
)

class KeyboardChecker:
    def __init__(self):
        self.devices = []
        self.issues = []

    def run(self):
        print_banner("KEYBOARD DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_device_manager()
        self.check_wmi_keyboard()
        self.check_raw_input_devices()
        self.check_driver_details()
        self.check_hid_status()
        self.check_usb_controllers()
        self.check_power_management()
        self.check_filter_drivers()

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

    def check_device_manager(self):
        print_section("Device Manager - Keyboard Enumeration")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_Keyboard get Name, Description, Status, Availability, ConfigManagerErrorCode /FORMAT:LIST'
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
                        print(f"  Error Code: {Colors.RED}{err_code} - {self._cm_error_desc(err_code)}{Colors.END}")
                        self.issues.append(f"Device {name}: Error {err_code}")
                    else:
                        print_success("No configuration errors")
                    self.devices.append(dev)
            else:
                print_warning("No keyboard devices found via WMI")
        else:
            print_error(f"WMI query failed: {stderr[:100]}")

    def check_wmi_keyboard(self):
        print_section("WMI Deep Inspection")
        queries = [
            ("Layout", 'wmic path Win32_Keyboard get Layout /FORMAT:LIST'),
            ("PNP Device ID", 'wmic path Win32_Keyboard get PNPDeviceID /FORMAT:LIST'),
            ("Number of Function Keys", 'wmic path Win32_Keyboard get NumberOfFunctionKeys /FORMAT:LIST'),
            ("Password", 'wmic path Win32_Keyboard get Password /FORMAT:LIST'),
            ("Is Locked", 'wmic path Win32_Keyboard get IsLocked /FORMAT:LIST'),
        ]
        for label, cmd in queries:
            stdout, _, rc = self._run_cmd(cmd)
            if rc == 0:
                val = self._extract_wmic_value(stdout)
                if val:
                    print(f"  {Colors.GRAY}{label:25}{Colors.END}: {Colors.WHITE}{val}{Colors.END}")

    def check_raw_input_devices(self):
        print_section("Raw Input Device Registry")
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\kbdhid\Parameters" /s 2>nul'
        )
        if rc == 0 and stdout:
            print_info("KbdHid Parameters found")
            for line in stdout.splitlines():
                if line.strip() and not line.startswith("HKEY"):
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")
        else:
            print_warning("Could not read kbdhid parameters")

        # Check for keyboard class devices
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E96B-E325-11CE-BFC1-08002BE10318}" /s 2>nul | findstr /i "DriverDesc DriverDate DriverVersion"'
        )
        if rc == 0 and stdout:
            print_info("Keyboard Class Driver Details:")
            for line in stdout.splitlines()[:10]:
                if line.strip():
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")

    def check_driver_details(self):
        print_section("Driver File Analysis")
        driver_files = [
            ("Keyboard Class Driver", "C:\Windows\System32\drivers\kbdclass.sys"),
            ("HID Keyboard Driver", "C:\Windows\System32\drivers\kbdhid.sys"),
            ("Legacy Keyboard Driver", "C:\Windows\System32\drivers\i8042prt.sys"),
        ]

        for name, path in driver_files:
            if os.path.exists(path):
                try:
                    stat = os.stat(path)
                    from datetime import datetime
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    size_kb = stat.st_size / 1024

                    # Try to get version info
                    ver = self._get_file_version(path)
                    ver_str = f" v{ver}" if ver else ""

                    print(f"{Colors.GREEN}✓{Colors.END} {Colors.WHITE}{name}{Colors.END}{Colors.CYAN}{ver_str}{Colors.END}")
                    print(f"    Path: {Colors.GRAY}{path}{Colors.END}")
                    print(f"    Size: {Colors.GRAY}{size_kb:.1f} KB{Colors.END}")
                    print(f"    Last Modified: {Colors.GRAY}{mtime}{Colors.END}")
                except Exception as e:
                    print_warning(f"Could not inspect {name}: {e}")
            else:
                print_error(f"{name} not found at expected path")
                self.issues.append(f"Missing driver: {name}")

    def check_hid_status(self):
        print_section("HID Service Status")
        stdout, _, rc = self._run_cmd('sc query kbdhid')
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state and "RUNNING" in state.upper():
                print_success(f"KbdHid service is {Colors.GREEN}{state.strip()}{Colors.END}")
            else:
                print_warning(f"KbdHid service state: {state}")
                self.issues.append("KbdHid service not running properly")

        stdout, _, rc = self._run_cmd('sc query kbdclass')
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state and "RUNNING" in state.upper():
                print_success(f"KbdClass service is {Colors.GREEN}{state.strip()}{Colors.END}")
            else:
                print_warning(f"KbdClass service state: {state}")

    def check_usb_controllers(self):
        print_section("USB Root Hubs (Keyboard Connectivity)")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_USBHub WHERE "Name LIKE \'%Keyboard%\' OR Name LIKE \'%HID%\'" get Name, Status, PNPDeviceID /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {self._color_status(status)}")
            else:
                print_info("No dedicated USB keyboard hubs detected (may be internal)")

        # Check for USB keyboard specifically
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Keyboard%\'" get Name, Status, Manufacturer, PNPDeviceID /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for dev in entries:
                name = dev.get("Name", "Unknown")
                mfr = dev.get("Manufacturer", "Unknown")
                status = dev.get("Status", "Unknown")
                pnp = dev.get("PNPDeviceID", "")
                print(f"\n{Colors.BOLD}PnP Device:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
                print(f"  Manufacturer: {Colors.GRAY}{mfr}{Colors.END}")
                print(f"  Status: {self._color_status(status)}")
                if pnp:
                    print(f"  PNP ID: {Colors.GRAY}{pnp}{Colors.END}")

    def check_power_management(self):
        print_section("Power Management Settings")
        stdout, _, rc = self._run_cmd(
            'powercfg /devicequery wake_armed'
        )
        if rc == 0:
            devices = [d.strip() for d in stdout.splitlines() if d.strip()]
            kb_wake = [d for d in devices if "keyboard" in d.lower() or "hid" in d.lower()]
            if kb_wake:
                print_success("Keyboard can wake system from sleep:")
                for d in kb_wake:
                    print(f"  {Colors.GREEN}• {d}{Colors.END}")
            else:
                print_warning("No keyboard devices are wake-armed")

        # Check USB selective suspend
        stdout, _, rc = self._run_cmd(
            'powercfg /query SCHEME_CURRENT SUB_USBHubs USBHUB_IDLE 2>nul'
        )
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                if "Current AC Power Setting Index" in line or "Current DC Power Setting Index" in line:
                    val = line.split(":")[-1].strip()
                    try:
                        num = int(val, 16)
                        status = f"{Colors.RED}Enabled (may cause disconnects){Colors.END}" if num else f"{Colors.GREEN}Disabled{Colors.END}"
                        print(f"  USB Selective Suspend: {status}")
                    except:
                        pass

    def check_filter_drivers(self):
        print_section("Upper/Lower Filter Drivers")
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E96B-E325-11CE-BFC1-08002BE10318}" /v UpperFilters 2>nul'
        )
        if rc == 0 and stdout:
            val = self._extract_reg_value(stdout, "UpperFilters")
            if val:
                print_info(f"Upper Filters: {Colors.YELLOW}{val}{Colors.END}")
            else:
                print_info("No upper filter drivers")

        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E96B-E325-11CE-BFC1-08002BE10318}" /v LowerFilters 2>nul'
        )
        if rc == 0 and stdout:
            val = self._extract_reg_value(stdout, "LowerFilters")
            if val:
                print_info(f"Lower Filters: {Colors.YELLOW}{val}{Colors.END}")
            else:
                print_info("No lower filter drivers")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.devices:
            print_success(f"Detected {len(self.devices)} keyboard device(s)")
        else:
            print_error("No keyboard devices detected!")

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

    def _extract_wmic_value(self, text):
        for line in text.splitlines():
            if "=" in line and not line.startswith("\r\n"):
                return line.split("=", 1)[1].strip()
        return None

    def _extract_value(self, text, key):
        for line in text.splitlines():
            if key in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _extract_reg_value(self, text, value_name):
        for line in text.splitlines():
            if value_name in line:
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    return parts[2].strip()
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

    def _cm_error_desc(self, code):
        codes = {
            "0": "Device is working properly",
            "1": "Device is not configured correctly",
            "2": "Windows cannot load the driver",
            "3": "Driver might be corrupted",
            "4": "Device is not working properly",
            "5": "Driver could not be loaded",
            "6": "Problem with device bootloader",
            "7": "Filtered",
            "8": "Driver loader for device is missing",
            "9": "Device is not working properly (firmware)",
            "10": "Device cannot start",
            "12": "Device cannot find enough free resources",
            "14": "Device cannot work properly until restart",
            "16": "Windows cannot identify all resources",
            "18": "Reinstall drivers",
            "19": "Windows cannot start this hardware",
            "21": "Windows is removing this device",
            "22": "Device is disabled",
            "24": "Device is not present / not working properly",
            "28": "Drivers for this device are not installed",
            "29": "Device is disabled (firmware)",
            "31": "This device is not working properly",
            "32": "Driver (service) for this device has been disabled",
            "33": "Windows cannot determine which resources are required",
            "34": "Windows cannot determine the settings for this device",
            "35": "Your computer's system firmware does not include enough information",
            "36": "This device is requesting a PCI interrupt but is configured for ISA",
            "37": "Windows cannot initialize the device driver for this hardware",
            "38": "Windows cannot load the device driver",
            "39": "Windows cannot load the device driver (missing or corrupted)",
            "40": "Windows cannot access this hardware",
            "41": "Windows successfully loaded the device driver but cannot find the hardware",
            "42": "Windows cannot load the device driver (duplicate device)",
            "43": "Windows has stopped this device because it has reported problems",
            "44": "An application or service has shut down this hardware device",
            "45": "Currently, this hardware device is not connected to the computer",
            "46": "Windows cannot gain access to this hardware device",
            "47": "Windows cannot use this hardware device",
            "48": "The software for this device has been blocked",
            "49": "Windows cannot start new hardware devices",
            "50": "Windows cannot apply all of the properties for this device",
            "51": "This device is currently waiting on another device",
            "52": "Windows cannot verify the digital signature",
        }
        return codes.get(str(code), "Unknown error")

    def _get_file_version(self, filepath):
        try:
            wapi = ctypes.windll.version
            size = wapi.GetFileVersionInfoSizeW(filepath, None)
            if size == 0:
                return None
            buf = ctypes.create_string_buffer(size)
            wapi.GetFileVersionInfoW(filepath, 0, size, buf)

            ulen = ctypes.c_uint()
            uptr = ctypes.c_void_p()
            wapi.VerQueryValueW(buf, r"\VarFileInfo\Translation", ctypes.byref(uptr), ctypes.byref(ulen))
            if ulen.value == 0:
                return None

            lang = ctypes.cast(uptr, ctypes.POINTER(ctypes.c_uint32)).contents.value
            lang_str = f"{lang & 0xFFFF:04x}{lang >> 16:04x}"

            wapi.VerQueryValueW(buf, f"\StringFileInfo\{lang_str}\FileVersion", ctypes.byref(uptr), ctypes.byref(ulen))
            if ulen.value > 0:
                return ctypes.wstring_at(uptr.value)
        except Exception:
            pass
        return None


def main():
    checker = KeyboardChecker()
    checker.run()

if __name__ == "__main__":
    main()
