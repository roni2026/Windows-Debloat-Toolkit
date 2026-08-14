"""
KB Toolkit - Advanced Tuning Module
Lower-level tweaks that don't fit neatly into Debloat, Gaming, System, or
Handheld — foreground process priority, filesystem overhead, and network
adapter power management.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, print_error,
    print_warning, print_info, is_admin, prompt_continue, print_divider
)
from tweak_engine import Tweak, reg_write, reg_delete_value, reg_matches, apply_tweaks, revert_tweaks, run_cmd


def _build_tweaks():
    tweaks = []

    tweaks.append(Tweak(
        "adv_foreground_priority", "Boost Foreground App Priority",
        "Sets Win32PrioritySeparation so the app you're actively using gets a larger CPU time-slice boost over background processes.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl", "Win32PrioritySeparation", 38),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl", "Win32PrioritySeparation", 2),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl", "Win32PrioritySeparation", 38),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "adv_last_access_timestamp", "Disable NTFS Last-Access Timestamp",
        "Stops NTFS from updating a 'last accessed' timestamp on every file read — a small but real reduction in disk write overhead, especially on drives with huge numbers of small files.",
        apply=lambda: run_cmd("fsutil behavior set disablelastaccess 1"),
        revert=lambda: run_cmd("fsutil behavior set disablelastaccess 0"),
        check=lambda: "1" in run_cmd("fsutil behavior query disablelastaccess")[0],
    ))

    tweaks.append(Tweak(
        "adv_nic_power_save", "Disable Network Adapter Power Saving",
        "Stops Windows from letting the network adapter driver power it down to save energy — fixes some 'network randomly drops for a second' issues on desktops and docked laptops.",
        apply=lambda: run_cmd(
            'powershell -NoProfile -Command "Get-NetAdapter | ForEach-Object { '
            'Disable-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue }"'
        ),
        revert=lambda: run_cmd(
            'powershell -NoProfile -Command "Get-NetAdapter | ForEach-Object { '
            'Enable-NetAdapterPowerManagement -Name $_.Name -ErrorAction SilentlyContinue }"'
        ),
        check=lambda: None,
    ))

    tweaks.append(Tweak(
        "adv_reserved_storage", "Disable Reserved Storage (System-Wide)",
        "Frees the space Windows reserves for its own updates and temp files. Same effect as the Handheld module's version — listed here too since it's broadly useful on any small-drive system, not just handhelds.",
        apply=lambda: run_cmd("DISM /Online /Set-ReservedStorageState /State:Disabled"),
        revert=lambda: run_cmd("DISM /Online /Set-ReservedStorageState /State:Enabled"),
        check=lambda: "Disabled" in run_cmd("DISM /Online /Get-ReservedStorageState")[0],
        risk="reboot",
    ))

    return tweaks


class AdvancedTweaks:
    def __init__(self):
        self.tweaks = _build_tweaks()

    def run(self):
        print_banner("ADVANCED TUNING", Colors.HEADER)
        print_warning("These are lower-level tweaks. Read each description before applying.")
        if not is_admin():
            print_warning("Not running as Administrator — these will fail without elevation.")
        print()

        self._print_status()
        print(f"\n  {Colors.CYAN}[A]{Colors.END} Apply selected   {Colors.CYAN}[R]{Colors.END} Revert selected   {Colors.CYAN}[Enter]{Colors.END} Back")
        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()

        if choice == "a":
            selected = self._select()
            if selected:
                applied, skipped, failed = apply_tweaks(selected)
                self._summary(applied, skipped, failed, "applied")
        elif choice == "r":
            selected = self._select()
            if selected:
                reverted, skipped, failed = revert_tweaks(selected)
                self._summary(reverted, skipped, failed, "reverted")

        prompt_continue()

    def _print_status(self):
        print_section("Current Status")
        for i, t in enumerate(self.tweaks, 1):
            state = t.status()
            tag = f"{Colors.GREEN}ON {Colors.END}" if state is True else (
                  f"{Colors.GRAY}OFF{Colors.END}" if state is False else f"{Colors.YELLOW}?  {Colors.END}")
            risk_tag = f" {Colors.YELLOW}[reboot]{Colors.END}" if t.risk == "reboot" else ""
            print(f"  {Colors.CYAN}{i:>2}.{Colors.END} [{tag}] {t.name}{risk_tag}")
            print(f"       {Colors.GRAY}{t.description}{Colors.END}")

    def _select(self):
        raw = input(f"  {Colors.GRAY}Enter numbers separated by commas, or 'a' for all: {Colors.END}").strip().lower()
        if raw == "a":
            return self.tweaks
        selected = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(self.tweaks):
                selected.append(self.tweaks[int(part) - 1])
        return selected

    def _summary(self, done, skipped, failed, verb):
        print()
        print_divider("─")
        print_success(f"{len(done)} tweak(s) {verb}")
        if skipped:
            print_info(f"{len(skipped)} already at target state")
        if failed:
            print_error(f"{len(failed)} failed — see above")


def main():
    AdvancedTweaks().run()


if __name__ == "__main__":
    main()
