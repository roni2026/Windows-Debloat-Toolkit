"""
KB Toolkit - Startup & Performance Checker Module
Startup programs, logon-triggered scheduled tasks, last boot time/duration,
and top CPU/memory consuming processes right now.
"""
import subprocess
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    format_bytes, print_stat, Spinner
)


class StartupChecker:
    def __init__(self):
        self.startup_items = []
        self.logon_tasks = []
        self.issues = []

    def run(self):
        print_banner("STARTUP & PERFORMANCE DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_boot_time()
        self.check_startup_programs()
        self.check_logon_scheduled_tasks()
        self.check_top_processes_memory()
        self.check_top_processes_cpu()

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

    # ---------------------------------------------------------------- boot time
    def check_boot_time(self):
        print_section("Last Boot")
        stdout, stderr, rc = self._run_cmd(
            'wmic os get LastBootUpTime /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            m = re.search(r"LastBootUpTime=(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", stdout)
            if m:
                y, mo, d, h, mi, s = m.groups()
                print(f"  Last Boot: {Colors.WHITE}{y}-{mo}-{d} {h}:{mi}:{s}{Colors.END}")
            else:
                print_warning("Could not parse last boot time")
        else:
            print_warning("Could not query last boot time")

        ps_cmd = (
            'powershell -NoProfile -Command '
            '"Get-WinEvent -FilterHashtable @{LogName=\'Microsoft-Windows-Diagnostics-Performance/Operational\'; Id=100} '
            '-MaxEvents 1 -ErrorAction SilentlyContinue | '
            'ForEach-Object { $_.Properties[0].Value }"'
        )
        b_stdout, _, b_rc = self._run_cmd(ps_cmd)
        if b_rc == 0 and b_stdout.strip():
            try:
                boot_ms = int(b_stdout.strip())
                color = Colors.GREEN if boot_ms < 30000 else (Colors.YELLOW if boot_ms < 60000 else Colors.RED)
                print(f"  Boot Duration: {color}{boot_ms / 1000:.1f}s{Colors.END}")
                if boot_ms >= 60000:
                    self.issues.append(f"Slow boot time: {boot_ms / 1000:.1f}s (last recorded)")
            except ValueError:
                print_info("Boot duration event found but could not be parsed")
        else:
            print_info("No boot-performance event found (needs at least one prior full boot with diagnostics enabled)")

    # ---------------------------------------------------------------- startup programs
    def check_startup_programs(self):
        print_section("Startup Programs")
        stdout, stderr, rc = self._run_cmd(
            'wmic startup get Caption, Command, Location, User /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"Could not enumerate startup programs: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_info("No startup programs found")
            return

        for item in entries:
            name = item.get("Caption", "Unknown")
            location = item.get("Location", "").strip()
            user = item.get("User", "").strip()
            print(f"  {Colors.WHITE}{name}{Colors.END}")
            print(f"    {Colors.GRAY}{location} — {user or 'All Users'}{Colors.END}")
            self.startup_items.append(item)

        print_stat("Total startup programs", len(entries))
        if len(entries) > 15:
            self.issues.append(f"{len(entries)} programs launch at startup — consider trimming via Task Manager > Startup")

    # ---------------------------------------------------------------- scheduled tasks at logon
    def check_logon_scheduled_tasks(self):
        print_section("Scheduled Tasks Running At Logon")
        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-ScheduledTask | Where-Object { $_.State -ne \'Disabled\' -and '
            '($_.Triggers | Where-Object { $_.CimClass.CimClassName -eq \'MSFT_TaskLogonTrigger\' }) } | '
            'Select-Object -ExpandProperty TaskName"'
        )
        stdout, stderr, rc = self._run_cmd(ps_cmd, timeout=20)
        if rc == 0 and stdout.strip():
            tasks = [l.strip() for l in stdout.splitlines() if l.strip()]
            for t in tasks:
                print(f"  {Colors.WHITE}{t}{Colors.END}")
                self.logon_tasks.append(t)
            print_stat("Logon-triggered tasks", len(tasks))
        else:
            print_info("No logon-triggered scheduled tasks found, or Get-ScheduledTask unavailable")

    # ---------------------------------------------------------------- top processes
    def check_top_processes_memory(self):
        print_section("Top Processes by Memory")
        stdout, stderr, rc = self._run_cmd(
            'wmic process get Name, ProcessId, WorkingSetSize /FORMAT:CSV'
        )
        if rc != 0 or not stdout.strip():
            print_error("Could not enumerate processes")
            return

        rows = self._parse_wmic_csv(stdout)
        rows = [r for r in rows if r.get("WorkingSetSize", "").isdigit()]
        rows.sort(key=lambda r: int(r["WorkingSetSize"]), reverse=True)

        for r in rows[:10]:
            name = r.get("Name", "Unknown")
            pid = r.get("ProcessId", "")
            mem = int(r["WorkingSetSize"])
            print(f"  {Colors.WHITE}{name:<28}{Colors.END} PID {Colors.GRAY}{pid:<8}{Colors.END} {Colors.CYAN}{format_bytes(mem)}{Colors.END}")

    def check_top_processes_cpu(self):
        print_section("Top Processes by CPU (instantaneous)")
        with Spinner("Sampling CPU usage") as sp:
            stdout, stderr, rc = self._run_cmd(
                'wmic path Win32_PerfFormattedData_PerfProc_Process '
                'get Name, PercentProcessorTime, IDProcess /FORMAT:CSV',
                timeout=20
            )

        if rc != 0 or not stdout.strip():
            print_warning("Could not sample CPU usage")
            return

        rows = self._parse_wmic_csv(stdout)
        rows = [r for r in rows if r.get("PercentProcessorTime", "").isdigit()
                and r.get("Name", "") not in ("_Total", "Idle")]
        rows.sort(key=lambda r: int(r["PercentProcessorTime"]), reverse=True)

        shown = 0
        for r in rows:
            pct = int(r["PercentProcessorTime"])
            if pct <= 0:
                continue
            name = r.get("Name", "Unknown")
            pid = r.get("IDProcess", "")
            color = Colors.RED if pct > 50 else (Colors.YELLOW if pct > 20 else Colors.WHITE)
            print(f"  {Colors.WHITE}{name:<28}{Colors.END} PID {Colors.GRAY}{pid:<8}{Colors.END} {color}{pct}%{Colors.END}")
            shown += 1
            if shown >= 10:
                break

        if shown == 0:
            print_info("No processes showing significant CPU usage at this instant")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Startup programs", len(self.startup_items))
        print_stat("Logon scheduled tasks", len(self.logon_tasks))

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No obvious startup/performance red flags")

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

    def _parse_wmic_csv(self, text):
        lines = [l for l in text.splitlines() if l.strip()]
        if len(lines) < 2:
            return []
        header = lines[0].split(",")
        rows = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) != len(header):
                continue
            rows.append(dict(zip(header, parts)))
        return rows


def main():
    checker = StartupChecker()
    checker.run()

if __name__ == "__main__":
    main()
