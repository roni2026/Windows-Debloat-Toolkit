"""
KB Toolkit - Key Remapper & Disabler
Provides both persistent (registry) and temporary (hook) key remapping.
Handles stuck/faulty keys by disabling or remapping scancodes.
"""
import ctypes
import ctypes.wintypes
import sys
import os
import time
import json
import threading
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, 
    print_error, print_warning, print_info, is_admin, 
    get_vk_name, get_scancode_name, SCANCODES, prompt_continue
)

# Registry path for scancode map
REG_PATH = r"SYSTEM\CurrentControlSet\Control\Keyboard Layout"
REG_VALUE = "Scancode Map"

class KeyRemapper:
    def __init__(self):
        self.current_mappings = OrderedDict()  # source_scancode -> target_scancode
        self.backup_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "backups", "scancode_backup.json"
        )
        self.hook_active = False
        self.hook_handle = None
        self.hook_thread = None
        self.hook_mappings = {}  # vk -> vk for session hook
        self.disabled_vks = set()

    def run(self):
        print_banner("KEY REMAPPER & DISABLER", Colors.YELLOW)

        while True:
            self._load_current_mappings()
            self._show_menu()

            choice = input(f"\n{Colors.CYAN}Select option: {Colors.END}").strip().lower()

            if choice == "1":
                self._add_mapping_menu()
            elif choice == "2":
                self._disable_key_menu()
            elif choice == "3":
                self._remove_mapping_menu()
            elif choice == "4":
                self._view_mappings()
            elif choice == "5":
                self._apply_registry_mappings()
            elif choice == "6":
                self._clear_all_mappings()
            elif choice == "7":
                self._backup_mappings()
            elif choice == "8":
                self._restore_mappings()
            elif choice == "9":
                self._quick_stuck_key_fix()
            elif choice == "10":
                self._session_hook_menu()
            elif choice == "11":
                self._show_scancode_reference()
            elif choice == "0":
                if self.hook_active:
                    self._stop_hook()
                break
            else:
                print_error("Invalid option")

    def _show_menu(self):
        print(f"""
{Colors.BOLD}Registry-Based Mapping{Colors.END} (Persistent, requires admin + reboot)
  {Colors.CYAN}1.{Colors.END} Remap key → another key
  {Colors.CYAN}2.{Colors.END} Disable key completely
  {Colors.CYAN}3.{Colors.END} Remove specific mapping
  {Colors.CYAN}4.{Colors.END} View current mappings
  {Colors.CYAN}5.{Colors.END} Apply registry changes
  {Colors.CYAN}6.{Colors.END} Clear ALL mappings
  {Colors.CYAN}7.{Colors.END} Backup current mappings
  {Colors.CYAN}8.{Colors.END} Restore from backup

{Colors.BOLD}Session-Based Tools{Colors.END} (Temporary, no reboot needed)
  {Colors.CYAN}9.{Colors.END} Quick stuck-key fix (auto-detect & disable)
  {Colors.CYAN}10.{Colors.END} Session hook remapper (experimental)

{Colors.BOLD}Reference{Colors.END}
  {Colors.CYAN}11.{Colors.END} Show scancode reference table

  {Colors.CYAN}0.{Colors.END} Return to main menu
""")

    def _load_current_mappings(self):
        self.current_mappings.clear()
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH, 0, winreg.KEY_READ)
            try:
                data, _ = winreg.QueryValueEx(key, REG_VALUE)
                winreg.CloseKey(key)

                if len(data) >= 12:
                    count = int.from_bytes(data[8:12], "little")
                    for i in range(count - 1):
                        offset = 12 + i * 4
                        mapping = int.from_bytes(data[offset:offset+4], "little")
                        target = (mapping >> 16) & 0xFFFF
                        source = mapping & 0xFFFF
                        if source != 0:
                            self.current_mappings[source] = target
            except FileNotFoundError:
                pass
        except Exception as e:
            pass

    def _add_mapping_menu(self):
        print_section("Add Key Remap")
        print("Enter source key (name or hex scancode, e.g., 'CAPS' or '0x3A'):")
        src = input(f"  {Colors.CYAN}Source: {Colors.END}").strip().upper()
        src_sc = self._parse_scancode(src)

        if src_sc is None:
            print_error("Invalid source key")
            return

        print("Enter target key (name or hex scancode, e.g., 'ESC' or '0x01'):")
        tgt = input(f"  {Colors.CYAN}Target: {Colors.END}").strip().upper()
        tgt_sc = self._parse_scancode(tgt)

        if tgt_sc is None:
            print_error("Invalid target key")
            return

        self.current_mappings[src_sc] = tgt_sc
        print_success(f"Mapped {get_scancode_name(src_sc)} → {get_scancode_name(tgt_sc)}")
        print_warning("You must select 'Apply registry changes' and reboot for this to take effect")

    def _disable_key_menu(self):
        print_section("Disable Key")
        print("Enter key to disable (name or hex scancode, e.g., 'F1' or '0x3B'):")
        key = input(f"  {Colors.CYAN}Key: {Colors.END}").strip().upper()
        sc = self._parse_scancode(key)

        if sc is None:
            print_error("Invalid key")
            return

        self.current_mappings[sc] = 0x0000  # 0x0000 = disabled
        print_success(f"Disabled {get_scancode_name(sc)}")
        print_warning("You must select 'Apply registry changes' and reboot for this to take effect")

    def _remove_mapping_menu(self):
        print_section("Remove Mapping")
        if not self.current_mappings:
            print_warning("No mappings to remove")
            return

        print("Current mappings:")
        mappings_list = list(self.current_mappings.items())
        for i, (src, tgt) in enumerate(mappings_list, 1):
            tgt_name = "DISABLED" if tgt == 0 else get_scancode_name(tgt)
            print(f"  {Colors.CYAN}{i}.{Colors.END} {get_scancode_name(src)} → {tgt_name}")

        choice = input(f"\n{Colors.CYAN}Enter number to remove (or 'all'): {Colors.END}").strip()
        if choice.lower() == "all":
            self.current_mappings.clear()
            print_success("All mappings removed from session")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(mappings_list):
                    src = mappings_list[idx][0]
                    del self.current_mappings[src]
                    print_success(f"Removed mapping for {get_scancode_name(src)}")
                else:
                    print_error("Invalid selection")
            except ValueError:
                print_error("Invalid input")

    def _view_mappings(self):
        print_section("Current Registry Mappings")
        if not self.current_mappings:
            print_info("No scancode mappings currently configured in registry")
        else:
            print(f"{Colors.BOLD}{'Source':<20} → {'Target':<20}{Colors.END}")
            print(f"{Colors.GRAY}{'─' * 50}{Colors.END}")
            for src, tgt in self.current_mappings.items():
                src_name = get_scancode_name(src)
                tgt_name = "DISABLED" if tgt == 0 else get_scancode_name(tgt)
                src_hex = f"0x{src:04X}"
                tgt_hex = f"0x{tgt:04X}" if tgt != 0 else "0x0000"
                print(f"  {Colors.WHITE}{src_name:<12}{Colors.GRAY}({src_hex}){Colors.END}  →  {Colors.YELLOW if tgt == 0 else Colors.GREEN}{tgt_name:<12}{Colors.GRAY}({tgt_hex}){Colors.END}")

        # Also show session hook status
        if self.hook_active:
            print(f"\n{Colors.BOLD}Session Hook Active:{Colors.END}")
            for vk, mapped_vk in self.hook_mappings.items():
                print(f"  {Colors.CYAN}{get_vk_name(vk)} → {get_vk_name(mapped_vk)}{Colors.END}")
            if self.disabled_vks:
                print(f"  {Colors.RED}Disabled: {', '.join(get_vk_name(v) for v in self.disabled_vks)}{Colors.END}")

    def _apply_registry_mappings(self):
        if not is_admin():
            print_error("Administrator privileges required to modify registry scancode map")
            print_info("Please restart this tool as Administrator")
            return

        print_section("Applying Registry Changes")

        try:
            import winreg

            if not self.current_mappings:
                # Delete the value if no mappings
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH, 0, winreg.KEY_WRITE)
                    winreg.DeleteValue(key, REG_VALUE)
                    winreg.CloseKey(key)
                    print_success("Scancode Map removed from registry")
                except FileNotFoundError:
                    print_info("No scancode map exists in registry")
            else:
                # Build binary data
                header = b"\x00\x00\x00\x00\x00\x00\x00\x00"
                count = len(self.current_mappings) + 1
                count_bytes = count.to_bytes(4, "little")

                mappings = b""
                for src, tgt in self.current_mappings.items():
                    mapping = (tgt << 16) | src
                    mappings += mapping.to_bytes(4, "little")

                null_term = b"\x00\x00\x00\x00"
                data = header + count_bytes + mappings + null_term

                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, REG_VALUE, 0, winreg.REG_BINARY, data)
                winreg.CloseKey(key)

                print_success(f"Applied {len(self.current_mappings)} mapping(s) to registry")

            print_warning("\n⚠ A system REBOOT is required for changes to take effect!")

            reboot = input(f"{Colors.YELLOW}Reboot now? [y/N]: {Colors.END}").strip().lower()
            if reboot == "y":
                os.system('shutdown /r /t 5 /c "Keyboard remapping applied"')
                print_info("Rebooting in 5 seconds...")
                time.sleep(6)

        except Exception as e:
            print_error(f"Failed to apply registry changes: {e}")

    def _clear_all_mappings(self):
        confirm = input(f"{Colors.RED}Are you sure you want to clear ALL mappings? [yes/no]: {Colors.END}").strip().lower()
        if confirm == "yes":
            self.current_mappings.clear()
            print_success("All mappings cleared from session")
            print_info("Select 'Apply registry changes' to commit")
        else:
            print_info("Cancelled")

    def _backup_mappings(self):
        print_section("Backup Mappings")
        os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)

        backup_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mappings": {f"0x{k:04X}": f"0x{v:04X}" for k, v in self.current_mappings.items()}
        }

        try:
            with open(self.backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2)
            print_success(f"Backup saved to: {self.backup_file}")
        except Exception as e:
            print_error(f"Backup failed: {e}")

    def _restore_mappings(self):
        print_section("Restore Mappings")
        if not os.path.exists(self.backup_file):
            print_error(f"No backup found at: {self.backup_file}")
            return

        try:
            with open(self.backup_file, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            mappings = backup_data.get("mappings", {})
            self.current_mappings.clear()
            for k, v in mappings.items():
                self.current_mappings[int(k, 16)] = int(v, 16)

            print_success(f"Restored {len(self.current_mappings)} mapping(s) from backup")
            print_info(f"Backup created: {backup_data.get('timestamp', 'unknown')}")
            print_warning("Select 'Apply registry changes' to commit to registry")
        except Exception as e:
            print_error(f"Restore failed: {e}")

    def _quick_stuck_key_fix(self):
        print_banner("QUICK STUCK-KEY FIX", Colors.RED)
        print(f"""
{Colors.YELLOW}This will monitor your keyboard for 5 seconds and detect any key{Colors.END}
{Colors.YELLOW}that is held down continuously (stuck key). You can then choose to{Colors.END}
{Colors.YELLOW}disable it immediately.{Colors.END}

{Colors.CYAN}Do NOT press any keys during the detection period.{Colors.END}
""")
        input(f"{Colors.GREEN}Press Enter to start 5-second detection...{Colors.END}")

        stuck_keys = set()
        hold_start = {}

        print(f"{Colors.YELLOW}Detecting... (do not press any keys){Colors.END}")

        # Initial state
        for vk in range(1, 256):
            state = ctypes.windll.user32.GetAsyncKeyState(vk)
            if state & 0x8000:
                hold_start[vk] = time.time()

        # Monitor for 5 seconds
        start = time.time()
        while time.time() - start < 5:
            for vk in range(1, 256):
                state = ctypes.windll.user32.GetAsyncKeyState(vk)
                is_pressed = (state & 0x8000) != 0

                if is_pressed:
                    if vk not in hold_start:
                        hold_start[vk] = time.time()
                    elif time.time() - hold_start[vk] > 2.0:
                        stuck_keys.add(vk)
                else:
                    hold_start.pop(vk, None)

            time.sleep(0.05)

        # Filter out common modifiers that might legitimately be held
        stuck_keys = {k for k in stuck_keys if k not in (
            0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C
        )}

        if stuck_keys:
            print(f"\n{Colors.RED}⚠ STUCK KEYS DETECTED:{Colors.END}")
            for vk in stuck_keys:
                sc = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
                print(f"  {Colors.RED}• {get_vk_name(vk)} (VK:0x{vk:02X}, SC:0x{sc:02X}){Colors.END}")

            print(f"\n{Colors.CYAN}Options:{Colors.END}")
            print(f"  {Colors.CYAN}1.{Colors.END} Disable detected stuck keys (registry)")
            print(f"  {Colors.CYAN}2.{Colors.END} Disable detected stuck keys (session hook, temporary)")
            print(f"  {Colors.CYAN}3.{Colors.END} Remap stuck key to another key")
            print(f"  {Colors.CYAN}4.{Colors.END} Cancel")

            choice = input(f"\n{Colors.CYAN}Select: {Colors.END}").strip()

            if choice == "1":
                for vk in stuck_keys:
                    sc = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
                    if sc > 0:
                        self.current_mappings[sc] = 0x0000
                print_success(f"Added {len(stuck_keys)} key(s) to disable list")
                print_warning("Apply registry changes and reboot to take effect")
            elif choice == "2":
                self.disabled_vks.update(stuck_keys)
                if not self.hook_active:
                    self._start_hook()
                print_success(f"Disabled {len(stuck_keys)} key(s) via session hook")
                print_info("Keys are disabled immediately. Hook will remain active until you exit.")
            elif choice == "3":
                for vk in stuck_keys:
                    sc = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
                    print(f"\nRemap {get_vk_name(vk)} to which key?")
                    new_key = input(f"  {Colors.CYAN}Target key: {Colors.END}").strip().upper()
                    new_sc = self._parse_scancode(new_key)
                    if new_sc:
                        self.current_mappings[sc] = new_sc
                        print_success(f"Will remap {get_vk_name(vk)} → {get_scancode_name(new_sc)}")
                    else:
                        print_error("Invalid target, skipping")
                print_warning("Apply registry changes and reboot to take effect")
        else:
            print_success("No stuck keys detected!")

    def _session_hook_menu(self):
        print_banner("SESSION HOOK REMAPPER", Colors.CYAN)
        print(f"""
{Colors.YELLOW}This creates a temporary, session-only key remap using a low-level{Colors.END}
{Colors.YELLOW}keyboard hook. No admin or reboot required, but only affects{Colors.END}
{Colors.YELLOW}the current user session.{Colors.END}

{Colors.GRAY}Status: {Colors.GREEN if self.hook_active else Colors.RED}{'ACTIVE' if self.hook_active else 'INACTIVE'}{Colors.END}
""")

        print(f"{Colors.CYAN}1.{Colors.END} Add hook mapping")
        print(f"{Colors.CYAN}2.{Colors.END} Remove hook mapping")
        print(f"{Colors.CYAN}3.{Colors.END} Disable key via hook")
        print(f"{Colors.CYAN}4.{Colors.END} Start hook")
        print(f"{Colors.CYAN}5.{Colors.END} Stop hook")
        print(f"{Colors.CYAN}0.{Colors.END} Back")

        choice = input(f"\n{Colors.CYAN}Select: {Colors.END}").strip()

        if choice == "1":
            src = input(f"{Colors.CYAN}Source VK name/hex: {Colors.END}").strip().upper()
            tgt = input(f"{Colors.CYAN}Target VK name/hex: {Colors.END}").strip().upper()
            src_vk = self._parse_vk(src)
            tgt_vk = self._parse_vk(tgt)
            if src_vk and tgt_vk:
                self.hook_mappings[src_vk] = tgt_vk
                print_success(f"Hook mapping added: {get_vk_name(src_vk)} → {get_vk_name(tgt_vk)}")
            else:
                print_error("Invalid key code")
        elif choice == "2":
            if not self.hook_mappings:
                print_warning("No hook mappings")
                return
            for i, (src, tgt) in enumerate(self.hook_mappings.items(), 1):
                print(f"  {i}. {get_vk_name(src)} → {get_vk_name(tgt)}")
            idx = input("Remove which: ").strip()
            try:
                key = list(self.hook_mappings.keys())[int(idx)-1]
                del self.hook_mappings[key]
                print_success("Removed")
            except:
                print_error("Invalid")
        elif choice == "3":
            key = input(f"{Colors.CYAN}Key to disable (VK name/hex): {Colors.END}").strip().upper()
            vk = self._parse_vk(key)
            if vk:
                self.disabled_vks.add(vk)
                print_success(f"Will disable {get_vk_name(vk)} via hook")
            else:
                print_error("Invalid key")
        elif choice == "4":
            self._start_hook()
        elif choice == "5":
            self._stop_hook()

    def _start_hook(self):
        if self.hook_active:
            print_warning("Hook already active")
            return

        try:
            self.hook_active = True
            self.hook_thread = threading.Thread(target=self._hook_thread, daemon=True)
            self.hook_thread.start()
            print_success("Session hook started")
            print_info("Hook is running in background. Keys will be remapped/disabled.")
        except Exception as e:
            print_error(f"Failed to start hook: {e}")
            self.hook_active = False

    def _stop_hook(self):
        if not self.hook_active:
            print_warning("Hook not active")
            return

        self.hook_active = False
        if self.hook_handle:
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None
        print_success("Session hook stopped")

    def _hook_thread(self):
        # Low-level keyboard hook callback
        WH_KEYBOARD_LL = 13
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        WM_SYSKEYDOWN = 0x0104
        WM_SYSKEYUP = 0x0105

        @ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        def hook_proc(nCode, wParam, lParam):
            if nCode >= 0:
                kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kb_struct.vkCode

                if vk in self.disabled_vks:
                    return 1  # Block key

                if vk in self.hook_mappings and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    # Inject target key instead
                    target_vk = self.hook_mappings[vk]
                    self._inject_key(target_vk)
                    return 1  # Block original

            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        self.hook_callback = hook_proc
        self.hook_handle = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, hook_proc, ctypes.windll.kernel32.GetModuleHandleW(None), 0
        )

        if not self.hook_handle:
            self.hook_active = False
            return

        # Message loop
        msg = ctypes.wintypes.MSG()
        while self.hook_active:
            bRet = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if bRet == 0 or bRet == -1:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    def _inject_key(self, vk):
        INPUT_KEYBOARD = 1
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.wintypes.WORD),
                ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
            ]

        class INPUT_I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.wintypes.DWORD), ("_input", INPUT_I)]
            _anonymous_ = ("_input",)

        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.wScan = 0
        inp.ki.dwFlags = 0
        inp.ki.time = 0
        inp.ki.dwExtraInfo = None

        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        # Key up
        inp.ki.dwFlags = KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _show_scancode_reference(self):
        print_banner("SCANCODE REFERENCE TABLE", Colors.CYAN)
        print(f"{Colors.BOLD}{'Name':<15} {'Scancode':<10} {'Name':<15} {'Scancode':<10} {'Name':<15} {'Scancode':<10}{Colors.END}")
        print(f"{Colors.GRAY}{'─' * 75}{Colors.END}")

        items = sorted(SCANCODES.items(), key=lambda x: x[1])
        for i in range(0, len(items), 3):
            row = items[i:i+3]
            parts = []
            for name, sc in row:
                parts.append(f"{Colors.WHITE}{name:<15}{Colors.END}{Colors.GRAY}0x{sc:02X}{Colors.END}")
            print("  ".join(parts))

        print(f"\n{Colors.YELLOW}Tip: Use the key name (e.g., 'CAPS') or hex value (e.g., '0x3A') when prompted.{Colors.END}")
        prompt_continue()

    def _parse_scancode(self, text):
        text = text.strip().upper()
        if text.startswith("0X"):
            try:
                return int(text, 16)
            except ValueError:
                return None
        return SCANCODES.get(text)

    def _parse_vk(self, text):
        text = text.strip().upper()
        if text.startswith("0X"):
            try:
                return int(text, 16)
            except ValueError:
                return None
        # Reverse lookup in VK_CODES
        for vk, name in get_vk_name.__globals__.get("VK_CODES", {}).items():
            if name == text:
                return vk
        # Try scancode name
        sc = SCANCODES.get(text)
        if sc:
            return ctypes.windll.user32.MapVirtualKeyW(sc, 3)  # MAPVK_VSC_TO_VK_EX
        return None


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
    ]


def main():
    remapper = KeyRemapper()
    remapper.run()

if __name__ == "__main__":
    main()
