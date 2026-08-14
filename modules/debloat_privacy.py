"""
KB Toolkit - Debloat & Privacy Module
Turns off Windows telemetry, ad surfaces, and AI features that ship
enabled by default, using official registry/Group Policy switches.
Every tweak here has a matching revert, so nothing is one-way.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, print_error,
    print_warning, print_info, is_admin, prompt_continue, print_divider
)
from tweak_engine import Tweak, reg_write, reg_delete_value, reg_matches, apply_tweaks, revert_tweaks


def _build_tweaks():
    tweaks = []

    # Telemetry
    tweaks.append(Tweak(
        "priv_telemetry", "Diagnostic Data → Basic",
        "Sets telemetry reporting to the minimum level Windows allows.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry", 1),
    ))

    tweaks.append(Tweak(
        "priv_advertising_id", "Disable Advertising ID",
        "Stops apps from using a per-device ID to personalize ads.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy", 1),
    ))

    tweaks.append(Tweak(
        "priv_activity_history", "Disable Activity History",
        "Stops Windows from recording and uploading your activity timeline.",
        apply=lambda: (
            reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "EnableActivityFeed", 0),
            reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "PublishUserActivities", 0),
            reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "UploadUserActivities", 0),
        ),
        revert=lambda: (
            reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "EnableActivityFeed"),
            reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "PublishUserActivities"),
            reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "UploadUserActivities"),
        ),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "EnableActivityFeed", 0),
    ))

    # Copilot / AI features
    tweaks.append(Tweak(
        "priv_copilot", "Disable Windows Copilot",
        "Removes the Copilot button and blocks it from launching.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", 1),
    ))

    tweaks.append(Tweak(
        "priv_recall", "Disable Recall (AI snapshots)",
        "Turns off Recall's continuous screen-snapshot feature, where available.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis", 1),
    ))

    # Start menu / taskbar ads
    tweaks.append(Tweak(
        "priv_start_suggestions", "Disable Start Menu Suggestions/Ads",
        "Stops Microsoft from injecting suggested apps and \"tips\" into Start.",
        apply=lambda: (
            reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 0),
            reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-338388Enabled", 0),
        ),
        revert=lambda: (
            reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 1),
            reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-338388Enabled", 1),
        ),
        check=lambda: reg_matches("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "priv_lockscreen_tips", "Disable Lock Screen Tips & Fun Facts",
        "Stops Windows Spotlight tips from appearing on the lock screen.",
        apply=lambda: reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "RotatingLockScreenOverlayEnabled", 0),
        revert=lambda: reg_write("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "RotatingLockScreenOverlayEnabled", 1),
        check=lambda: reg_matches("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "RotatingLockScreenOverlayEnabled", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "priv_widgets", "Disable Taskbar Widgets",
        "Removes the Widgets icon and feed from the taskbar.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Dsh", "AllowNewsAndInterests", 0),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Dsh", "AllowNewsAndInterests"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Dsh", "AllowNewsAndInterests", 0),
    ))

    # Cortana / Search
    tweaks.append(Tweak(
        "priv_cortana", "Disable Cortana",
        "Turns off Cortana integration in Search.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCortana", 0),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCortana"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCortana", 0),
    ))

    tweaks.append(Tweak(
        "priv_bing_search", "Disable Web Search in Start Menu",
        "Keeps Start menu search local instead of sending queries to Bing.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1),
    ))

    return tweaks


class DebloatPrivacy:
    def __init__(self):
        self.tweaks = _build_tweaks()

    def run(self):
        print_banner("DEBLOAT & PRIVACY", Colors.MAGENTA)
        if not is_admin():
            print_warning("Not running as Administrator — most of these tweaks write to HKLM and will fail.")
            print_info("Choose 'A' from the main menu to relaunch elevated.")
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
    DebloatPrivacy().run()


if __name__ == "__main__":
    main()
