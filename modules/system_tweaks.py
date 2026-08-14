"""
KB Toolkit - System Core Tweaks Module
Windows 11 shell tweaks that don't fit "privacy" or "gaming" — classic
context menu, background app throttling, and visual effects tuned for
performance over eye candy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, print_error,
    print_warning, print_info, is_admin, prompt_continue, print_divider
)
from tweak_engine import Tweak, reg_write, reg_delete_value, reg_delete_key, reg_matches, apply_tweaks, revert_tweaks, run_cmd


def _build_tweaks():
    tweaks = []

    tweaks.append(Tweak(
        "sys_classic_menu", "Classic Right-Click Context Menu",
        "Restores the full Windows 10-style right-click menu instead of the shortened Win11 one.",
        apply=lambda: reg_write(
            "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32",
            "", "", "SZ"
        ),
        revert=lambda: reg_delete_key(
            "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32"
        ),
        check=lambda: reg_matches(
            "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32", "", ""
        ),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_background_apps", "Disable Background Apps",
        "Stops UWP/Store apps from running and syncing when you're not using them.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppPrivacy",
                                 "LetAppsRunInBackground", 2),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppPrivacy",
                                         "LetAppsRunInBackground"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppPrivacy",
                                   "LetAppsRunInBackground", 2),
    ))

    tweaks.append(Tweak(
        "sys_visual_perf", "Visual Effects → Best Performance",
        "Turns off animations, shadows, and transparency effects to reduce GPU/CPU overhead.",
        apply=lambda: (
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects",
                      "VisualFXSetting", 2),
            reg_write("HKCU\\Control Panel\\Desktop", "UserPreferencesMask", bytes([0x90, 0x12, 0x03, 0x80, 0x10, 0x00, 0x00, 0x00]), "BINARY"),
        ),
        revert=lambda: (
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects",
                      "VisualFXSetting", 0),
            reg_write("HKCU\\Control Panel\\Desktop", "UserPreferencesMask", bytes([0x9E, 0x1E, 0x07, 0x80, 0x12, 0x00, 0x00, 0x00]), "BINARY"),
        ),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects",
                                   "VisualFXSetting", 2),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_search_highlights", "Disable Search Highlights",
        "Removes the promoted/seasonal icons that appear in the taskbar search box.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search",
                                 "EnableDynamicContentInWSB", 0),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search",
                                         "EnableDynamicContentInWSB"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search",
                                   "EnableDynamicContentInWSB", 0),
    ))

    tweaks.append(Tweak(
        "sys_show_file_ext", "Show File Extensions",
        "Turns on file extensions in Explorer — off by default, and a common source of double-extension malware confusion.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                                 "HideFileExt", 0),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                                  "HideFileExt", 1),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                                   "HideFileExt", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_end_task_taskbar", "Enable 'End Task' in Taskbar Right-Click",
        "Adds a quick End Task option when right-clicking a taskbar app — no need to open Task Manager.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\TaskbarDeveloperSettings",
                                 "TaskbarEndTask", 1),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\TaskbarDeveloperSettings",
                                  "TaskbarEndTask", 0),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\TaskbarDeveloperSettings",
                                   "TaskbarEndTask", 1),
        needs_admin=False,
    ))

    return tweaks


class SystemTweaks:
    def __init__(self):
        self.tweaks = _build_tweaks()

    def run(self):
        print_banner("SYSTEM CORE TWEAKS", Colors.CYAN)
        print()
        self._print_status()
        print(f"\n  {Colors.CYAN}[A]{Colors.END} Apply selected   {Colors.CYAN}[R]{Colors.END} Revert selected   {Colors.CYAN}[Enter]{Colors.END} Back")
        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()

        if choice == "a":
            selected = self._select()
            if selected:
                applied, skipped, failed = apply_tweaks(selected)
                self._summary(applied, skipped, failed, "applied")
                if any("Context Menu" in t.name or "Taskbar" in t.name for t in selected):
                    print_info("Restart Explorer (or sign out/in) for taskbar/menu changes to show.")
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
            print(f"  {Colors.CYAN}{i:>2}.{Colors.END} [{tag}] {t.name}")
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
    SystemTweaks().run()


if __name__ == "__main__":
    main()
