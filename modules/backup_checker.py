"""
KB Toolkit - Backup & Restore Point Checker Module
System Restore protection status and restore points, File History status,
Volume Shadow Copy service health, and legacy Windows Backup status —
answers "if I break something, can I undo it?"
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, Spinner
)


class BackupChecker:
    def __init__(self):
        self.issues = []
        self.restore_points = []

    def run(self):
        print_banner("BACKUP & RESTORE POINT DIAGNOSTIC SUITE", Colors.BLUE)

        if not is_admin():
            print_warning("Not running as Administrator — some System Protection details may be limited")

        self.check_system_restore_service()
        self.check_restore_points()
        self.check_system_protection_drives()
        self.check_file_history()
        self.check_vss_service()
        self.check_legacy_windows_backup()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True, timeout=30):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "timed out", -1
        except Exception as e:
            return "", str(e), -1

    # ---------------------------------------------------------------- system restore
    def check_system_restore_service(self):
        print_section("System Restore Service")
        stdout, _, rc = self._run_cmd("sc query swprv")  # Volume Shadow Copy provider host, also gates restore
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state:
                print(f"  Software Shadow Copy Provider: {Colors.GRAY}{state.strip()}{Colors.END}")

        stdout, _, rc = self._run_cmd(
            'powershell -NoProfile -Command "'
            'Get-CimInstance -Namespace root/default -ClassName SystemRestore -ErrorAction SilentlyContinue | '
            'Select-Object -First 1 | Out-Null; if ($?) { \\"available\\" } else { \\"unavailable\\" }"'
        )
        if "available" in stdout.lower() and "unavailable" not in stdout.lower():
            print_success("System Restore is available on this system")
        else:
            print_info("Could not confirm System Restore availability via WMI (may still work — check Control Panel > System Protection)")

    def check_restore_points(self):
        print_section("Restore Points")
        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-ComputerRestorePoint -ErrorAction SilentlyContinue | '
            'Sort-Object CreationTime -Descending | Select-Object -First 10 | '
            'ForEach-Object { \\"$($_.CreationTime)|$($_.Description)|$($_.RestorePointType)\\" }"'
        )
        with Spinner("Querying restore points") as sp:
            stdout, stderr, rc = self._run_cmd(ps_cmd, timeout=20)

        if rc != 0 or not stdout.strip():
            print_warning("No restore points found (or System Protection is disabled for this drive)")
            self.issues.append("No System Restore points found")
            print_info(r"Enable via: Control Panel > System > System Protection > Configure")
            return

        lines = [l for l in stdout.splitlines() if l.strip() and "|" in l]
        for line in lines:
            parts = line.split("|")
            date = parts[0].strip() if parts else "Unknown"
            desc = parts[1].strip() if len(parts) > 1 else "Unknown"
            rp_type = parts[2].strip() if len(parts) > 2 else ""
            print(f"  {Colors.WHITE}{date}{Colors.END}  {Colors.GRAY}{desc}{Colors.END} {Colors.CYAN}[{rp_type}]{Colors.END}")
            self.restore_points.append(line)

        print_stat("Restore points found", len(lines))

    def check_system_protection_drives(self):
        print_section("System Protection by Drive")
        stdout, _, rc = self._run_cmd("vssadmin list shadowstorage", timeout=15)
        if rc == 0 and stdout.strip():
            volumes = [l.strip() for l in stdout.splitlines() if "For volume" in l]
            if volumes:
                for v in volumes:
                    print(f"  {Colors.GRAY}{v}{Colors.END}")
            else:
                print_warning("No shadow storage associations found — System Protection appears OFF for all drives")
                self.issues.append("System Protection appears disabled on all drives (no shadow storage found)")
        else:
            print_warning("Could not query shadow storage (requires Administrator)")

    # ---------------------------------------------------------------- file history
    def check_file_history(self):
        print_section("File History")
        stdout, _, rc = self._run_cmd("sc query fhsvc")
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state and "RUNNING" in state.upper():
                print_success(f"File History service is {Colors.GREEN}{state.strip()}{Colors.END}")
            elif state:
                print_info(f"File History service state: {state.strip()} (starts on-demand when File History is turned on)")

        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-ItemProperty -Path \'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\FileHistory\' '
            '-ErrorAction SilentlyContinue | Select-Object -ExpandProperty ConfigStatus -ErrorAction SilentlyContinue"'
        )
        stdout, _, rc = self._run_cmd(ps_cmd, timeout=10)
        if stdout.strip():
            status_map = {"0": "Not configured", "1": "Configured (may be paused)", "2": "Active"}
            status = status_map.get(stdout.strip(), stdout.strip())
            print(f"  Configuration status: {Colors.CYAN}{status}{Colors.END}")
        else:
            print_info("File History does not appear to be configured")

    # ---------------------------------------------------------------- vss
    def check_vss_service(self):
        print_section("Volume Shadow Copy (VSS) Service")
        stdout, _, rc = self._run_cmd("sc query vss")
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state:
                ok = "STOPPED" in state.upper() or "RUNNING" in state.upper()
                color = Colors.GREEN if ok else Colors.YELLOW
                print(f"  VSS Service: {color}{state.strip()}{Colors.END} {Colors.GRAY}(normally Stopped until needed — that's expected){Colors.END}")
        else:
            print_warning("Could not query VSS service")

    # ---------------------------------------------------------------- legacy backup
    def check_legacy_windows_backup(self):
        print_section("Legacy Windows Backup (wbadmin)")
        stdout, stderr, rc = self._run_cmd("wbadmin get versions", timeout=20)
        has_versions = "Backup time" in stdout
        if rc == 0 and has_versions:
            versions = [l for l in stdout.splitlines() if "Backup time" in l or "Version identifier" in l]
            if versions:
                print_success(f"Found {len(versions) // 2 if versions else 0} scheduled/legacy backup version(s)")
                for v in versions[:6]:
                    print(f"  {Colors.GRAY}{v.strip()}{Colors.END}")
            else:
                print_info("wbadmin available but no backup versions found")
        else:
            print_info("No legacy Windows Backup (wbadmin) versions found, or feature not installed on this edition")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Restore points found", len(self.restore_points))

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("System Restore and backup mechanisms look healthy")

        print_info("If nothing is protected, turning on System Protection is the quickest safety net:")
        print_info(r"Control Panel > System > System Protection > Configure > Turn on system protection")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")

    def _extract_value(self, text, key):
        for line in text.splitlines():
            if key in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None


def main():
    checker = BackupChecker()
    checker.run()

if __name__ == "__main__":
    main()
