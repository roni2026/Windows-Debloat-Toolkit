"""
Mouse & Trackpad Toolkit - Settings & Remapper
Modifies pointer behavior, button mapping, trackpad settings, and more.
"""
import ctypes
import ctypes.wintypes
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mouse_utils import (
    Colors, MouseColors, print_mouse_banner, print_section, print_success, 
    print_error, print_warning, print_info, is_admin, prompt_continue
)

# Registry paths
MOUSE_REG = r"HKCU\Control Panel\Mouse"
DESKTOP_REG = r"HKCU\Control Panel\Desktop"
PTP_REG = r"HKCU\Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad"

class MouseRemapper:
    def __init__(self):
        self.backup_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backups"
        )
        os.makedirs(self.backup_dir, exist_ok=True)

    def run(self):
        print_mouse_banner("MOUSE & TRACKPAD SETTINGS")

        while True:
            self._show_menu()
            choice = input(f"\n{Colors.CYAN}Select option: {Colors.END}").strip().lower()

            if choice == "1":
                self._adjust_pointer_speed()
            elif choice == "2":
                self._toggle_enhance_precision()
            elif choice == "3":
                self._swap_buttons()
            elif choice == "4":
                self._adjust_double_click()
            elif choice == "5":
                self._adjust_scroll_lines()
            elif choice == "6":
                self._toggle_snaptop()
            elif choice == "7":
                self._toggle_mouse_trails()
            elif choice == "8":
                self._toggle_hide_while_typing()
            elif choice == "9":
                self._trackpad_enable_disable()
            elif choice == "10":
                self._trackpad_gestures()
            elif choice == "11":
                self._palm_rejection_settings()
            elif choice == "12":
                self._natural_scrolling()
            elif choice == "13":
                self._backup_settings()
            elif choice == "14":
                self._restore_settings()
            elif choice == "15":
                self._reset_defaults()
            elif choice == "16":
                self._show_current_settings()
            elif choice == "0":
                break
            else:
                print_error("Invalid option")

    def _show_menu(self):
        print(f"""
{Colors.BOLD}{Colors.BLUE}POINTER & BUTTON SETTINGS{Colors.END}
  {Colors.CYAN}1.{Colors.END}  Adjust pointer speed              {Colors.CYAN}2.{Colors.END}  Toggle enhance pointer precision
  {Colors.CYAN}3.{Colors.END}  Swap left/right buttons           {Colors.CYAN}4.{Colors.END}  Adjust double-click speed
  {Colors.CYAN}5.{Colors.END}  Adjust scroll wheel lines         {Colors.CYAN}6.{Colors.END}  Toggle SnapTo default button
  {Colors.CYAN}7.{Colors.END}  Toggle mouse trails               {Colors.CYAN}8.{Colors.END}  Toggle hide pointer while typing

{Colors.BOLD}{Colors.YELLOW}TRACKPAD SETTINGS{Colors.END}
  {Colors.CYAN}9.{Colors.END}  Enable/disable trackpad           {Colors.CYAN}10.{Colors.END} Configure gestures (tap/scroll)
  {Colors.CYAN}11.{Colors.END} Palm rejection sensitivity        {Colors.CYAN}12.{Colors.END} Toggle natural scrolling

{Colors.BOLD}{Colors.GREEN}MANAGEMENT{Colors.END}
  {Colors.CYAN}13.{Colors.END} Backup current settings           {Colors.CYAN}14.{Colors.END} Restore from backup
  {Colors.CYAN}15.{Colors.END} Reset all to Windows defaults     {Colors.CYAN}16.{Colors.END} View current settings

  {Colors.CYAN}0.{Colors.END}  Return to main menu
""")

    def _get_reg_value(self, path, value):
        stdout, _, rc = self._run_cmd(f'reg query "{path}" /v {value} 2>nul')
        if rc == 0:
            return self._extract_reg_value(stdout, value)
        return None

    def _set_reg_value(self, path, value, data, type_str="REG_SZ"):
        if type_str == "REG_DWORD":
            cmd = f'reg add "{path}" /v {value} /t REG_DWORD /d {data} /f'
        elif type_str == "REG_BINARY":
            cmd = f'reg add "{path}" /v {value} /t REG_BINARY /d {data} /f'
        else:
            cmd = f'reg add "{path}" /v {value} /t REG_SZ /d "{data}" /f'

        stdout, stderr, rc = self._run_cmd(cmd)
        return rc == 0

    def _run_cmd(self, cmd, shell=True):
        import subprocess
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=shell,
                                    encoding="utf-8", errors="ignore", timeout=10)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def _extract_reg_value(self, text, value_name):
        for line in text.splitlines():
            if value_name in line:
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    return parts[2].strip()
        return None

    def _refresh_system(self):
        # Notify Windows of changes
        ctypes.windll.user32.SystemParametersInfoW(0x001F, 0, None, 2)  # SPI_SETMOUSE
        ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, None, 2)  # SPI_SETMOUSESPEED
        ctypes.windll.user32.SystemParametersInfoW(0x0020, 0, None, 2)  # SPI_SETMOUSEBUTTONSWAP
        ctypes.windll.user32.SystemParametersInfoW(0x002F, 0, None, 2)  # SPI_SETDOUBLECLICKTIME
        ctypes.windll.user32.SystemParametersInfoW(0x0069, 0, None, 2)  # SPI_SETWHEELSCROLLLINES
        print_info("System settings refreshed")

    def _adjust_pointer_speed(self):
        print_section("Adjust Pointer Speed")
        current = self._get_reg_value(MOUSE_REG, "MouseSensitivity")
        print(f"Current sensitivity: {Colors.CYAN}{current}{Colors.END} (1-20, 10=default)")

        val = input(f"{Colors.CYAN}Enter new value (1-20): {Colors.END}").strip()
        try:
            speed = int(val)
            if 1 <= speed <= 20:
                if self._set_reg_value(MOUSE_REG, "MouseSensitivity", str(speed)):
                    print_success(f"Pointer speed set to {speed}")
                    self._refresh_system()
                else:
                    print_error("Failed to set registry value")
            else:
                print_error("Value must be between 1 and 20")
        except ValueError:
            print_error("Invalid number")

    def _toggle_enhance_precision(self):
        print_section("Enhance Pointer Precision")
        current = self._get_reg_value(MOUSE_REG, "MouseSpeed")
        is_on = current == "1" if current else False

        status = f"{Colors.GREEN}ON{Colors.END}" if is_on else f"{Colors.RED}OFF{Colors.END}"
        print(f"Current state: {status}")
        print(f"{Colors.GRAY}(This is Windows mouse acceleration){Colors.END}")

        new_val = "0" if is_on else "1"
        if self._set_reg_value(MOUSE_REG, "MouseSpeed", new_val, "REG_SZ"):
            # Also need to set thresholds for acceleration to work properly
            if new_val == "1":
                self._set_reg_value(MOUSE_REG, "MouseThreshold1", "6", "REG_SZ")
                self._set_reg_value(MOUSE_REG, "MouseThreshold2", "10", "REG_SZ")
            else:
                self._set_reg_value(MOUSE_REG, "MouseThreshold1", "0", "REG_SZ")
                self._set_reg_value(MOUSE_REG, "MouseThreshold2", "0", "REG_SZ")

            print_success(f"Enhance pointer precision turned {'OFF' if is_on else 'ON'}")
            self._refresh_system()
        else:
            print_error("Failed to toggle")

    def _swap_buttons(self):
        print_section("Swap Left/Right Buttons")
        current = self._get_reg_value(MOUSE_REG, "SwapMouseButtons")
        is_swapped = current == "1" if current else False

        status = f"{Colors.YELLOW}SWAPPED (Right-handed mode){Colors.END}" if is_swapped else f"{Colors.GREEN}NORMAL (Left-handed mode){Colors.END}"
        print(f"Current: {status}")

        new_val = "0" if is_swapped else "1"
        if self._set_reg_value(MOUSE_REG, "SwapMouseButtons", new_val, "REG_SZ"):
            print_success(f"Buttons set to {'normal' if is_swapped else 'swapped'}")
            self._refresh_system()
        else:
            print_error("Failed to swap buttons")

    def _adjust_double_click(self):
        print_section("Adjust Double-Click Speed")
        current = self._get_reg_value(MOUSE_REG, "DoubleClickSpeed")
        print(f"Current: {Colors.CYAN}{current}ms{Colors.END} (200-900, 500=default)")

        val = input(f"{Colors.CYAN}Enter new value in ms (200-900): {Colors.END}").strip()
        try:
            speed = int(val)
            if 200 <= speed <= 900:
                if self._set_reg_value(MOUSE_REG, "DoubleClickSpeed", str(speed), "REG_SZ"):
                    print_success(f"Double-click speed set to {speed}ms")
                    self._refresh_system()
                else:
                    print_error("Failed to set")
            else:
                print_error("Value must be between 200 and 900")
        except ValueError:
            print_error("Invalid number")

    def _adjust_scroll_lines(self):
        print_section("Adjust Scroll Wheel Lines")
        current = self._get_reg_value(MOUSE_REG, "WheelScrollLines")
        print(f"Current: {Colors.CYAN}{current}{Colors.END} lines per notch (0-100, 3=default)")

        val = input(f"{Colors.CYAN}Enter new value (0=disabled, 1-100): {Colors.END}").strip()
        try:
            lines = int(val)
            if 0 <= lines <= 100:
                if self._set_reg_value(MOUSE_REG, "WheelScrollLines", str(lines), "REG_SZ"):
                    print_success(f"Scroll set to {lines} line(s) per notch")
                    self._refresh_system()
                else:
                    print_error("Failed to set")
            else:
                print_error("Value must be between 0 and 100")
        except ValueError:
            print_error("Invalid number")

    def _toggle_snaptop(self):
        print_section("SnapTo Default Button")
        current = self._get_reg_value(MOUSE_REG, "SnapToDefaultButton")
        is_on = current == "1" if current else False

        status = f"{Colors.GREEN}ON{Colors.END}" if is_on else f"{Colors.RED}OFF{Colors.END}"
        print(f"Current: {status}")
        print(f"{Colors.GRAY}(Auto-moves cursor to default button in dialogs){Colors.END}")

        new_val = "0" if is_on else "1"
        if self._set_reg_value(MOUSE_REG, "SnapToDefaultButton", new_val, "REG_SZ"):
            print_success(f"SnapTo turned {'OFF' if is_on else 'ON'}")
            self._refresh_system()
        else:
            print_error("Failed to toggle")

    def _toggle_mouse_trails(self):
        print_section("Mouse Trails")
        current = self._get_reg_value(MOUSE_REG, "MouseTrails")
        is_on = current and current != "0"

        status = f"{Colors.GREEN}ON ({current} trails){Colors.END}" if is_on else f"{Colors.RED}OFF{Colors.END}"
        print(f"Current: {status}")

        if is_on:
            new_val = "0"
        else:
            val = input(f"{Colors.CYAN}Trail length (1-7, higher=longer): {Colors.END}").strip()
            try:
                length = int(val)
                if 1 <= length <= 7:
                    new_val = str(length)
                else:
                    print_error("Invalid length")
                    return
            except ValueError:
                print_error("Invalid number")
                return

        if self._set_reg_value(MOUSE_REG, "MouseTrails", new_val, "REG_SZ"):
            print_success(f"Mouse trails {'disabled' if new_val == '0' else 'set to ' + new_val}")
            self._refresh_system()
        else:
            print_error("Failed to set")

    def _toggle_hide_while_typing(self):
        print_section("Hide Pointer While Typing")
        current = self._get_reg_value(MOUSE_REG, "HideCursorOnTyping")
        # Also check via SystemParametersInfo

        # This is stored differently, let's use SPI
        val = ctypes.c_bool()
        ctypes.windll.user32.SystemParametersInfoW(0x2005, 0, ctypes.byref(val), 0)  # SPI_GETMOUSEVANISH
        is_on = val.value

        status = f"{Colors.GREEN}ON{Colors.END}" if is_on else f"{Colors.RED}OFF{Colors.END}"
        print(f"Current: {status}")

        new_val = not is_on
        ctypes.windll.user32.SystemParametersInfoW(0x2006, int(new_val), None, 3)  # SPI_SETMOUSEVANISH
        print_success(f"Hide while typing turned {'ON' if new_val else 'OFF'}")

    def _trackpad_enable_disable(self):
        print_section("Trackpad Enable/Disable")

        # Check if PTP
        stdout, _, rc = self._run_cmd(
            'reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status" /v Enabled 2>nul'
        )

        if rc == 0 and stdout.strip():
            # PTP trackpad
            val = self._extract_reg_value(stdout, "Enabled")
            is_enabled = val == "0x1" if val else True

            status = f"{Colors.GREEN}ENABLED{Colors.END}" if is_enabled else f"{Colors.RED}DISABLED{Colors.END}"
            print(f"Precision Touchpad: {status}")

            choice = input(f"{Colors.CYAN}Enable [E] or Disable [D] trackpad? {Colors.END}").strip().lower()
            if choice in ("e", "enable"):
                if is_admin():
                    self._set_reg_value("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status", "Enabled", "1", "REG_DWORD")
                    print_success("Trackpad enabled (reboot required)")
                else:
                    print_error("Admin required to enable PTP")
            elif choice in ("d", "disable"):
                if is_admin():
                    self._set_reg_value("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad\Status", "Enabled", "0", "REG_DWORD")
                    print_success("Trackpad disabled (reboot required)")
                else:
                    print_error("Admin required to disable PTP")
        else:
            # Legacy trackpad - check via device manager disable/enable
            print_info("Legacy trackpad detected")
            print_info("Use Device Manager or Fn+trackpad key to toggle")
            print_info("Common Fn combinations: Fn+F5, Fn+F7, Fn+F9, Fn+F10")

            # Try to find and disable via WMI
            stdout, _, rc = self._run_cmd(
                'wmic path Win32_PnPEntity WHERE "Name LIKE \'%Touchpad%\' OR Name LIKE \'%Trackpad%\'" get Name, Status, DeviceID /FORMAT:LIST'
            )
            if rc == 0 and stdout.strip():
                entries = self._parse_wmic_list(stdout)
                for dev in entries:
                    name = dev.get("Name", "Unknown")
                    status = dev.get("Status", "Unknown")
                    dev_id = dev.get("DeviceID", "")
                    print(f"\n  {Colors.WHITE}{name}{Colors.END}")
                    print(f"    Status: {self._color_status(status)}")
                    if dev_id:
                        print(f"    DeviceID: {Colors.GRAY}{dev_id}{Colors.END}")
                        if is_admin():
                            print(f"    {Colors.YELLOW}You can disable/enable this via Device Manager{Colors.END}")

    def _trackpad_gestures(self):
        print_section("Trackpad Gestures")

        print(f"{Colors.BOLD}Gesture Options:{Colors.END}")
        print(f"  {Colors.CYAN}1.{Colors.END} Toggle tap-to-click")
        print(f"  {Colors.CYAN}2.{Colors.END} Toggle two-finger scroll")
        print(f"  {Colors.CYAN}3.{Colors.END} Toggle three-finger tap")
        print(f"  {Colors.CYAN}4.{Colors.END} Toggle four-finger tap")
        print(f"  {Colors.CYAN}5.{Colors.END} Toggle edge gestures")
        print(f"  {Colors.CYAN}0.{Colors.END} Back")

        choice = input(f"\n{Colors.CYAN}Select: {Colors.END}").strip()

        if choice == "1":
            self._toggle_ptp_setting("TapEnabled", "Tap-to-click")
        elif choice == "2":
            self._toggle_ptp_setting("ScrollEnabled", "Two-finger scroll")
        elif choice == "3":
            self._toggle_ptp_setting("ThreeFingerTapEnabled", "Three-finger tap")
        elif choice == "4":
            self._toggle_ptp_setting("FourFingerTapEnabled", "Four-finger tap")
        elif choice == "5":
            self._toggle_ptp_setting("EdgeGesture", "Edge gestures")

    def _toggle_ptp_setting(self, value_name, display_name):
        current = self._get_reg_value(PTP_REG, value_name)
        is_on = current == "0x1" if current else True

        status = f"{Colors.GREEN}ON{Colors.END}" if is_on else f"{Colors.RED}OFF{Colors.END}"
        print(f"{display_name}: {status}")

        new_val = "0" if is_on else "1"
        if self._set_reg_value(PTP_REG, value_name, new_val, "REG_DWORD"):
            print_success(f"{display_name} turned {'OFF' if is_on else 'ON'}")
        else:
            print_error(f"Failed to toggle {display_name}")

    def _palm_rejection_settings(self):
        print_section("Palm Rejection Sensitivity")
        print(f"{Colors.GRAY}This helps prevent accidental cursor movement while typing.{Colors.END}")

        # PTP has CursorSpeed which affects sensitivity
        current = self._get_reg_value(PTP_REG, "CursorSpeed")
        print(f"Current cursor speed: {Colors.CYAN}{current}{Colors.END}")

        val = input(f"{Colors.CYAN}Enter sensitivity (1-20, lower=less sensitive/better palm rejection): {Colors.END}").strip()
        try:
            speed = int(val)
            if 1 <= speed <= 20:
                if self._set_reg_value(PTP_REG, "CursorSpeed", str(speed), "REG_DWORD"):
                    print_success(f"Cursor speed set to {speed}")
                    print_info("Lower values = better palm rejection but slower cursor")
                else:
                    print_error("Failed to set")
            else:
                print_error("Value must be 1-20")
        except ValueError:
            print_error("Invalid number")

    def _natural_scrolling(self):
        print_section("Natural Scrolling")
        current = self._get_reg_value(PTP_REG, "ScrollDirection")
        is_natural = current == "0x0" if current else False  # 0 = natural, 1 = standard

        status = f"{Colors.GREEN}NATURAL (content follows finger){Colors.END}" if is_natural else f"{Colors.YELLOW}STANDARD (scrollbar follows finger){Colors.END}"
        print(f"Current: {status}")

        new_val = "1" if is_natural else "0"
        if self._set_reg_value(PTP_REG, "ScrollDirection", new_val, "REG_DWORD"):
            print_success(f"Scrolling set to {'standard' if is_natural else 'natural'}")
        else:
            print_error("Failed to set")

    def _backup_settings(self):
        print_section("Backup Settings")

        settings = {}
        values = ["MouseSpeed", "MouseSensitivity", "MouseThreshold1", "MouseThreshold2",
                  "SwapMouseButtons", "DoubleClickSpeed", "MouseTrails", "WheelScrollLines",
                  "SnapToDefaultButton"]

        for val in values:
            settings[val] = self._get_reg_value(MOUSE_REG, val)

        # PTP settings
        ptp_values = ["CursorSpeed", "ScrollDirection", "TapEnabled", "ScrollEnabled",
                      "ThreeFingerTapEnabled", "FourFingerTapEnabled", "EdgeGesture"]
        ptp_settings = {}
        for val in ptp_values:
            ptp_settings[val] = self._get_reg_value(PTP_REG, val)

        backup = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mouse_settings": settings,
            "ptp_settings": ptp_settings
        }

        backup_file = os.path.join(self.backup_dir, "mouse_settings_backup.json")
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup, f, indent=2)
            print_success(f"Settings backed up to: {backup_file}")
        except Exception as e:
            print_error(f"Backup failed: {e}")

    def _restore_settings(self):
        print_section("Restore Settings")
        backup_file = os.path.join(self.backup_dir, "mouse_settings_backup.json")

        if not os.path.exists(backup_file):
            print_error(f"No backup found at: {backup_file}")
            return

        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                backup = json.load(f)

            mouse = backup.get("mouse_settings", {})
            for key, val in mouse.items():
                if val:
                    self._set_reg_value(MOUSE_REG, key, val, "REG_SZ")

            ptp = backup.get("ptp_settings", {})
            for key, val in ptp.items():
                if val:
                    self._set_reg_value(PTP_REG, key, val, "REG_DWORD")

            print_success("Settings restored from backup")
            print_info(f"Backup date: {backup.get('timestamp', 'unknown')}")
            self._refresh_system()
        except Exception as e:
            print_error(f"Restore failed: {e}")

    def _reset_defaults(self):
        confirm = input(f"{Colors.RED}Reset ALL mouse settings to Windows defaults? [yes/no]: {Colors.END}").strip().lower()
        if confirm != "yes":
            print_info("Cancelled")
            return

        print_section("Resetting to Defaults")

        defaults = {
            "MouseSpeed": "1",
            "MouseSensitivity": "10",
            "MouseThreshold1": "6",
            "MouseThreshold2": "10",
            "SwapMouseButtons": "0",
            "DoubleClickSpeed": "500",
            "MouseTrails": "0",
            "WheelScrollLines": "3",
            "SnapToDefaultButton": "0",
        }

        for key, val in defaults.items():
            self._set_reg_value(MOUSE_REG, key, val, "REG_SZ")

        # PTP defaults
        ptp_defaults = {
            "CursorSpeed": "10",
            "ScrollDirection": "1",
            "TapEnabled": "1",
            "ScrollEnabled": "1",
        }

        for key, val in ptp_defaults.items():
            self._set_reg_value(PTP_REG, key, val, "REG_DWORD")

        print_success("All settings reset to Windows defaults")
        self._refresh_system()

    def _show_current_settings(self):
        print_section("Current Mouse Settings")

        settings = [
            ("MouseSensitivity", "Pointer Speed"),
            ("MouseSpeed", "Enhance Precision (1=ON)"),
            ("SwapMouseButtons", "Buttons Swapped (1=Yes)"),
            ("DoubleClickSpeed", "Double-Click Speed (ms)"),
            ("WheelScrollLines", "Scroll Lines"),
            ("MouseTrails", "Mouse Trails (0=OFF)"),
            ("SnapToDefaultButton", "SnapTo (1=ON)"),
        ]

        print(f"{Colors.BOLD}{'Setting':<30} {'Value':<20}{Colors.END}")
        print(f"{Colors.GRAY}{'─' * 55}{Colors.END}")

        for key, label in settings:
            val = self._get_reg_value(MOUSE_REG, key)
            if val:
                print(f"  {Colors.GRAY}{label:<28}{Colors.END}: {Colors.WHITE}{val}{Colors.END}")

        # PTP settings
        print(f"\n{Colors.BOLD}Precision Touchpad Settings:{Colors.END}")
        ptp_settings = [
            ("CursorSpeed", "Cursor Speed"),
            ("ScrollDirection", "Scroll Direction (0=Natural)"),
            ("TapEnabled", "Tap-to-Click"),
            ("ScrollEnabled", "Two-Finger Scroll"),
        ]

        for key, label in ptp_settings:
            val = self._get_reg_value(PTP_REG, key)
            if val:
                print(f"  {Colors.GRAY}{label:<28}{Colors.END}: {Colors.WHITE}{val}{Colors.END}")

        input(f"\n{Colors.GRAY}Press Enter to continue...{Colors.END}")

    def _parse_wmic_list(self, text):
        entries = []
        current = {}
        for line in text.splitlines():
            line = line.strip()
            if not line:
                if current:
                    entries.append(current)
                    current = {}
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                current[k.strip()] = v.strip()
        if current:
            entries.append(current)
        return entries

    def _color_status(self, status):
        s = status.lower() if status else ""
        if "ok" in s or "running" in s:
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif "error" in s or "failed" in s or "degraded" in s:
            return f"{Colors.RED}{status}{Colors.END}"
        elif "warning" in s or "unknown" in s:
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    remapper = MouseRemapper()
    remapper.run()

if __name__ == "__main__":
    main()
