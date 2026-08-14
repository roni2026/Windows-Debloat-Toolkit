"""
KB Toolkit - Reclaim Space Module
Deeper, slower cleanup than the everyday Optimizer: permanently trims the
WinSxS component store and clears out old update/upgrade leftovers
(Windows.old, $WINDOWS.~BT). Read-only size scan first, nothing is
deleted without a listed, confirmed selection.
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, print_error,
    print_warning, print_info, is_admin, prompt_continue, print_divider,
    format_bytes, Spinner
)
from tweak_engine import run_cmd

CANDIDATES = [
    ("windows_old", "Windows.old (previous Windows install)", r"C:\Windows.old"),
    ("windows_bt", "$WINDOWS.~BT (upgrade staging files)", r"C:\$WINDOWS.~BT"),
    ("windows_ws", "$WINDOWS.~WS (upgrade staging files)", r"C:\$WINDOWS.~WS"),
]


class ReclaimSpace:
    def __init__(self):
        self.freed = 0

    def run(self):
        print_banner("RECLAIM SPACE", Colors.BLUE)
        if not is_admin():
            print_error("Administrator privileges are required for this module.")
            prompt_continue()
            return

        print_warning("This is a deeper cleanup than Optimizer — it can remove your ability to roll")
        print_warning("back a recent Windows upgrade. Don't run this right after a feature update")
        print_warning("unless you're confident everything is working.")
        print()

        self._scan_folders()
        self._component_store_status()

        print(f"\n  {Colors.CYAN}[1]{Colors.END} Delete found leftover folders")
        print(f"  {Colors.CYAN}[2]{Colors.END} Compact the component store (DISM /StartComponentCleanup /ResetBase)")
        print(f"  {Colors.CYAN}[3]{Colors.END} Both")
        print(f"  {Colors.CYAN}[Enter]{Colors.END} Cancel")
        choice = input(f"\n  {Colors.CYAN}Select: {Colors.END}").strip()

        if choice in ("1", "3"):
            self._delete_folders()
        if choice in ("2", "3"):
            self._component_cleanup()

        if self.freed:
            print()
            print_success(f"Total space reclaimed: {format_bytes(self.freed)}")
        prompt_continue()

    def _scan_folders(self):
        print_section("Scanning for leftover upgrade/install folders")
        self.found = []
        for key, label, path in CANDIDATES:
            if os.path.isdir(path):
                size = self._folder_size(path)
                self.found.append((key, label, path, size))
                print(f"  {Colors.YELLOW}Found{Colors.END}  {label:<40} {format_bytes(size)}")
            else:
                print(f"  {Colors.GRAY}Not present{Colors.END}  {label}")
        if not self.found:
            print_info("Nothing to clean up here — no leftover upgrade folders found.")

    def _folder_size(self, path):
        total = 0
        try:
            for root, _, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
        except Exception:
            pass
        return total

    def _delete_folders(self):
        if not getattr(self, "found", None):
            return
        print_section("Removing Leftover Folders")
        for key, label, path, size in self.found:
            print(f"  Removing {label}...")
            # Windows.old is owned by TrustedInstaller — takeown/icacls first, then rd.
            run_cmd(f'takeown /f "{path}" /r /d y', timeout=300)
            run_cmd(f'icacls "{path}" /grant administrators:F /t', timeout=300)
            stdout, stderr, rc = run_cmd(f'rd /s /q "{path}"', timeout=300)
            if not os.path.isdir(path):
                print_success(f"Removed {label} ({format_bytes(size)} freed)")
                self.freed += size
            else:
                print_error(f"Could not fully remove {label} — {stderr[:150] if stderr else 'in use or permission denied'}")

    def _component_store_status(self):
        print_section("Component Store (WinSxS)")
        spinner = Spinner("Checking component store size")
        spinner.start()
        stdout, stderr, rc = run_cmd("dism /online /cleanup-image /analyzecomponentstore", timeout=300)
        spinner.stop()
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                if "Actual Size" in line or "Shared Size" in line or "Component Store Cleanup Recommended" in line:
                    print(f"  {line.strip()}")
        else:
            print_warning("Could not read component store size (DISM may need to run elevated).")

    def _component_cleanup(self):
        print_section("Compacting Component Store")
        print_info("Running DISM /StartComponentCleanup /ResetBase — this can take several minutes")
        print_warning("and permanently removes the ability to uninstall old cumulative updates.")
        confirm = input(f"  {Colors.YELLOW}Type 'yes' to continue: {Colors.END}").strip().lower()
        if confirm != "yes":
            print_info("Skipped.")
            return
        spinner = Spinner("Compacting component store")
        spinner.start()
        stdout, stderr, rc = run_cmd(
            "dism /online /cleanup-image /startcomponentcleanup /resetbase", timeout=1800
        )
        spinner.stop()
        if rc == 0:
            print_success("Component store compacted.")
        else:
            print_error(f"DISM cleanup failed: {(stderr or stdout)[:200]}")


def main():
    ReclaimSpace().run()


if __name__ == "__main__":
    main()
