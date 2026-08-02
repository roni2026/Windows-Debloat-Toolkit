"""
Mouse & Trackpad Toolkit - Diagnostic Module
Comprehensive hardware, driver, and settings analysis.
"""
import subprocess
import re
import ctypes
import ctypes.wintypes
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mouse_utils import (
    Colors, MouseColors, print_mouse_banner, print_section, print_success, 
    print_error, print_warning, print_info, is_admin, prompt_continue, get_vendor_from_pnp
)

class MouseChecker:
    def __init__(self):
        self.devices = []
        self.issues = []
        self.is_ptp = False
        self.trackpad_vendor = None

    def run(self):
        print_mouse_banner("MOUSE & TRACKPAD DIAGNOSTIC SUITE")

        self.check_device_manager()
        self.check_precision_touchpad()
        self.check_driver_details()
        self.check_hid_services()
        self.check_usb_mice()
        self.check_pointer_settings()
        self.check_trackpad_registry()
        self.check_power_management()
        self.check_wireless_status()
        self.check_raw_input()
        self.check_filter_drivers()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True, timeout=15):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def check_device_manager(self):
        print_section("Device Manager - Pointing Devices")

        # WMI Pointing Device query
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PointingDevice get Name, Description, Status, PNPDeviceID, Manufacturer, NumberOfButtons, Handedness /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for i, dev in enumerate(entries, 1):
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    pnp = dev.get("PNPDeviceID", "")
                    mfr = dev.get("Manufacturer", "Unknown")
                    buttons = dev.get("NumberOfButtons", "?")
                    handed = dev.get("Handedness", "?")

                    vendor = get_vendor_from_pnp(pnp) if pnp else mfr
                    if "touchpad" in name.lower() or "trackpad" in name.lower():
                        self.trackpad_vendor = vendor

                    print(f"{Colors.BOLD}Device {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
                    print(f"  Vendor: {Colors.GRAY}{vendor}{Colors.END}")
                    print(f"  Status: {self._color_status(status)}")
                    print(f"  Buttons: {Colors.GRAY}{buttons}{Colors.END}")
                    if handed and handed != "?":
                        print(f"  Handedness: {Colors.GRAY}{handed}{Colors.END}")
                    if pnp:
                        print(f"  PNP ID: {Colors.GRAY}{pnp}{Colors.END}")

                    if "error" in status.lower() or "degraded" in status.lower():
                        self.issues.append(f"Device {name}: {status}")

                    self.devices.append(dev)
            else:
                print_warning("No pointing devices found via WMI")
        else:
            print_error("WMI query failed")

        # Also check PnP entities specifically for mouse
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Mouse%\' OR Name LIKE \'%Touchpad%\' OR Name LIKE \'%Trackpad%\' OR Name LIKE \'%Pointing%\' OR Name LIKE \'%HID-compliant%\'" get Name, Status, Manufacturer, PNPDeviceID /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for dev in entries:
                name = dev.get("Name", "")
                if any(x in name.lower() for x in ["mouse", "touchpad", "trackpad", "pointing"]):
                    status = dev.get("Status", "Unknown")
                    mfr = dev.get("Manufacturer", "Unknown")
                    pnp = dev.get("PNPDeviceID", "")
                    print(f"\n{Colors.BOLD}PnP:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
                    print(f"  Mfr: {Colors.GRAY}{mfr}{Colors.END} | Status: {self._color_status(status)}")
                    if pnp and "HID" in pnp.upper():
                        print(f"  {Colors.CYAN}HID Device detected{Colors.END}")

    def check_precision_touchpad(self):
        print_section("Precision Touchpad (PTP) Detection")

        # Check registry for PTP
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad" /s 2>nul'
        )
        if rc == 0 and stdout.strip():
            self.is_ptp = True
            print_success("Precision Touchpad detected!")
            for line in stdout.splitlines():
                line = line.strip()
                if line and not line.startswith("HKEY") and "REG_" in line:
                    print(f"  {Colors.GRAY}{line}{Colors.END}")
        else:
            print_info("No Precision Touchpad registry entries found")
            print_info("This may be a legacy Synaptics/Elan/Alps trackpad")

        # Check for PTP status
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status" /v Enabled 2>nul'
        )
        if rc == 0 and stdout.strip():
            val = self._extract_reg_value(stdout, "Enabled")
            if val:
                status = f"{Colors.GREEN}Enabled{Colors.END}" if val == "0x1" else f"{Colors.RED}Disabled{Colors.END}"
                print(f"  PTP Status: {status}")

        # Check Windows Settings for touchpad
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad" /s 2>nul'
        )
        if rc == 0 and stdout.strip():
            print_info("User PTP settings found:")
            for line in stdout.splitlines()[:15]:
                if line.strip() and "REG_" in line:
                    print(f"    {Colors.GRAY}{line.strip()}{Colors.END}")

    def check_driver_details(self):
        print_section("Driver File Analysis")

        driver_files = [
            ("Mouse Class Driver", "C:\Windows\System32\drivers\mouclass.sys"),
            ("HID Mouse Driver", "C:\Windows\System32\drivers\mouhid.sys"),
            ("PS/2 Mouse Driver", "C:\Windows\System32\drivers\mouclass.sys"),
            ("I2C HID Driver", "C:\Windows\System32\drivers\i2chid.sys"),
            ("I2C Controller", "C:\Windows\System32\drivers\iai2c.sys"),
            ("USB HID Driver", "C:\Windows\System32\drivers\hidusb.sys"),
        ]

        # Check for vendor-specific drivers
        vendor_drivers = [
            ("Synaptics", "C:\Windows\System32\drivers\SynTP.sys"),
            ("Elan", "C:\Windows\System32\drivers\ETD.sys"),
            ("Alps", "C:\Windows\System32\drivers\Apfiltr.sys"),
            ("Cypress", "C:\Windows\System32\drivers\Cytp2k.sys"),
        ]

        for name, path in driver_files:
            self._inspect_driver(name, path)

        print(f"\n{Colors.BOLD}Vendor-Specific Drivers:{Colors.END}")
        vendor_found = False
        for name, path in vendor_drivers:
            if os.path.exists(path):
                vendor_found = True
                self._inspect_driver(name, path)

        if not vendor_found:
            print_info("No vendor-specific trackpad drivers found (using generic HID)")

    def _inspect_driver(self, name, path):
        if os.path.exists(path):
            try:
                stat = os.stat(path)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_kb = stat.st_size / 1024
                ver = self._get_file_version(path)
                ver_str = f" v{ver}" if ver else ""

                print(f"{Colors.GREEN}✓{Colors.END} {Colors.WHITE}{name}{Colors.END}{MouseColors.ORANGE}{ver_str}{Colors.END}")
                print(f"    Path: {Colors.GRAY}{path}{Colors.END}")
                print(f"    Size: {Colors.GRAY}{size_kb:.1f} KB{Colors.END}")
                print(f"    Modified: {Colors.GRAY}{mtime}{Colors.END}")
            except Exception as e:
                print_warning(f"Could not inspect {name}: {e}")
        else:
            print(f"  {Colors.GRAY}○ {name} not found at {path}{Colors.END}")

    def check_hid_services(self):
        print_section("HID & Mouse Services")

        services = ["mouhid", "mouclass", "hidserv", "TabletInputService"]
        for svc in services:
            stdout, _, rc = self._run_cmd(f'sc query {svc}')
            if rc == 0:
                state = self._extract_value(stdout, "STATE")
                if state:
                    color = Colors.GREEN if "RUNNING" in state.upper() else Colors.YELLOW
                    print(f"  {svc:<20} {color}{state}{Colors.END}")
            else:
                print(f"  {Colors.GRAY}{svc:<20} Not installed{Colors.END}")

    def check_usb_mice(self):
        print_section("USB Mouse Connectivity")

        stdout, _, rc = self._run_cmd(
            'wmic path Win32_USBHub WHERE "Name LIKE \'%Mouse%\' OR Name LIKE \'%HID%\' OR Name LIKE \'%Logitech%\' OR Name LIKE \'%Razer%\'" get Name, Status, PNPDeviceID /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {self._color_status(status)}")

        # Check for USB selective suspend on hubs
        stdout, _, rc = self._run_cmd(
            'powercfg /devicequery wake_armed'
        )
        if rc == 0:
            devices = [d.strip() for d in stdout.splitlines() if d.strip()]
            mouse_wake = [d for d in devices if any(x in d.lower() for x in ["mouse", "hid", "usb"])]
            if mouse_wake:
                print_success("Mouse can wake system from sleep:")
                for d in mouse_wake:
                    print(f"  {Colors.GREEN}• {d}{Colors.END}")
            else:
                print_info("No mouse devices are wake-armed")

    def check_pointer_settings(self):
        print_section("Pointer Settings (Registry)")

        settings_queries = [
            ("MouseSpeed", "HKCU\Control Panel\Mouse", "MouseSpeed"),
            ("MouseThreshold1", "HKCU\Control Panel\Mouse", "MouseThreshold1"),
            ("MouseThreshold2", "HKCU\Control Panel\Mouse", "MouseThreshold2"),
            ("MouseSensitivity", "HKCU\Control Panel\Mouse", "MouseSensitivity"),
            ("SwapMouseButtons", "HKCU\Control Panel\Mouse", "SwapMouseButtons"),
            ("DoubleClickSpeed", "HKCU\Control Panel\Mouse", "DoubleClickSpeed"),
            ("MouseTrails", "HKCU\Control Panel\Mouse", "MouseTrails"),
            ("SnapToDefaultButton", "HKCU\Control Panel\Mouse", "SnapToDefaultButton"),
            ("SmoothMouseXCurve", "HKCU\Control Panel\Mouse", "SmoothMouseXCurve"),
            ("SmoothMouseYCurve", "HKCU\Control Panel\Mouse", "SmoothMouseYCurve"),
        ]

        for label, path, value in settings_queries:
            stdout, _, rc = self._run_cmd(f'reg query "{path}" /v {value} 2>nul')
            if rc == 0:
                val = self._extract_reg_value(stdout, value)
                if val:
                    # Interpret some values
                    interp = ""
                    if label == "MouseSpeed" and val == "1":
                        interp = f" {Colors.YELLOW}(Enhance pointer precision ON){Colors.END}"
                    elif label == "SwapMouseButtons" and val == "1":
                        interp = f" {Colors.YELLOW}(Left/Right swapped){Colors.END}"
                    elif label == "SnapToDefaultButton" and val == "1":
                        interp = f" {Colors.YELLOW}(SnapTo enabled){Colors.END}"
                    elif label == "MouseSensitivity":
                        interp = f" {Colors.GRAY}(1-20 scale){Colors.END}"

                    print(f"  {Colors.GRAY}{label:<20}{Colors.END}: {Colors.WHITE}{val}{Colors.END}{interp}")

    def check_trackpad_registry(self):
        print_section("Trackpad-Specific Settings")

        if self.is_ptp:
            # PTP settings
            settings = [
                ("CursorSpeed", "HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\CursorSpeed"),
                ("ScrollDirection", "HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\ScrollDirection"),
                ("ThreeFingerTapEnabled", "HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\ThreeFingerTapEnabled"),
                ("FourFingerTapEnabled", "HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\FourFingerTapEnabled"),
                ("EdgeGesture", "HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\EdgeGesture"),
            ]
            for label, path in settings:
                stdout, _, rc = self._run_cmd(f'reg query "{path}" 2>nul')
                if rc == 0:
                    val = self._extract_reg_value(stdout, os.path.basename(path))
                    if val:
                        print(f"  {Colors.GRAY}{label:<25}{Colors.END}: {Colors.WHITE}{val}{Colors.END}")

        # Legacy trackpad settings
        legacy_paths = [
            ("Synaptics", "HKLM\SOFTWARE\Synaptics\SynTP\Install"),
            ("Elan", "HKLM\SOFTWARE\Elantech"),
            ("Alps", "HKLM\SOFTWARE\Alps\Apoint"),
        ]

        for name, path in legacy_paths:
            stdout, _, rc = self._run_cmd(f'reg query "{path}" /s 2>nul | findstr /i "version driver"')
            if rc == 0 and stdout.strip():
                print_info(f"{name} driver registry found:")
                for line in stdout.splitlines()[:5]:
                    if line.strip():
                        print(f"    {Colors.GRAY}{line.strip()}{Colors.END}")

        # Check if trackpad is disabled via function key
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\ActionCenter\Quick Actions\All\QuickActions.StateChange\Toggles\Toggles\Toggles\Toggles" /s 2>nul | findstr /i "touchpad"'
        )
        # Also check airplane mode / device disable
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Touchpad%\' OR Name LIKE \'%Trackpad%\'" get Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            if "error" in stdout.lower() or "disabled" in stdout.lower():
                print_warning("Trackpad may be disabled!")
                self.issues.append("Trackpad appears disabled in Device Manager")

    def check_power_management(self):
        print_section("Power Management")

        # USB selective suspend
        stdout, _, rc = self._run_cmd('powercfg /query SCHEME_CURRENT SUB_USBHubs 2>nul')
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                if "Current AC Power Setting" in line or "Current DC Power Setting" in line:
                    val = line.split(":")[-1].strip()
                    try:
                        num = int(val, 16)
                        status = f"{Colors.RED}Enabled (may cause disconnects){Colors.END}" if num else f"{Colors.GREEN}Disabled{Colors.END}"
                        print(f"  USB Selective Suspend: {status}")
                    except:
                        pass

        # Check mouse power settings
        stdout, _, rc = self._run_cmd('powercfg /query SCHEME_CURRENT SUB_MOUSE 2>nul')
        if rc == 0 and stdout:
            print_info("Mouse power settings found")

    def check_wireless_status(self):
        print_section("Wireless Mouse Status")

        # Try to find battery info via WMI
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_Battery get EstimatedChargeRemaining, BatteryStatus, Name /FORMAT:LIST 2>nul'
        )
        if rc == 0 and stdout.strip() and "Name" in stdout:
            entries = self._parse_wmic_list(stdout)
            for bat in entries:
                name = bat.get("Name", "Unknown")
                charge = bat.get("EstimatedChargeRemaining", "?")
                status = bat.get("BatteryStatus", "?")
                print(f"  {Colors.WHITE}{name}{Colors.END}")
                print(f"    Charge: {Colors.CYAN}{charge}%{Colors.END}")
                print(f"    Status: {Colors.GRAY}{status}{Colors.END}")
        else:
            print_info("No wireless mouse battery info available via WMI")

        # Check for Bluetooth mice
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Bluetooth%\' AND Name LIKE \'%Mouse%\'" get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                print_success("Bluetooth mouse detected:")
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Unknown')}{Colors.END}")

    def check_raw_input(self):
        print_section("Raw Input Device Enumeration")

        # Check GetRawInputDeviceList indirectly via registry
        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\mouhid\Parameters" /s 2>nul'
        )
        if rc == 0 and stdout.strip():
            print_info("MouHid Parameters:")
            for line in stdout.splitlines():
                if line.strip() and not line.startswith("HKEY"):
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")

        # Check for multiple mice
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PointingDevice get Name /FORMAT:CSV | find /c /v ""'
        )
        if rc == 0:
            try:
                count = int(stdout.strip()) - 1  # minus header
                if count > 1:
                    print_warning(f"Multiple pointing devices detected ({count})")
                    print_info("This can cause cursor jumping or conflicts")
                    self.issues.append(f"Multiple pointing devices: {count} detected")
                else:
                    print_success(f"Single pointing device detected")
            except:
                pass

    def check_filter_drivers(self):
        print_section("Upper/Lower Filter Drivers")

        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E96F-E325-11CE-BFC1-08002BE10318}" /v UpperFilters 2>nul'
        )
        if rc == 0 and stdout:
            val = self._extract_reg_value(stdout, "UpperFilters")
            if val:
                print_info(f"Mouse Upper Filters: {Colors.YELLOW}{val}{Colors.END}")
            else:
                print_info("No upper filter drivers")

        stdout, _, rc = self._run_cmd(
            'reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Class\{4D36E96F-E325-11CE-BFC1-08002BE10318}" /v LowerFilters 2>nul'
        )
        if rc == 0 and stdout:
            val = self._extract_reg_value(stdout, "LowerFilters")
            if val:
                print_info(f"Mouse Lower Filters: {Colors.YELLOW}{val}{Colors.END}")
            else:
                print_info("No lower filter drivers")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.devices:
            print_success(f"Detected {len(self.devices)} pointing device(s)")
        else:
            print_error("No pointing devices detected!")

        if self.is_ptp:
            print_success("Precision Touchpad (PTP) detected")
        elif self.trackpad_vendor:
            print_info(f"Legacy trackpad: {self.trackpad_vendor}")

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
    checker = MouseChecker()
    checker.run()

if __name__ == "__main__":
    main()
