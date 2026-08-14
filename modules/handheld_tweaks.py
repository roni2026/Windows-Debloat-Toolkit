"""
KB Toolkit - Handheld & Laptop Power Module
Sleep/hibernate and power-button behavior fixes aimed at handheld PCs and
laptops — the "won't wake up / battery drained in the bag" class of bugs.
Anything touching encryption or Core Isolation asks for a typed
confirmation first, since those carry real lockout/compatibility risk.
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
        "hh_hibernate_enable", "Enable Hibernate",
        "Turns hibernation back on (some OEM images ship it disabled) so it's available as a sleep option.",
        apply=lambda: run_cmd("powercfg /hibernate on"),
        revert=lambda: run_cmd("powercfg /hibernate off"),
        check=lambda: run_cmd("powercfg /a")[0].lower().find("hibernate") != -1
                      and "the following sleep states are unavailable" not in run_cmd("powercfg /a")[0].lower().split("hibernate")[0][-40:],
    ))

    tweaks.append(Tweak(
        "hh_power_button_hibernate", "Power Button → Hibernate (instead of Sleep)",
        "Fixes the common 'device wakes up hot in the bag' issue on handhelds by making the power "
        "button fully hibernate instead of using Modern Standby.",
        apply=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        revert=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 1 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 1 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        check=lambda: "2" in run_cmd(
            "powercfg /q SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION"
        )[0].split("Current AC Power Setting Index:")[-1][:10] if "PBUTTONACTION" in run_cmd(
            "powercfg /q SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION")[0] else None,
    ))

    tweaks.append(Tweak(
        "hh_usb_selective_suspend", "Disable USB Selective Suspend",
        "Stops Windows from power-cycling USB controllers mid-session — fixes some handheld "
        "controller/dongle drop-outs at the cost of slightly higher idle power draw.",
        apply=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_USB USBSELECTIVESUSPEND 0 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_USB USBSELECTIVESUSPEND 0 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        revert=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_USB USBSELECTIVESUSPEND 1 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_USB USBSELECTIVESUSPEND 1 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        check=lambda: None,  # powercfg query formatting for this one isn't reliably parseable; shown as unknown
    ))

    return tweaks


class HandheldTweaks:
    def __init__(self):
        self.tweaks = _build_tweaks()

    def run(self):
        print_banner("HANDHELD & LAPTOP POWER", Colors.YELLOW)
        print_info("These affect sleep/power-button behavior. Reasonable to run on any laptop, not just handhelds.")
        print()
        self._print_status()
        print(f"\n  {Colors.CYAN}[A]{Colors.END} Apply selected   {Colors.CYAN}[R]{Colors.END} Revert selected   "
              f"{Colors.CYAN}[C]{Colors.END} Core Isolation / Memory Integrity check   {Colors.CYAN}[Enter]{Colors.END} Back")
        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()

        if choice == "a":
            selected = self._select()
            if selected:
                applied, skipped, failed = apply_tweaks(selected, make_restore_point=False)
                self._summary(applied, skipped, failed, "applied")
        elif choice == "r":
            selected = self._select()
            if selected:
                reverted, skipped, failed = revert_tweaks(selected)
                self._summary(reverted, skipped, failed, "reverted")
        elif choice == "c":
            self._core_isolation_status()

        prompt_continue()

    def _print_status(self):
        print_section("Current Status")
        for i, t in enumerate(self.tweaks, 1):
            state = t.status()
            tag = f"{Colors.GREEN}ON {Colors.END}" if state is True else (
                  f"{Colors.GRAY}OFF{Colors.END}" if state is False else f"{Colors.YELLOW}?  {Colors.END}")
            print(f"  {Colors.CYAN}{i:>2}.{Colors.END} [{tag}] {t.name}")
            print(f"       {Colors.GRAY}{t.description}{Colors.END}")

    def _core_isolation_status(self):
        # Read-only check + guidance. Toggling this via registry is unreliable across
        # builds and can interact badly with BitLocker, so this stays informational only.
        print_section("Core Isolation / Memory Integrity")
        val = reg_matches(
            "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard\\Scenarios\\HypervisorEnforcedCodeIntegrity",
            "Enabled", 1
        )
        if val:
            print_warning("Memory Integrity is ON. It's a real security feature (blocks driver-level exploits)")
            print_warning("but can cost noticeable FPS on some older/handheld GPU drivers.")
            print_info("To turn it off: Settings → Privacy & security → Windows Security → Device security →")
            print_info("Core isolation. Doing it through the Settings app (not the registry) avoids the boot")
            print_info("issues that can happen if BitLocker is active and the change is made incorrectly.")
        else:
            print_info("Memory Integrity appears to be OFF or its state could not be confirmed on this build.")

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
    HandheldTweaks().run()


if __name__ == "__main__":
    main()
