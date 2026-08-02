"""
KB Toolkit - Driver Update Scanner Module
Flags drivers by staleness (age since last driver date). No internet/vendor
database is used — this is a local heuristic, not a "latest version available"
checker, and the module says so up front.
"""
import subprocess
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, Spinner
)

# Device classes users most often care about when troubleshooting
PRIORITY_CLASSES = {
    "display", "net", "hdc", "media", "keyboard", "mouse", "usb",
    "bluetooth", "system", "diskdrive", "scsiadapter", "printer",
}

STALE_MONTHS_WARN = 24
STALE_MONTHS_FLAG = 48


class DriverChecker:
    def __init__(self):
        self.drivers = []
        self.stale_drivers = []
        self.issues = []

    def run(self):
        print_banner("DRIVER AGE SCANNER", Colors.BLUE)
        print_info("This checks how OLD each installed driver is, not whether a newer")
        print_info("version exists online — Windows Update / vendor sites still needed for that")

        self.scan_drivers()
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

    def scan_drivers(self):
        print_section("Scanning Installed Drivers")
        with Spinner("Querying signed driver inventory (this can take a moment)") as sp:
            stdout, stderr, rc = self._run_cmd(
                'wmic path Win32_PnPSignedDriver get DeviceName, DriverVersion, '
                'DriverDate, Manufacturer, DeviceClass /FORMAT:LIST',
                timeout=60
            )

        if rc != 0 or not stdout.strip():
            print_error(f"Could not enumerate drivers: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        now = datetime.now()

        for d in entries:
            name = d.get("DeviceName", "").strip()
            date_raw = d.get("DriverDate", "").strip()
            version = d.get("DriverVersion", "Unknown").strip()
            manufacturer = d.get("Manufacturer", "Unknown").strip()
            dclass = d.get("DeviceClass", "").strip()

            if not name or not date_raw:
                continue

            driver_date = self._parse_wmi_date(date_raw)
            if not driver_date:
                continue

            age_months = (now.year - driver_date.year) * 12 + (now.month - driver_date.month)

            record = {
                "name": name, "version": version, "manufacturer": manufacturer,
                "class": dclass, "date": driver_date, "age_months": age_months,
            }
            self.drivers.append(record)

            if age_months >= STALE_MONTHS_WARN:
                self.stale_drivers.append(record)

        print_stat("Total drivers scanned", len(self.drivers))
        self._print_stale_report()

    def _print_stale_report(self):
        if not self.stale_drivers:
            print_success(f"No drivers older than {STALE_MONTHS_WARN} months found")
            return

        # Priority devices first (things users actually troubleshoot), then by age descending
        def sort_key(r):
            is_priority = r["class"].lower() in PRIORITY_CLASSES
            return (not is_priority, -r["age_months"])

        ordered = sorted(self.stale_drivers, key=sort_key)

        print_section(f"Drivers Older Than {STALE_MONTHS_WARN} Months")
        shown = 0
        for r in ordered:
            if shown >= 25:
                remaining = len(ordered) - shown
                print(f"  {Colors.GRAY}... and {remaining} more{Colors.END}")
                break

            years = r["age_months"] / 12
            color = Colors.RED if r["age_months"] >= STALE_MONTHS_FLAG else Colors.YELLOW
            priority_tag = f" {Colors.CYAN}[{r['class']}]{Colors.END}" if r["class"] else ""

            print(f"  {color}{years:.1f}y{Colors.END}  {Colors.WHITE}{r['name']}{Colors.END}{priority_tag}")
            print(f"        {Colors.GRAY}{r['manufacturer']} — v{r['version']} — {r['date'].strftime('%Y-%m-%d')}{Colors.END}")

            if r["age_months"] >= STALE_MONTHS_FLAG and r["class"].lower() in PRIORITY_CLASSES:
                self.issues.append(f"{r['name']}: driver is {years:.1f} years old ({r['class']})")

            shown += 1

        print_stat(f"Drivers older than {STALE_MONTHS_WARN} months", len(self.stale_drivers))
        very_old = [r for r in self.stale_drivers if r["age_months"] >= STALE_MONTHS_FLAG]
        if very_old:
            print_warning(f"{len(very_old)} driver(s) are over {STALE_MONTHS_FLAG // 12} years old")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Total drivers scanned", len(self.drivers))
        print_stat(f"Older than {STALE_MONTHS_WARN} months", len(self.stale_drivers))

        if self.issues:
            print_warning(f"Found {len(self.issues)} notable stale driver(s) in priority device classes:")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No critically outdated drivers in priority device classes")

        print_info("Update stale drivers via Windows Update > Optional Updates, or the manufacturer's site")
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

    def _parse_wmi_date(self, raw):
        # WMI date format: YYYYMMDDHHMMSS.ffffff+ZZZ
        if not raw or len(raw) < 8:
            return None
        try:
            return datetime.strptime(raw[:8], "%Y%m%d")
        except ValueError:
            return None


def main():
    checker = DriverChecker()
    checker.run()

if __name__ == "__main__":
    main()
