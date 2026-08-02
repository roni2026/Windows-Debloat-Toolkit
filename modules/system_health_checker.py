"""
KB Toolkit - System File & Update Health Module
sfc /scannow and DISM health-check wrappers, Windows Update service/history
status, and pending-reboot detection. Long-running steps use a spinner since
they don't expose live percentage over a captured stdout stream.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, print_divider, Spinner
)

TASKS = [
    ("dism_checkhealth", "DISM CheckHealth (quick, read-only)",        False),
    ("dism_scanhealth",  "DISM ScanHealth (deeper scan, a few minutes)", True),
    ("sfc_scan",         "SFC /scannow (verifies & repairs system files)", True),
    ("wu_status",        "Windows Update service & history status",     False),
    ("pending_reboot",   "Pending reboot check",                        False),
]


class SystemHealthChecker:
    def __init__(self):
        self.issues = []
        self.tasks_run = []

    def run(self):
        print_banner("SYSTEM FILE & UPDATE HEALTH", Colors.BLUE)

        if not is_admin():
            print_warning("Not running as Administrator — DISM ScanHealth and SFC /scannow require")
            print_warning("elevation and will be skipped (read-only checks still run)")

        selected = self._select_tasks()
        if not selected:
            print_info("No tasks selected — nothing to do")
            prompt_continue()
            return

        print()
        print_divider("═")
        print(f"{Colors.BOLD}  Running {len(selected)} check(s)...{Colors.END}")
        print_divider("═")

        for key in selected:
            label = next(t[1] for t in TASKS if t[0] == key)
            try:
                getattr(self, f"_task_{key}")()
                self.tasks_run.append(label)
            except Exception as e:
                self.issues.append(f"{label}: error — {e}")
                print_error(f"Task failed: {e}")

        self.print_summary()
        prompt_continue()

    def _select_tasks(self):
        print_section("Select Checks")
        for i, (key, label, needs_admin) in enumerate(TASKS, 1):
            admin_tag = f" {Colors.YELLOW}[admin]{Colors.END}" if needs_admin else ""
            skip_tag = ""
            if needs_admin and not is_admin():
                skip_tag = f" {Colors.GRAY}(will be skipped — not elevated){Colors.END}"
            print(f"  {Colors.CYAN}{i}.{Colors.END} {label}{admin_tag}{skip_tag}")
        print(f"\n  {Colors.GRAY}Enter numbers separated by commas, 'a' for all, or Enter to cancel{Colors.END}")
        print(f"  {Colors.GRAY}Note: SFC /scannow can take 10-20+ minutes{Colors.END}")

        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()
        if not choice:
            return []
        if choice == "a":
            return [t[0] for t in TASKS if not (t[2] and not is_admin())]

        selected = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(TASKS):
                key, label, needs_admin = TASKS[int(part) - 1]
                if needs_admin and not is_admin():
                    print_warning(f"Skipping '{label}' — requires Administrator")
                    continue
                selected.append(key)
        return selected

    def _run_cmd(self, cmd, shell=True, timeout=1800):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", str(e), -1

    # ---------------------------------------------------------------- DISM
    def _task_dism_checkhealth(self):
        print_section("DISM CheckHealth")
        with Spinner("Checking component store health") as sp:
            stdout, stderr, rc = self._run_cmd(
                "DISM /Online /Cleanup-Image /CheckHealth", timeout=60
            )
        if "No component store corruption detected" in stdout:
            print_success("No component store corruption detected")
        elif rc == 0 and stdout.strip():
            print_warning("DISM reported an issue — see details below")
            for line in stdout.splitlines():
                if line.strip():
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")
            self.issues.append("DISM CheckHealth flagged possible component store corruption")
        else:
            print_error(f"DISM CheckHealth failed: {stderr[:150]}")

    def _task_dism_scanhealth(self):
        print_section("DISM ScanHealth")
        print_info("This performs a deeper scan and can take several minutes...")
        with Spinner("Scanning component store (this may take a while)") as sp:
            stdout, stderr, rc = self._run_cmd(
                "DISM /Online /Cleanup-Image /ScanHealth", timeout=1200
            )
        if "No component store corruption detected" in stdout:
            print_success("No component store corruption detected")
        elif "repairable" in stdout.lower():
            print_warning("Component store corruption detected and is repairable")
            print_info("Run 'DISM /Online /Cleanup-Image /RestoreHealth' (needs internet or install media) to fix")
            self.issues.append("DISM ScanHealth found repairable component store corruption")
        elif rc == 0 and stdout.strip():
            for line in stdout.splitlines()[-10:]:
                if line.strip():
                    print(f"  {Colors.GRAY}{line.strip()}{Colors.END}")
        else:
            print_error(f"DISM ScanHealth failed: {stderr[:150]}")

    # ---------------------------------------------------------------- SFC
    def _task_sfc_scan(self):
        print_section("SFC /scannow")
        print_info("Verifying and repairing protected system files — this can take 10-20+ minutes")
        with Spinner("Running SFC /scannow") as sp:
            stdout, stderr, rc = self._run_cmd("sfc /scannow", timeout=1800)

        text = stdout.replace("\x00", "")
        if "did not find any integrity violations" in text.lower():
            print_success("No integrity violations found — system files are healthy")
        elif "found corrupt files and successfully repaired" in text.lower():
            print_success("Corrupt files were found and successfully repaired")
        elif "found corrupt files but was unable to fix" in text.lower():
            print_error("Corrupt files were found but SFC could not repair them")
            print_info("Try running DISM /RestoreHealth first, then re-run SFC")
            self.issues.append("SFC found corrupt system files it could not repair")
        elif "did not complete the requested verification" in text.lower():
            print_warning("SFC could not complete — try running from Safe Mode or after a DISM RestoreHealth")
            self.issues.append("SFC scan did not complete successfully")
        else:
            print_warning("SFC finished with an unrecognized result — check CBS.log for details")
            print_info(r"Log: C:\Windows\Logs\CBS\CBS.log")

    # ---------------------------------------------------------------- windows update
    def _task_wu_status(self):
        print_section("Windows Update Status")
        for svc_id, svc_name in (("wuauserv", "Windows Update"), ("bits", "Background Intelligent Transfer")):
            stdout, _, rc = self._run_cmd(f"sc query {svc_id}", timeout=10)
            if rc == 0:
                state = None
                for line in stdout.splitlines():
                    if "STATE" in line:
                        state = line.split(":", 1)[-1].strip()
                if state:
                    ok = "RUNNING" in state.upper() or "STOPPED" in state.upper()
                    color = Colors.GREEN if "RUNNING" in state.upper() else Colors.GRAY
                    print(f"  {svc_name}: {color}{state}{Colors.END}")

        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5 HotFixID, InstalledOn | '
            'ForEach-Object { \\"$($_.HotFixID)|$($_.InstalledOn)\\" }"'
        )
        stdout, _, rc = self._run_cmd(ps_cmd, timeout=20)
        if rc == 0 and stdout.strip():
            print(f"\n  {Colors.BOLD}Recent Updates:{Colors.END}")
            for line in stdout.splitlines():
                parts = line.strip().split("|")
                if len(parts) == 2:
                    print(f"    {Colors.WHITE}{parts[0]}{Colors.END}  {Colors.GRAY}{parts[1]}{Colors.END}")
        else:
            print_info("Could not retrieve recent update history")

    # ---------------------------------------------------------------- pending reboot
    def _task_pending_reboot(self):
        print_section("Pending Reboot Check")
        checks = [
            (r'reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"', "Component Based Servicing"),
            (r'reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"', "Windows Update"),
            (r'reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager" /v PendingFileRenameOperations', "Pending File Rename Operations"),
        ]
        pending = False
        for cmd, label in checks:
            stdout, _, rc = self._run_cmd(cmd, timeout=10)
            if rc == 0 and stdout.strip():
                print_warning(f"Reboot pending: {label}")
                pending = True

        if not pending:
            print_success("No pending reboot detected")
        else:
            self.issues.append("A system reboot is pending — some fixes/updates won't take effect until you restart")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Checks completed", len(self.tasks_run), Colors.GREEN)

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No system file or update health issues detected")

        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")


def main():
    checker = SystemHealthChecker()
    checker.run()

if __name__ == "__main__":
    main()
