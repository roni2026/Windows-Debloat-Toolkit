"""
KB Toolkit - Hardware Checker Module
Broad laptop/desktop hardware health scan: WiFi, Bluetooth, fans/thermal,
trackpad, ports, NFC, SIM/WWAN, memory card reader, battery, webcam — plus
a catch-all scan for ANY device Windows reports as having a problem, so
things not covered by name still get flagged.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)


class HardwareChecker:
    def __init__(self):
        self.is_laptop = None
        self.problem_devices = []
        self.issues = []

    def run(self):
        print_banner("FULL HARDWARE DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_system_overview()
        self.check_battery()
        self.check_wifi()
        self.check_bluetooth()
        self.check_thermal_fan()
        self.check_trackpad()
        self.check_ports_controllers()
        self.check_nfc_smartcard()
        self.check_wwan_sim()
        self.check_card_reader()
        self.check_webcam()
        self.check_all_problem_devices()

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

    # ---------------------------------------------------------------- system
    def check_system_overview(self):
        print_section("System Overview")
        stdout, _, rc = self._run_cmd(
            'wmic computersystem get Manufacturer, Model, SystemType, PCSystemType /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                info = entries[0]
                manufacturer = info.get("Manufacturer", "Unknown")
                model = info.get("Model", "Unknown")
                pc_type = info.get("PCSystemType", "")
                # PCSystemType: 1=Desktop, 2=Mobile(laptop), 3=Workstation, etc.
                self.is_laptop = pc_type == "2"
                kind = "Laptop" if self.is_laptop else ("Desktop/Workstation" if pc_type else "Unknown")
                print(f"  Manufacturer: {Colors.WHITE}{manufacturer}{Colors.END}")
                print(f"  Model: {Colors.WHITE}{model}{Colors.END}")
                print(f"  Chassis Type: {Colors.CYAN}{kind}{Colors.END}")

        stdout, _, rc = self._run_cmd('wmic bios get SMBIOSBIOSVersion, Manufacturer /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                bios = entries[0]
                print(f"  BIOS: {Colors.GRAY}{bios.get('Manufacturer', '')} {bios.get('SMBIOSBIOSVersion', '')}{Colors.END}")

    # ---------------------------------------------------------------- battery
    def check_battery(self):
        print_section("Battery")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_Battery get BatteryStatus, EstimatedChargeRemaining, DesignVoltage, Name /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for bat in entries:
                    name = bat.get("Name", "Battery")
                    status_code = bat.get("BatteryStatus", "").strip()
                    charge = bat.get("EstimatedChargeRemaining", "").strip()
                    status_map = {
                        "1": "Discharging", "2": "AC/On Battery", "3": "Fully Charged",
                        "4": "Low", "5": "Critical", "6": "Charging", "7": "Charging High",
                        "8": "Charging Low", "9": "Charging Critical", "10": "Undefined",
                        "11": "Partially Charged",
                    }
                    status_name = status_map.get(status_code, "Unknown")
                    print(f"  {Colors.WHITE}{name}{Colors.END}")
                    print(f"  Status: {self._color_generic(status_name)}   Charge: {Colors.WHITE}{charge}%{Colors.END}")
                    if status_code in ("4", "5", "9"):
                        self.issues.append(f"Battery status: {status_name} ({charge}%)")
            else:
                print_info("No battery detected — likely a desktop system")
        else:
            print_info("No battery detected — likely a desktop system")

    # ---------------------------------------------------------------- wifi
    def check_wifi(self):
        print_section("Wi-Fi Adapter")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_NetworkAdapter WHERE "(Name LIKE \'%Wireless%\' OR Name LIKE \'%Wi-Fi%\' OR Name LIKE \'%WiFi%\' OR Name LIKE \'%802.11%\')" '
            'get Name, Status, NetEnabled, NetConnectionStatus /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for adapter in entries:
                    name = adapter.get("Name", "Unknown")
                    status = adapter.get("Status", "Unknown")
                    enabled = adapter.get("NetEnabled", "").strip().upper() == "TRUE"
                    print(f"  {Colors.WHITE}{name}{Colors.END}")
                    print(f"  Status: {self._color_generic(status)}   Enabled: {Colors.GREEN if enabled else Colors.RED}{enabled}{Colors.END}")
                    if not enabled:
                        self.issues.append(f"Wi-Fi adapter disabled: {name}")
            else:
                print_warning("No Wi-Fi adapter found")
        else:
            print_warning("Could not query Wi-Fi adapters")

        wl_stdout, _, wl_rc = self._run_cmd("netsh wlan show interfaces")
        if wl_rc == 0 and wl_stdout.strip():
            state = self._extract_value(wl_stdout, "State")
            signal = self._extract_value(wl_stdout, "Signal")
            if state:
                print(f"  Connection State: {self._color_generic(state)}")
            if signal:
                print(f"  Signal Strength: {Colors.WHITE}{signal}{Colors.END}")
        else:
            print_info("netsh wlan reported no active wireless interface")

    # ---------------------------------------------------------------- bluetooth
    def check_bluetooth(self):
        print_section("Bluetooth")
        stdout, _, rc = self._run_cmd("sc query bthserv")
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state:
                running = "RUNNING" in state.upper()
                print(f"  Bluetooth Support Service: {Colors.GREEN if running else Colors.YELLOW}{state.strip()}{Colors.END}")

        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Bluetooth%\'" get Name, Status, ConfigManagerErrorCode /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    err = dev.get("ConfigManagerErrorCode", "")
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {self._color_generic(status)}")
                    if err and err != "0":
                        self.issues.append(f"Bluetooth device {name}: Error {err}")
            else:
                print_warning("No Bluetooth devices found — adapter may be absent or disabled")
        else:
            print_warning("Could not query Bluetooth devices")

    # ---------------------------------------------------------------- thermal
    def check_thermal_fan(self):
        print_section("Fan / Thermal")
        stdout, _, rc = self._run_cmd('wmic path Win32_Fan get Name, Status, DesiredSpeed /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for fan in entries:
                    name = fan.get("Name", "Fan")
                    status = fan.get("Status", "Unknown")
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {self._color_generic(status)}")
            else:
                print_info("Win32_Fan reports no data (most OEMs don't expose fan telemetry to Windows)")
        else:
            print_info("Fan telemetry unavailable via WMI on this system")

        stdout, _, rc = self._run_cmd(
            'wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for zone in entries:
                raw = zone.get("CurrentTemperature", "")
                if raw:
                    try:
                        celsius = (int(raw) / 10) - 273.15
                        color = Colors.GREEN if celsius < 70 else (Colors.YELLOW if celsius < 90 else Colors.RED)
                        print(f"  Thermal Zone: {color}{celsius:.1f}°C{Colors.END}")
                        if celsius >= 90:
                            self.issues.append(f"High thermal zone reading: {celsius:.1f}°C")
                    except (ValueError, ZeroDivisionError):
                        pass
        else:
            print_info("ACPI thermal zone data not exposed by this system's firmware")

    # ---------------------------------------------------------------- trackpad
    def check_trackpad(self):
        print_section("Trackpad / Touchpad")
        if self.is_laptop is False:
            print_info("Desktop system — no built-in trackpad expected")
            return
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%touchpad%\' OR Name LIKE \'%precision touchpad%\' OR Name LIKE \'%synaptics%\' OR Name LIKE \'%elan%\'" '
            'get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Trackpad')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")
                print_info("For deeper diagnostics (gestures, palm rejection), use Mouse Checker / Mouse Settings")
            else:
                print_info("No dedicated trackpad device name matched (may show as a generic HID/mouse device)")
        else:
            print_warning("Could not query for trackpad devices")

    # ---------------------------------------------------------------- ports
    def check_ports_controllers(self):
        print_section("Ports & Controllers")
        stdout, _, rc = self._run_cmd('wmic path Win32_USBController get Name, Status /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for ctrl in entries:
                print(f"  {Colors.WHITE}{ctrl.get('Name', 'USB Controller')}{Colors.END} — {self._color_generic(ctrl.get('Status', 'Unknown'))}")
        else:
            print_warning("Could not enumerate USB controllers")

        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Thunderbolt%\'" get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for dev in entries:
                print(f"  {Colors.WHITE}{dev.get('Name', 'Thunderbolt')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")

        stdout, _, rc = self._run_cmd('wmic path Win32_DesktopMonitor get Name, ScreenWidth, ScreenHeight /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for mon in entries:
                w, h = mon.get("ScreenWidth", ""), mon.get("ScreenHeight", "")
                if w and h:
                    print(f"  Display: {Colors.GRAY}{mon.get('Name', 'Monitor')} ({w}x{h}){Colors.END}")

    # ---------------------------------------------------------------- nfc
    def check_nfc_smartcard(self):
        print_section("NFC / Smart Card Reader")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%NFC%\' OR Name LIKE \'%Smart Card%\' OR PNPClass=\'SmartCardReader\'" '
            'get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Unknown')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")
            else:
                print_info("No NFC or smart card reader detected (not all systems have one)")
        else:
            print_info("Could not query for NFC/smart card devices")

    # ---------------------------------------------------------------- wwan/sim
    def check_wwan_sim(self):
        print_section("Mobile Broadband / SIM (WWAN)")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%WWAN%\' OR Name LIKE \'%Mobile Broadband%\' OR Name LIKE \'%Cellular%\' OR Name LIKE \'%LTE%\' OR Name LIKE \'%5G%\'" '
            'get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Unknown')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")
            else:
                print_info("No WWAN/mobile broadband modem detected (no SIM slot on this system)")
        else:
            print_info("Could not query for WWAN devices")

    # ---------------------------------------------------------------- card reader
    def check_card_reader(self):
        print_section("Memory Card Reader")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "Name LIKE \'%card reader%\' OR Name LIKE \'%SD host%\' OR Name LIKE \'%MMC%\'" '
            'get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Unknown')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")
            else:
                print_info("No dedicated memory card reader detected")
        else:
            print_info("Could not query for card readers")

    # ---------------------------------------------------------------- webcam
    def check_webcam(self):
        print_section("Webcam / Camera")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "PNPClass=\'Camera\' OR PNPClass=\'Image\' AND Name LIKE \'%camera%\' OR Name LIKE \'%webcam%\'" '
            'get Name, Status /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    print(f"  {Colors.WHITE}{dev.get('Name', 'Unknown')}{Colors.END} — {self._color_generic(dev.get('Status', 'Unknown'))}")
            else:
                print_info("No webcam detected")
        else:
            print_info("Could not query for webcam devices")

    # ---------------------------------------------------------------- catch-all
    def check_all_problem_devices(self):
        print_section("Everything Else — Full Problem-Device Scan")
        print_info("Scanning ALL hardware for driver/config errors, regardless of category...")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_PnPEntity WHERE "ConfigManagerErrorCode!=0" get Name, ConfigManagerErrorCode, PNPClass /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for dev in entries:
                    name = dev.get("Name", "Unknown")
                    err = dev.get("ConfigManagerErrorCode", "")
                    cls = dev.get("PNPClass", "Unknown")
                    print(f"  {Colors.RED}✗{Colors.END} {Colors.WHITE}{name}{Colors.END} {Colors.GRAY}[{cls}]{Colors.END} — Error {Colors.RED}{err}{Colors.END}")
                    self.problem_devices.append(dev)
                    self.issues.append(f"{name} ({cls}): Error {err}")
            else:
                print_success("No devices with unresolved driver/config errors anywhere on this system")
        else:
            print_warning(f"Could not run full problem-device scan: {stderr[:100]}")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.problem_devices:
            print_error(f"{len(self.problem_devices)} device(s) with unresolved errors detected")
        else:
            print_success("No devices system-wide reported driver/config errors")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s) total:")
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

    def _color_generic(self, status):
        s = status.lower() if status else ""
        if s in ("ok", "connected", "fully charged", "running"):
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif s in ("error", "failed", "degraded", "disconnected", "critical", "low"):
            return f"{Colors.RED}{status}{Colors.END}"
        elif s in ("warning", "unknown", "discharging"):
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    checker = HardwareChecker()
    checker.run()

if __name__ == "__main__":
    main()
