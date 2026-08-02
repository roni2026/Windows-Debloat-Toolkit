"""
KB Toolkit - Battery Health Checker Module
Current charge/status plus a powercfg /batteryreport wrapper that extracts
design capacity vs. full charge capacity to compute battery wear.
"""
import subprocess
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, Spinner
)

BATTERY_STATUS = {
    "1": "Discharging", "2": "AC Power (not charging)", "3": "Fully Charged",
    "4": "Low", "5": "Critical", "6": "Charging", "7": "Charging, High",
    "8": "Charging, Low", "9": "Charging, Critical", "10": "Undefined",
    "11": "Partially Charged",
}


class BatteryChecker:
    def __init__(self):
        self.has_battery = False
        self.issues = []
        self.design_capacity = None
        self.full_charge_capacity = None

    def run(self):
        print_banner("BATTERY HEALTH DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_current_status()
        if self.has_battery:
            self.generate_battery_report()
        else:
            print_info("No battery detected — this looks like a desktop system, skipping battery report")

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

    # ---------------------------------------------------------------- current status
    def check_current_status(self):
        print_section("Current Battery Status")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_Battery get Name, EstimatedChargeRemaining, '
            'BatteryStatus, Chemistry, DesignVoltage /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_info("No battery found via WMI (desktop, or battery not reporting)")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_info("No battery found via WMI (desktop, or battery not reporting)")
            return

        self.has_battery = True
        for battery in entries:
            name = battery.get("Name", "Battery")
            charge = battery.get("EstimatedChargeRemaining", "").strip()
            status_code = battery.get("BatteryStatus", "").strip()
            status = BATTERY_STATUS.get(status_code, "Unknown")

            color = Colors.GREEN
            if charge.isdigit():
                pct = int(charge)
                color = Colors.GREEN if pct > 40 else (Colors.YELLOW if pct > 15 else Colors.RED)
                if pct <= 15 and status_code not in ("6", "7", "3"):
                    self.issues.append(f"Battery critically low: {pct}%")

            print(f"  {Colors.WHITE}{name}{Colors.END}")
            print(f"  Charge: {color}{charge or '?'}%{Colors.END}   Status: {Colors.CYAN}{status}{Colors.END}")

    # ---------------------------------------------------------------- battery report
    def generate_battery_report(self):
        print_section("Battery Health Report (powercfg)")
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError:
            out_dir = os.environ.get("TEMP", ".")

        report_path = os.path.join(out_dir, "battery_report.html")

        with Spinner("Generating battery report (powercfg /batteryreport)") as sp:
            stdout, stderr, rc = self._run_cmd(f'powercfg /batteryreport /output "{report_path}"', timeout=30)

        if rc != 0 or not os.path.exists(report_path):
            print_warning("Could not generate battery report")
            if stderr:
                print(f"  {Colors.GRAY}{stderr.strip()[:150]}{Colors.END}")
            return

        print_success(f"Report saved to {report_path}")

        try:
            with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except OSError as e:
            print_warning(f"Could not read report for analysis: {e}")
            return

        self._analyze_report(html)

    def _analyze_report(self, html):
        design = self._extract_capacity(html, "DESIGN CAPACITY")
        full = self._extract_capacity(html, "FULL CHARGE CAPACITY")
        cycle_match = re.search(r"CYCLE COUNT.*?<td[^>]*>([\d,]+)</td>", html, re.IGNORECASE | re.DOTALL)
        cycle_count = cycle_match.group(1).replace(",", "") if cycle_match else None

        if design and full:
            self.design_capacity = design
            self.full_charge_capacity = full
            wear_pct = max(0, 100 - (full / design * 100))
            health_pct = 100 - wear_pct

            color = Colors.GREEN if health_pct >= 80 else (Colors.YELLOW if health_pct >= 60 else Colors.RED)
            print(f"\n  Design Capacity:      {Colors.WHITE}{design:,} mWh{Colors.END}")
            print(f"  Full Charge Capacity: {Colors.WHITE}{full:,} mWh{Colors.END}")
            print(f"  Battery Health:       {color}{health_pct:.1f}%{Colors.END} ({Colors.GRAY}{wear_pct:.1f}% wear{Colors.END})")

            if health_pct < 60:
                self.issues.append(f"Battery health at {health_pct:.1f}% — significant capacity loss, consider replacement")
            elif health_pct < 80:
                self.issues.append(f"Battery health at {health_pct:.1f}% — noticeable capacity loss")
        else:
            print_info("Could not parse capacity figures from the report — open the HTML file directly for full details")

        if cycle_count:
            print(f"  Cycle Count:          {Colors.WHITE}{cycle_count}{Colors.END}")

        print_info("Open the saved HTML report for full charge history and battery usage graphs")

    def _extract_capacity(self, html, label):
        # Matches rows like: <span ...>DESIGN CAPACITY</span></td><td ...>47,000 mWh</td>
        pattern = rf"{label}.*?([\d,]+)\s*mWh"
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if not self.has_battery:
            print_info("No battery present on this system (desktop)")
        elif self.design_capacity and self.full_charge_capacity:
            health_pct = 100 - max(0, 100 - (self.full_charge_capacity / self.design_capacity * 100))
            print_stat("Battery health", f"{health_pct:.1f}%")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No critical battery issues detected")

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


def main():
    checker = BatteryChecker()
    checker.run()

if __name__ == "__main__":
    main()
