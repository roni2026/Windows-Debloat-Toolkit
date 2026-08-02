"""
KB Toolkit - Reset & Repair Helpers Module
The "fix-it" counterpart to the checker modules: network stack reset,
print spooler reset, Windows Update component reset, Explorer restart,
Windows Search index rebuild, and Store app cache reset.

Every task explains what it does and (for anything disruptive) asks for
explicit confirmation before running, in addition to the shared admin-gated
task picker used elsewhere in the toolkit.
"""
import subprocess
import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, print_divider, Spinner
)

TASKS = [
    ("explorer_restart",  "Restart Windows Explorer (fix taskbar/icon glitches)",         False),
    ("winsock_reset",     "Reset Network Stack (Winsock + TCP/IP) — needs reboot",         True),
    ("network_repair",    "Release/Renew IP + Flush DNS (no reboot needed)",               False),
    ("spooler_reset",     "Reset Print Spooler (clears stuck print queue)",                True),
    ("wu_component_reset","Reset Windows Update Components (deeper than cache clear)",     True),
    ("search_reindex",    "Rebuild Windows Search Index",                                  True),
    ("store_reset",       "Reset Microsoft Store cache (wsreset)",                         False),
]

CONFIRM_REQUIRED = {"winsock_reset", "wu_component_reset", "search_reindex"}


class RepairToolkit:
    def __init__(self):
        self.tasks_run = []
        self.errors = []

    def run(self):
        print_banner("RESET & REPAIR TOOLKIT", Colors.BLUE)
        print_warning("These actions modify live system state. Read each description before selecting.")

        if not is_admin():
            print_warning("Not running as Administrator — several repair tasks will be skipped")
            print_info("Choose 'A' from the main menu to relaunch elevated")

        selected = self._select_tasks()
        if not selected:
            print_info("No tasks selected — nothing to do")
            prompt_continue()
            return

        print()
        print_divider("═")
        print(f"{Colors.BOLD}  Running {len(selected)} repair task(s)...{Colors.END}")
        print_divider("═")

        for key in selected:
            label = next(t[1] for t in TASKS if t[0] == key)
            if key in CONFIRM_REQUIRED:
                confirm = input(
                    f"\n  {Colors.YELLOW}Confirm: {label}? This changes system configuration. [y/N]: {Colors.END}"
                ).strip().lower()
                if confirm != "y":
                    print_info(f"Skipped: {label}")
                    continue

            try:
                getattr(self, f"_task_{key}")()
                self.tasks_run.append(label)
            except Exception as e:
                self.errors.append(f"{label}: {e}")
                print_error(f"Task failed: {e}")

        self.print_summary()
        prompt_continue()

    def _select_tasks(self):
        print_section("Select Repair Actions")
        for i, (key, label, needs_admin) in enumerate(TASKS, 1):
            admin_tag = f" {Colors.YELLOW}[admin]{Colors.END}" if needs_admin else ""
            confirm_tag = f" {Colors.MAGENTA}[confirm]{Colors.END}" if key in CONFIRM_REQUIRED else ""
            skip_tag = ""
            if needs_admin and not is_admin():
                skip_tag = f" {Colors.GRAY}(will be skipped — not elevated){Colors.END}"
            print(f"  {Colors.CYAN}{i}.{Colors.END} {label}{admin_tag}{confirm_tag}{skip_tag}")
        print(f"\n  {Colors.GRAY}Enter numbers separated by commas, or Enter to cancel{Colors.END}")
        print(f"  {Colors.GRAY}(No 'run all' here on purpose — pick specific fixes for your issue){Colors.END}")

        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()
        if not choice:
            return []

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

    def _run_cmd(self, cmd, shell=True, timeout=60):
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

    # ---------------------------------------------------------------- tasks
    def _task_explorer_restart(self):
        print_section("Restart Windows Explorer")
        with Spinner("Restarting explorer.exe") as sp:
            self._run_cmd("taskkill /f /im explorer.exe", timeout=15)
            self._run_cmd("start explorer.exe", timeout=15)
        print_success("Explorer restarted — taskbar/icons should refresh momentarily")

    def _task_winsock_reset(self):
        print_section("Reset Network Stack")
        with Spinner("Resetting Winsock catalog") as sp:
            stdout1, _, rc1 = self._run_cmd("netsh winsock reset", timeout=30)
        with Spinner("Resetting TCP/IP stack") as sp:
            stdout2, _, rc2 = self._run_cmd("netsh int ip reset", timeout=30)

        if rc1 == 0 and rc2 == 0:
            print_success("Network stack reset — a REBOOT is required for changes to take effect")
        else:
            print_warning("Reset commands ran but reported an issue — a reboot may still be needed")

    def _task_network_repair(self):
        print_section("Release/Renew IP + Flush DNS")
        with Spinner("Releasing current IP lease") as sp:
            self._run_cmd("ipconfig /release", timeout=20)
        with Spinner("Renewing IP lease") as sp:
            stdout, _, rc = self._run_cmd("ipconfig /renew", timeout=30)
        with Spinner("Flushing DNS cache") as sp:
            self._run_cmd("ipconfig /flushdns", timeout=15)

        if rc == 0:
            print_success("IP lease renewed and DNS cache flushed")
        else:
            print_warning("Renew reported an issue — check adapter connection (Wi-Fi/Ethernet may need reconnecting)")

    def _task_spooler_reset(self):
        print_section("Reset Print Spooler")
        with Spinner("Stopping Print Spooler service") as sp:
            self._run_cmd("net stop spooler", timeout=20)

        spool_path = r"C:\Windows\System32\spool\PRINTERS"
        cleared = 0
        if os.path.isdir(spool_path):
            for fn in os.listdir(spool_path):
                fp = os.path.join(spool_path, fn)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        cleared += 1
                except OSError:
                    continue

        with Spinner("Starting Print Spooler service") as sp:
            self._run_cmd("net start spooler", timeout=20)

        print_success(f"Print Spooler reset — cleared {cleared} stuck job file(s)")

    def _task_wu_component_reset(self):
        print_section("Reset Windows Update Components")
        print_info("Stopping Windows Update services...")
        with Spinner("Stopping wuauserv, cryptSvc, bits, msiserver") as sp:
            for svc in ("wuauserv", "cryptSvc", "bits", "msiserver"):
                self._run_cmd(f"net stop {svc}", timeout=20)

        renamed = []
        for folder, backup_suffix in (
            (r"C:\Windows\SoftwareDistribution", ".bak"),
            (r"C:\Windows\System32\catroot2", ".bak"),
        ):
            if os.path.isdir(folder):
                backup_path = folder + backup_suffix
                try:
                    if os.path.isdir(backup_path):
                        shutil.rmtree(backup_path, ignore_errors=True)
                    os.rename(folder, backup_path)
                    renamed.append(os.path.basename(folder))
                except OSError as e:
                    print_warning(f"Could not rename {folder}: {e}")

        with Spinner("Restarting Windows Update services") as sp:
            for svc in ("wuauserv", "cryptSvc", "bits", "msiserver"):
                self._run_cmd(f"net start {svc}", timeout=20)

        if renamed:
            print_success(f"Reset complete — renamed and rebuilt: {', '.join(renamed)}")
            print_info("Windows will recreate these folders automatically on next update check")
        else:
            print_warning("Services were cycled but no folders needed renaming (already clean)")

    def _task_search_reindex(self):
        print_section("Rebuild Windows Search Index")
        with Spinner("Stopping Windows Search service") as sp:
            self._run_cmd("net stop wsearch", timeout=20)

        index_path = os.path.join(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            "Microsoft", "Search", "Data", "Applications", "Windows"
        )
        cleared = False
        if os.path.isdir(index_path):
            try:
                shutil.rmtree(index_path, ignore_errors=True)
                cleared = True
            except OSError:
                pass

        with Spinner("Starting Windows Search service") as sp:
            self._run_cmd("net start wsearch", timeout=20)

        if cleared:
            print_success("Search index cleared — Windows will rebuild it in the background")
            print_info("Reindexing can take anywhere from minutes to hours depending on file count")
        else:
            print_warning("Search index folder not found or could not be cleared — service was still restarted")

    def _task_store_reset(self):
        print_section("Reset Microsoft Store Cache")
        with Spinner("Running wsreset.exe") as sp:
            stdout, stderr, rc = self._run_cmd("wsreset.exe", timeout=30)
        print_success("Store cache reset triggered (wsreset runs silently and closes the Store automatically)")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                          REPAIR SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Tasks completed", len(self.tasks_run), Colors.GREEN)

        if self.tasks_run:
            print(f"\n  {Colors.BOLD}Completed:{Colors.END}")
            for t in self.tasks_run:
                print(f"    {Colors.GREEN}✓{Colors.END} {t}")

        if self.errors:
            print(f"\n  {Colors.BOLD}Errors:{Colors.END}")
            for e in self.errors:
                print(f"    {Colors.RED}✗{Colors.END} {e}")

        print_info("If you ran the network/Winsock reset, restart your computer now")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")


def main():
    toolkit = RepairToolkit()
    toolkit.run()

if __name__ == "__main__":
    main()
