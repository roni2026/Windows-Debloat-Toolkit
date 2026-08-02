"""
KB Toolkit - Display & GPU Checker Module
Graphics adapters, connected monitors, resolution/refresh rate, and
display driver crash (TDR) history from the Event Log.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    format_bytes, print_stat, Spinner
)

VIDEO_STATUS_OK = {"OK"}


class DisplayChecker:
    def __init__(self):
        self.gpus = []
        self.monitors = []
        self.issues = []

    def run(self):
        print_banner("DISPLAY & GPU DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_gpus()
        self.check_monitors()
        self.check_current_resolution()
        self.check_driver_crash_events()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True, timeout=30):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    # ---------------------------------------------------------------- GPUs
    def check_gpus(self):
        print_section("Graphics Adapters")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_VideoController get Name, DriverVersion, DriverDate, '
            'AdapterRAM, Status, PNPDeviceID /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"Could not query graphics adapters: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_warning("No graphics adapters found via WMI")
            return

        for i, gpu in enumerate(entries, 1):
            name = gpu.get("Name", "Unknown")
            driver_ver = gpu.get("DriverVersion", "Unknown").strip()
            driver_date_raw = gpu.get("DriverDate", "").strip()
            ram = gpu.get("AdapterRAM", "").strip()
            status = gpu.get("Status", "Unknown").strip()
            pnp_id = gpu.get("PNPDeviceID", "")

            # Skip empty/disabled placeholder entries some systems report
            if not name or name.lower() == "unknown":
                continue

            driver_date = self._format_wmi_date(driver_date_raw)
            ram_str = format_bytes(ram) if ram.isdigit() and int(ram) > 0 else "Unknown (shared/integrated)"
            is_virtual = "VEN_" not in pnp_id and pnp_id != ""

            print(f"{Colors.BOLD}GPU {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
            print(f"  Driver: {Colors.GRAY}{driver_ver}{Colors.END}   Date: {Colors.GRAY}{driver_date}{Colors.END}")
            print(f"  Video Memory: {Colors.CYAN}{ram_str}{Colors.END}")
            print(f"  Status: {self._color_status(status)}")

            if status not in VIDEO_STATUS_OK and status.strip():
                self.issues.append(f"{name}: status reported as '{status}'")

            self.gpus.append(gpu)

        if len(self.gpus) > 1:
            print_info(f"{len(self.gpus)} adapters detected — likely a hybrid/switchable graphics laptop (integrated + discrete)")

    # ---------------------------------------------------------------- monitors
    def check_monitors(self):
        print_section("Connected Monitors")
        stdout, stderr, rc = self._run_cmd(
            'powershell -NoProfile -Command "'
            'Get-CimInstance -Namespace root\\wmi -ClassName WmiMonitorID -ErrorAction SilentlyContinue | '
            'ForEach-Object { '
            '$name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join \'\'; '
            '$serial = ($_.SerialNumberID | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join \'\'; '
            '\\"$name|$serial\\" }"'
        )
        if rc == 0 and stdout.strip():
            lines = [l for l in stdout.splitlines() if l.strip()]
            for line in lines:
                parts = line.split("|")
                name = parts[0].strip() if parts and parts[0].strip() else "Unknown Monitor"
                serial = parts[1].strip() if len(parts) > 1 else ""
                print(f"  {Colors.WHITE}{name}{Colors.END}" + (f"  {Colors.GRAY}(S/N: {serial}){Colors.END}" if serial else ""))
                self.monitors.append(name)
            print_stat("Monitors detected", len(lines))
        else:
            print_warning("Could not enumerate monitor identities (WMI monitor namespace unavailable)")
            print_info("Falling back to Desktop Monitor enumeration")
            self._check_monitors_fallback()

    def _check_monitors_fallback(self):
        stdout, _, rc = self._run_cmd('wmic desktopmonitor get Name, ScreenWidth, ScreenHeight /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for mon in entries:
                name = mon.get("Name", "Unknown")
                w = mon.get("ScreenWidth", "")
                h = mon.get("ScreenHeight", "")
                dims = f"{w}x{h}" if w and h else "Unknown resolution"
                print(f"  {Colors.WHITE}{name}{Colors.END}  {Colors.GRAY}{dims}{Colors.END}")
                self.monitors.append(name)

    # ---------------------------------------------------------------- resolution
    def check_current_resolution(self):
        print_section("Current Resolution & Refresh Rate")
        stdout, _, rc = self._run_cmd(
            'wmic path Win32_VideoController get CurrentHorizontalResolution, '
            'CurrentVerticalResolution, CurrentRefreshRate, Name /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for gpu in entries:
                name = gpu.get("Name", "Unknown")
                h = gpu.get("CurrentHorizontalResolution", "").strip()
                v = gpu.get("CurrentVerticalResolution", "").strip()
                hz = gpu.get("CurrentRefreshRate", "").strip()
                if h and v:
                    hz_color = Colors.YELLOW if hz.isdigit() and int(hz) < 60 else Colors.GREEN
                    print(f"  {Colors.WHITE}{name}{Colors.END}: {Colors.CYAN}{h}x{v}{Colors.END} @ {hz_color}{hz or '?'}Hz{Colors.END}")
        else:
            print_warning("Could not determine current resolution/refresh rate")

    # ---------------------------------------------------------------- driver crashes
    def check_driver_crash_events(self):
        print_section("Display Driver Crash History (TDR events)")
        ps_cmd = (
            'powershell -NoProfile -Command "'
            "$e = Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Display'; StartTime=(Get-Date).AddDays(-14)} "
            '-MaxEvents 20 -ErrorAction SilentlyContinue; '
            'if ($e) { $e | ForEach-Object { \\"$($_.TimeCreated.ToString(\'yyyy-MM-dd HH:mm\'))|$($_.Id)\\" } }"'
        )
        with Spinner("Checking Event Log for display driver crashes") as sp:
            stdout, stderr, rc = self._run_cmd(ps_cmd, timeout=30)

        if rc != 0 or not stdout.strip():
            print_success("No display driver crash/recovery events found in the last 14 days")
            return

        lines = [l for l in stdout.splitlines() if l.strip() and "|" in l]
        for line in lines[:10]:
            time_str, event_id = line.split("|", 1)
            print(f"  {Colors.YELLOW}{time_str}{Colors.END}  Event ID {Colors.WHITE}{event_id}{Colors.END} — driver stopped responding and recovered")

        if lines:
            self.issues.append(f"Display driver crashed/recovered {len(lines)}x in the last 14 days (Event ID 4101 pattern)")
            print_info("Frequent TDR events usually point to an outdated/unstable GPU driver, overheating, or overclocking")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.gpus:
            print_success(f"Detected {len(self.gpus)} graphics adapter(s)")
        else:
            print_error("No graphics adapters detected!")

        print_stat("Monitors detected", len(self.monitors))

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

    def _format_wmi_date(self, raw):
        if not raw or len(raw) < 8:
            return "Unknown"
        try:
            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        except Exception:
            return raw

    def _color_status(self, status):
        s = (status or "").lower()
        if s == "ok":
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif s in ("error", "degraded", "unknown"):
            return f"{Colors.RED}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    checker = DisplayChecker()
    checker.run()

if __name__ == "__main__":
    main()
