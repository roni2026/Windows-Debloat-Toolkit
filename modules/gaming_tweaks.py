"""
KB Toolkit - Gaming & Performance Module
Latency and frame-time tweaks: GPU scheduling, fullscreen optimizations,
Game Bar overlay, and the classic Nagle's Algorithm network tweak.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, print_error,
    print_warning, print_info, is_admin, prompt_continue, print_divider
)
from tweak_engine import Tweak, reg_write, reg_read, reg_delete_value, reg_matches, apply_tweaks, revert_tweaks, run_cmd

NIC_ROOT = r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"


def _list_nic_guids():
    """Enumerate network interface GUID subkeys under Tcpip\\Parameters\\Interfaces."""
    import winreg
    guids = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces") as key:
            i = 0
            while True:
                try:
                    guids.append(winreg.EnumKey(key, i))
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    return guids


def _nagle_apply():
    for guid in _list_nic_guids():
        path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\{guid}"
        reg_write(path, "TcpAckFrequency", 1, "DWORD")
        reg_write(path, "TCPNoDelay", 1, "DWORD")


def _nagle_revert():
    for guid in _list_nic_guids():
        path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\{guid}"
        reg_delete_value(path, "TcpAckFrequency")
        reg_delete_value(path, "TCPNoDelay")


def _nagle_check():
    guids = _list_nic_guids()
    if not guids:
        return None
    for guid in guids:
        path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\{guid}"
        if not reg_matches(path, "TCPNoDelay", 1):
            return False
    return True


def _build_tweaks():
    tweaks = []

    tweaks.append(Tweak(
        "game_hags", "Hardware-Accelerated GPU Scheduling",
        "Lets the GPU manage its own memory queue instead of the OS — lower latency on supported GPUs.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "HwSchMode", 2),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "HwSchMode", 1),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "HwSchMode", 2),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "game_gamedvr", "Disable Game Bar / Game DVR Capture",
        "Stops the background recording hook Game Bar installs on every game process.",
        apply=lambda: (
            reg_write("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 0),
            reg_write("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR", "AllowGameDVR", 0),
        ),
        revert=lambda: (
            reg_write("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 1),
            reg_delete_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR", "AllowGameDVR"),
        ),
        check=lambda: reg_matches("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 0),
    ))

    tweaks.append(Tweak(
        "game_mpo", "Disable Multiplane Overlay (MPO)",
        "Fixes flickering/black-flash issues some GPU+monitor combos have during fullscreen gaming.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows\\Dwm", "OverlayTestMode", 5),
        revert=lambda: reg_delete_value("HKLM\\SOFTWARE\\Microsoft\\Windows\\Dwm", "OverlayTestMode"),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Microsoft\\Windows\\Dwm", "OverlayTestMode", 5),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "game_fullscreen_opt", "Disable Fullscreen Optimizations (global default)",
        "Sets the system-wide default so exclusive fullscreen behaves like it did pre-Win10 DX changes.",
        apply=lambda: reg_write("HKCU\\SYSTEM\\GameConfigStore", "GameDVR_FSEBehaviorMode", 2),
        revert=lambda: reg_delete_value("HKCU\\SYSTEM\\GameConfigStore", "GameDVR_FSEBehaviorMode"),
        check=lambda: reg_matches("HKCU\\SYSTEM\\GameConfigStore", "GameDVR_FSEBehaviorMode", 2),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "game_nagle", "Disable Nagle's Algorithm",
        "Sends small network packets immediately instead of batching them — reduces input/network latency.",
        apply=_nagle_apply,
        revert=_nagle_revert,
        check=_nagle_check,
    ))

    tweaks.append(Tweak(
        "game_ultimate_perf", "Enable Ultimate Performance Power Plan",
        "Unlocks and activates the hidden power plan that avoids all CPU parking/throttling.",
        apply=lambda: run_cmd(
            "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 && "
            "for /f \"tokens=4\" %g in ('powercfg /list ^| findstr /c:\"Ultimate Performance\"') "
            "do powercfg /setactive %g"
        ),
        revert=lambda: run_cmd("powercfg /setactive SCHEME_BALANCED"),
        check=lambda: "Ultimate Performance" in run_cmd("powercfg /getactivescheme")[0],
    ))

    tweaks.append(Tweak(
        "game_vrr", "Enable Variable Refresh Rate",
        "Turns on OS-level VRR support for compatible monitors/GPUs (G-Sync/FreeSync).",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences", "DirectXUserGlobalSettings", "VRROptimizeEnable=1;", "SZ"),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences", "DirectXUserGlobalSettings", "VRROptimizeEnable=0;", "SZ"),
        check=lambda: "VRROptimizeEnable=1" in (reg_read("HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences", "DirectXUserGlobalSettings") or ""),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "game_gamemode", "Ensure Windows Game Mode is On",
        "Confirms Game Mode is enabled so background tasks get deprioritized while a game has focus.",
        apply=lambda: reg_write("HKCU\\Software\\Microsoft\\GameBar", "AutoGameModeEnabled", 1),
        revert=lambda: reg_write("HKCU\\Software\\Microsoft\\GameBar", "AutoGameModeEnabled", 0),
        check=lambda: reg_matches("HKCU\\Software\\Microsoft\\GameBar", "AutoGameModeEnabled", 1),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "game_xbox_services", "Disable Xbox Background Services",
        "Sets the Xbox Live auth/save/networking services to manual start so they aren't running when you're not using them — Game Bar/Xbox app still work when actually launched.",
        apply=lambda: run_cmd(
            "sc config XblAuthManager start= demand && sc config XblGameSave start= demand && "
            "sc config XboxNetApiSvc start= demand"
        ),
        revert=lambda: run_cmd(
            "sc config XblAuthManager start= auto && sc config XblGameSave start= auto && "
            "sc config XboxNetApiSvc start= auto"
        ),
        check=lambda: "DEMAND_START" in run_cmd("sc qc XblAuthManager")[0].upper(),
    ))

    tweaks.append(Tweak(
        "game_power_throttling", "Disable Power Throttling",
        "Stops Windows from clock-throttling background/foreground processes to save battery — useful on desktops or when plugged in for consistent frame times.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling", "PowerThrottlingOff", 1),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling", "PowerThrottlingOff", 0),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling", "PowerThrottlingOff", 1),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "game_network_throttling", "Disable Network Throttling Index",
        "Removes the ~10Mbps cap Windows' multimedia scheduler puts on network throughput while audio/games are running.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                 "NetworkThrottlingIndex", 0xffffffff),
        revert=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                  "NetworkThrottlingIndex", 10),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                   "NetworkThrottlingIndex", 0xffffffff),
    ))

    tweaks.append(Tweak(
        "game_mouse_accel", "Disable Enhance Pointer Precision",
        "Turns off Windows' mouse acceleration curve so cursor movement is 1:1 with physical mouse movement — the classic gaming-mouse tweak.",
        apply=lambda: (
            reg_write("HKCU\\Control Panel\\Mouse", "MouseSpeed", "0", "SZ"),
            reg_write("HKCU\\Control Panel\\Mouse", "MouseThreshold1", "0", "SZ"),
            reg_write("HKCU\\Control Panel\\Mouse", "MouseThreshold2", "0", "SZ"),
        ),
        revert=lambda: (
            reg_write("HKCU\\Control Panel\\Mouse", "MouseSpeed", "1", "SZ"),
            reg_write("HKCU\\Control Panel\\Mouse", "MouseThreshold1", "6", "SZ"),
            reg_write("HKCU\\Control Panel\\Mouse", "MouseThreshold2", "10", "SZ"),
        ),
        check=lambda: reg_matches("HKCU\\Control Panel\\Mouse", "MouseSpeed", "0"),
        needs_admin=False,
    ))

    tweaks.append(Tweak(
        "game_system_responsiveness", "Set System Responsiveness for Gaming",
        "Tells the multimedia class scheduler to reserve 0% of CPU for background tasks (default reserves some for smoothness of non-media apps) — trades general smoothness for game/media priority.",
        apply=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                 "SystemResponsiveness", 0),
        revert=lambda: reg_write("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                  "SystemResponsiveness", 20),
        check=lambda: reg_matches("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile",
                                   "SystemResponsiveness", 0),
    ))

    tweaks.append(Tweak(
        "game_ntfs_memory", "Increase NTFS System Cache",
        "Raises NTFS's memory usage tier for file-system caching — can help load times on titles reading lots of small files.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management",
                                 "NtfsMemoryUsage", 2),
        revert=lambda: reg_delete_value("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management",
                                         "NtfsMemoryUsage"),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management",
                                   "NtfsMemoryUsage", 2),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "game_pcie_aspm", "Disable PCIe Active State Power Management",
        "Keeps PCIe links (GPU, NVMe) out of low-power states during the current power plan — trims micro-stutter from link power transitions at the cost of some idle power draw.",
        apply=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        revert=lambda: run_cmd(
            "powercfg /setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 1 && "
            "powercfg /setactive SCHEME_CURRENT"
        ),
        check=lambda: None,
    ))

    tweaks.append(Tweak(
        "game_tdr_delay", "Increase GPU Crash-Recovery Timeout (TdrDelay)",
        "Extends how long Windows waits before assuming a GPU has hung and resetting the driver — reduces false 'Display driver stopped responding' errors during heavy/long GPU workloads.",
        apply=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "TdrDelay", 8),
        revert=lambda: reg_write("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "TdrDelay", 2),
        check=lambda: reg_matches("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "TdrDelay", 8),
        risk="reboot",
    ))

    tweaks.append(Tweak(
        "game_gpu_priority", "Raise GPU Priority for Games Task Category",
        "Bumps the GPU scheduling priority assigned to the 'Games' multimedia task category so games get preferential GPU time over other tasks.",
        apply=lambda: reg_write(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games",
            "GPU Priority", 8
        ),
        revert=lambda: reg_write(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games",
            "GPU Priority", 2
        ),
        check=lambda: reg_matches(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games",
            "GPU Priority", 8
        ),
    ))

    return tweaks


class GamingTweaks:
    def __init__(self):
        self.tweaks = _build_tweaks()

    def run(self):
        print_banner("GAMING & PERFORMANCE", Colors.GREEN)
        if not is_admin():
            print_warning("Not running as Administrator — most of these tweaks write to HKLM and will fail.")
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
    GamingTweaks().run()


if __name__ == "__main__":
    main()
