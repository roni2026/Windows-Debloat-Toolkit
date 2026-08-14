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
from tweak_engine import Tweak, reg_write, reg_read, reg_delete_value, reg_delete_key, reg_matches, apply_tweaks, revert_tweaks, run_cmd


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

    tweaks.append(Tweak(
        "sys_transparency", "Disable Transparency Effects",
        "Turns off the frosted-glass transparency in Start, taskbar, and title bars — a small GPU/compositor saving.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "EnableTransparency", 0),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "EnableTransparency", 1),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "EnableTransparency", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_dark_theme", "Force Dark Theme",
        "Switches both apps and the system shell to dark mode.",
        apply=lambda: (
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", 0),
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "SystemUsesLightTheme", 0),
        ),
        revert=lambda: (
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", 1),
            reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "SystemUsesLightTheme", 1),
        ),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", "AppsUseLightTheme", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_fast_startup", "Disable Fast Startup",
        "Turns off the hybrid-shutdown hiberboot feature — fixes some dual-boot and driver-state bugs at the cost of a few seconds' boot time.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power", "HiberbootEnabled", 0),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power", "HiberbootEnabled", 1),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power", "HiberbootEnabled", 0),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "sys_taskbar_align_left", "Align Taskbar Icons Left",
        "Moves the Windows 11 taskbar icons back to the left edge instead of centered.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarAl", 0),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarAl", 1),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarAl", 0),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_taskbar_never_combine", "Never Combine Taskbar Buttons",
        "Shows every open window as its own separate taskbar button with a label, instead of grouping by app.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarGlomLevel", 2),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarGlomLevel", 0),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarGlomLevel", 2),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_explorer_open_to_pc", "Explorer Opens to 'This PC'",
        "Makes File Explorer default to This PC on launch instead of Quick Access.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "LaunchTo", 1),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "LaunchTo", 2),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "LaunchTo", 1),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_show_hidden", "Show Hidden Files",
        "Makes hidden files and folders visible in Explorer.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "Hidden", 1),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "Hidden", 2),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "Hidden", 1),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_clock_seconds", "Show Seconds in Taskbar Clock",
        "Adds a seconds display to the taskbar clock.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ShowSecondsInSystemClock", 1),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ShowSecondsInSystemClock", 0),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ShowSecondsInSystemClock", 1),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_disable_lockscreen", "Disable Lock Screen",
        "Skips straight to the login prompt instead of showing the lock screen first (Pro/Enterprise editions).",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization", "NoLockScreen", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization", "NoLockScreen"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization", "NoLockScreen", 1),
    ))

    tweaks.append(Tweak(
        "sys_search_indexing", "Disable Windows Search Indexing",
        "Stops the background indexer — can noticeably reduce disk activity on older HDDs, at the cost of slower Explorer/Start search.",
        apply=lambda: run_cmd("sc config WSearch start= disabled && net stop WSearch"),
        revert=lambda: run_cmd("sc config WSearch start= delayed-auto && net start WSearch"),
        check=lambda: "DISABLED" in run_cmd("sc qc WSearch")[0].upper(),
    ))

    tweaks.append(Tweak(
        "sys_remote_assistance", "Disable Remote Assistance",
        "Turns off the legacy Remote Assistance feature — reduces one avenue for unsolicited remote-control requests.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance", "fAllowToGetHelp", 0),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance", "fAllowToGetHelp", 1),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Remote Assistance", "fAllowToGetHelp", 0),
    ))

    tweaks.append(Tweak(
        "sys_adaptive_brightness", "Disable Adaptive Brightness",
        "Stops Windows auto-adjusting screen brightness based on the ambient light sensor.",
        apply=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 0 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 0 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        revert=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 1 && "
            "powercfg /setdcvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 1 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        check=lambda: None,
    ))

    tweaks.append(Tweak(
        "sys_menu_delay", "Reduce Menu Show Delay",
        "Cuts the delay before Start/context menus appear from the 400ms default down to instant.",
        apply=lambda: reg_write("HKCU\\Control Panel\\Desktop", "MenuShowDelay", "0", "SZ"),
        revert=lambda: reg_write("HKCU\\Control Panel\\Desktop", "MenuShowDelay", "400", "SZ"),
        check=lambda: reg_matches("HKCU\\Control Panel\\Desktop", "MenuShowDelay", "0"),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_shortcut_arrow", "Remove Shortcut Arrow Overlay",
        "Removes the little arrow badge Windows puts on shortcut icons.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons", "29", "%windir%\\System32\\shell32.dll,-50", "EXPAND_SZ"),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons", "29"),
        check=lambda: reg_read("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons", "29") is not None,
    ))

    tweaks.append(Tweak(
        "sys_detailed_bsod", "Enable Detailed Blue Screen Info",
        "Shows the stop code and driver info directly on a crash screen instead of just a sad face and QR code.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\CrashControl", "DisplayParameters", 1),
        revert=lambda: reg_delete_value("HKLM\\SYSTEM\\CurrentControlSet\\Control\\CrashControl", "DisplayParameters"),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\CrashControl", "DisplayParameters", 1),
    ))

    tweaks.append(Tweak(
        "sys_aero_shake", "Disable Aero Shake",
        "Stops shaking a window's title bar from minimizing every other window.",
        apply=lambda: reg_write("HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "NoWindowMinimizingShortcuts", 1),
        revert=lambda: reg_delete_value("HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "NoWindowMinimizingShortcuts"),
        check=lambda: reg_matches("HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer", "NoWindowMinimizingShortcuts", 1),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_remove_gallery", "Remove Gallery from Explorer Sidebar",
        "Removes the Gallery (OneDrive photos) shortcut from the File Explorer navigation pane.",
        apply=lambda: reg_write(
            "HKCU\\Software\\Classes\\CLSID\\{e88865ea-0e1c-4e20-9aa6-edcd0212c87c}",
            "System.IsPinnedToNameSpaceTree", 0
        ),
        revert=lambda: reg_write(
            "HKCU\\Software\\Classes\\CLSID\\{e88865ea-0e1c-4e20-9aa6-edcd0212c87c}",
            "System.IsPinnedToNameSpaceTree", 1
        ),
        check=lambda: reg_matches(
            "HKCU\\Software\\Classes\\CLSID\\{e88865ea-0e1c-4e20-9aa6-edcd0212c87c}",
            "System.IsPinnedToNameSpaceTree", 0
        ),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_remove_home", "Remove Home from Explorer Sidebar",
        "Removes the Home shortcut from the File Explorer navigation pane.",
        apply=lambda: reg_write(
            "HKCU\\Software\\Classes\\CLSID\\{f874310e-b6b7-47dc-bc84-b9e6b38f5903}",
            "System.IsPinnedToNameSpaceTree", 0
        ),
        revert=lambda: reg_write(
            "HKCU\\Software\\Classes\\CLSID\\{f874310e-b6b7-47dc-bc84-b9e6b38f5903}",
            "System.IsPinnedToNameSpaceTree", 1
        ),
        check=lambda: reg_matches(
            "HKCU\\Software\\Classes\\CLSID\\{f874310e-b6b7-47dc-bc84-b9e6b38f5903}",
            "System.IsPinnedToNameSpaceTree", 0
        ),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "sys_finish_setup_notif", "Disable 'Finish Setting Up Your Device' Notifications",
        "Stops the recurring nag notification asking you to sign into extra Microsoft services.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent", "DisableWindowsConsumerFeatures", 1),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent", "DisableWindowsConsumerFeatures"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent", "DisableWindowsConsumerFeatures", 1),
    ))

    tweaks.append(Tweak(
        "sys_snap_flyout", "Disable Snap Layout Flyout",
        "Stops the snap-layout grid from popping up when hovering the maximize button.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableSnapAssistFlyout", 0),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableSnapAssistFlyout", 1),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableSnapAssistFlyout", 0),
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
