"""
KB Toolkit - Event Log Scanner Module
Pulls recent Critical/Error entries from the System and Application logs and
translates the common, well-known ones into plain language instead of
dumping raw XML.
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

# (LogName, Source, EventId) -> plain-language meaning
KNOWN_EVENTS = {
    ("System", "Microsoft-Windows-Kernel-Power", "41"):
        "Unexpected shutdown/reboot — system lost power or crashed without a clean shutdown (check for power loss, overheating, or a driver crash)",
    ("System", "disk", "7"):
        "The disk detected a bad block — possible early sign of drive failure",
    ("System", "disk", "11"):
        "The driver detected a controller error on the disk — check cabling/SATA port or drive health",
    ("System", "disk", "51"):
        "Windows was unable to write/read part of a page file or file — possible failing disk",
    ("System", "Microsoft-Windows-WHEA-Logger", "18"):
        "A hardware error was corrected/reported by the CPU/chipset (WHEA) — can indicate RAM, CPU, or PSU instability",
    ("System", "Service Control Manager", "7000"):
        "A service failed to start",
    ("System", "Service Control Manager", "7001"):
        "A service failed to start because a dependency service failed",
    ("System", "Service Control Manager", "7009"):
        "A service timed out while starting",
    ("System", "Service Control Manager", "7011"):
        "A service timed out while processing a control request",
    ("System", "Service Control Manager", "7023"):
        "A service terminated with an error",
    ("System", "Service Control Manager", "7031"):
        "A service crashed unexpectedly and Windows attempted to restart it",
    ("System", "Service Control Manager", "7034"):
        "A service crashed unexpectedly and did NOT restart",
    ("Application", "Application Error", "1000"):
        "An application crashed (unhandled exception)",
    ("Application", "Application Hang", "1002"):
        "An application stopped responding (hang)",
    ("Application", "Windows Error Reporting", "1001"):
        "A crash/hang was reported to Windows Error Reporting (often paired with a 1000/1002 event above)",
    ("System", "BugCheck", "1001"):
        "A Blue Screen of Death (BSOD) occurred — check the bug check code for the specific cause",
}


class EventLogChecker:
    def __init__(self, days=7):
        self.days = days
        self.events = []
        self.issues = []
        self.log_stats = {}

    def run(self):
        print_banner("EVENT LOG SCANNER", Colors.BLUE)
        print_info(f"Scanning System and Application logs for Critical/Error entries in the last {self.days} day(s)")

        self.check_log_sizes()
        self.scan_log("System")
        self.scan_log("Application")
        self.summarize_known_patterns()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True, timeout=40):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    # ---------------------------------------------------------------- log sizes
    def check_log_sizes(self):
        print_section("Log Health")
        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-WinEvent -ListLog System,Application | '
            'Select-Object LogName, RecordCount, @{N=\'PctFull\';E={[math]::Round(($_.FileSize/$_.MaximumSizeInBytes)*100,1)}} | '
            'ForEach-Object { \\"$($_.LogName)|$($_.RecordCount)|$($_.PctFull)\\" }"'
        )
        stdout, _, rc = self._run_cmd(ps_cmd, timeout=20)
        if rc == 0 and stdout.strip():
            for line in stdout.splitlines():
                parts = line.strip().split("|")
                if len(parts) == 3:
                    log_name, count, pct_full = parts
                    self.log_stats[log_name] = (count, pct_full)
                    try:
                        pct = float(pct_full)
                        color = Colors.RED if pct > 90 else (Colors.YELLOW if pct > 70 else Colors.GREEN)
                    except ValueError:
                        color = Colors.WHITE
                    print(f"  {Colors.WHITE}{log_name:<14}{Colors.END} {Colors.GRAY}{count} records{Colors.END}   {color}{pct_full}% full{Colors.END}")
        else:
            print_warning("Could not read log size/record statistics")

    # ---------------------------------------------------------------- scan
    def scan_log(self, log_name):
        print_section(f"{log_name} Log — Critical/Error Events (last {self.days} day(s))")

        ps_cmd = (
            'powershell -NoProfile -Command "'
            f"$e = Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level=1,2; StartTime=(Get-Date).AddDays(-{self.days})}} "
            '-MaxEvents 200 -ErrorAction SilentlyContinue; '
            'if ($e) { $e | ForEach-Object { \\"$($_.TimeCreated.ToString(\'yyyy-MM-dd HH:mm\'))|$($_.ProviderName)|$($_.Id)|$($_.LevelDisplayName)\\" } }"'
        )
        with Spinner(f"Querying {log_name} log") as sp:
            stdout, stderr, rc = self._run_cmd(ps_cmd, timeout=40)

        if rc != 0 or not stdout.strip():
            print_success(f"No Critical/Error events found in {log_name} log for this period")
            return

        lines = [l for l in stdout.splitlines() if l.strip() and "|" in l]
        for line in lines:
            parts = line.split("|")
            if len(parts) != 4:
                continue
            time_str, provider, event_id, level = parts
            self.events.append({
                "log": log_name, "time": time_str, "provider": provider,
                "id": event_id, "level": level
            })

        # Group by (provider, id) for a compact view
        counts = {}
        for ev in [e for e in self.events if e["log"] == log_name]:
            key = (ev["provider"], ev["id"], ev["level"])
            counts[key] = counts.get(key, 0) + 1

        for (provider, event_id, level), count in sorted(counts.items(), key=lambda x: -x[1]):
            color = Colors.RED if level == "Critical" else Colors.YELLOW
            meaning = self._lookup_meaning(log_name, provider, event_id)
            count_tag = f" {Colors.GRAY}(x{count}){Colors.END}" if count > 1 else ""
            print(f"  {color}{level}{Colors.END}  {Colors.WHITE}{provider}{Colors.END} — Event ID {Colors.CYAN}{event_id}{Colors.END}{count_tag}")
            if meaning:
                print(f"    {Colors.GRAY}→ {meaning}{Colors.END}")

        print_stat(f"Total {log_name} Critical/Error events", len(lines))

    def _lookup_meaning(self, log_name, provider, event_id):
        # Exact provider match, then loose match on well-known short source names
        for (log, src, eid), meaning in KNOWN_EVENTS.items():
            if log == log_name and eid == event_id and (src.lower() == provider.lower() or src.lower() in provider.lower()):
                return meaning
        return None

    def summarize_known_patterns(self):
        print_section("Known Pattern Flags")
        found_any = False
        for (log, src, eid), meaning in KNOWN_EVENTS.items():
            matches = [e for e in self.events if e["log"] == log and e["id"] == eid
                       and (src.lower() == e["provider"].lower() or src.lower() in e["provider"].lower())]
            if matches:
                found_any = True
                print_warning(f"{meaning} ({len(matches)}x, most recent: {matches[0]['time']})")
                self.issues.append(f"{src} (ID {eid}) x{len(matches)}: {meaning}")

        if not found_any:
            print_success("No known critical failure patterns matched in the scanned window")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Total Critical/Error events scanned", len(self.events))
        for log_name, (count, pct_full) in self.log_stats.items():
            print_stat(f"{log_name} log size", f"{count} records, {pct_full}% full")

        if self.issues:
            print_warning(f"Found {len(self.issues)} known pattern(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No known critical failure patterns detected")

        print_info("This scans Critical/Error entries only — Warning-level events are not included")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")


def main():
    checker = EventLogChecker()
    checker.run()

if __name__ == "__main__":
    main()
