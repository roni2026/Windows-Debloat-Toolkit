"""
KB Toolkit - Real-Time Key Monitor
Displays live key press states, detects stuck keys, and shows scancode info.
"""
import ctypes
import ctypes.wintypes
import sys
import os
import time
import threading
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success, 
    print_error, print_warning, print_info, get_vk_name, get_scancode_name, prompt_continue
)

# Windows API constants
USER32 = ctypes.windll.user32
KERNEL32 = ctypes.windll.kernel32

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02

class KeyMonitor:
    def __init__(self):
        self.running = False
        self.pressed_keys = set()
        self.key_history = deque(maxlen=50)
        self.stuck_threshold = 3.0  # seconds
        self.key_hold_time = defaultdict(float)
        self.stuck_detected = set()
        self.total_presses = 0
        self.start_time = None
        self.lock = threading.Lock()
        self.show_scancodes = False
        self.show_vk = True
        self.log_mode = False
        self.filter_mouse = True

    def run(self):
        print_banner("REAL-TIME KEYBOARD MONITOR", Colors.GREEN)
        print(f"""
{Colors.GRAY}Controls:{Colors.END}
  {Colors.CYAN}[S]{Colors.END} Toggle scancode display
  {Colors.CYAN}[V]{Colors.END} Toggle VK code display  
  {Colors.CYAN}[M]{Colors.END} Toggle mouse button monitoring
  {Colors.CYAN}[L]{Colors.END} Toggle key logging to file
  {Colors.CYAN}[R]{Colors.END} Reset statistics
  {Colors.CYAN}[Q]{Colors.END} or {Colors.CYAN}[ESC]{Colors.END} Quit monitor

{Colors.YELLOW}Stuck key detection threshold: {self.stuck_threshold}s{Colors.END}
{Colors.YELLOW}Press any key to begin monitoring...{Colors.END}
""")
        input()

        self.start_time = time.time()
        self.running = True

        # Start input listener thread
        input_thread = threading.Thread(target=self._input_listener, daemon=True)
        input_thread.start()

        try:
            self._monitor_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self._print_final_stats()
            prompt_continue()

    def _monitor_loop(self):
        last_display = 0
        display_interval = 0.05  # 20Hz refresh

        while self.running:
            current_time = time.time()

            # Poll all keys 0x01 to 0xFF
            newly_pressed = set()
            newly_released = set()

            for vk in range(1, 256):
                if self.filter_mouse and vk in (VK_LBUTTON, VK_RBUTTON, 0x04, 0x05, 0x06):
                    continue

                state = USER32.GetAsyncKeyState(vk)
                is_pressed = (state & 0x8000) != 0

                with self.lock:
                    was_pressed = vk in self.pressed_keys

                    if is_pressed and not was_pressed:
                        newly_pressed.add(vk)
                        self.pressed_keys.add(vk)
                        self.key_hold_time[vk] = current_time
                        self.total_presses += 1

                        # Get scancode
                        scancode = USER32.MapVirtualKeyW(vk, 0)
                        self.key_history.append({
                            "vk": vk, "scancode": scancode, 
                            "time": current_time, "event": "DOWN"
                        })

                        if self.log_mode:
                            self._log_event(vk, scancode, "DOWN")

                    elif not is_pressed and was_pressed:
                        newly_released.add(vk)
                        self.pressed_keys.discard(vk)
                        self.stuck_detected.discard(vk)

                        if vk in self.key_hold_time:
                            del self.key_hold_time[vk]

                        scancode = USER32.MapVirtualKeyW(vk, 0)
                        self.key_history.append({
                            "vk": vk, "scancode": scancode,
                            "time": current_time, "event": "UP"
                        })

                        if self.log_mode:
                            self._log_event(vk, scancode, "UP")

            # Check for stuck keys
            with self.lock:
                for vk in list(self.pressed_keys):
                    if vk in self.key_hold_time:
                        hold_duration = current_time - self.key_hold_time[vk]
                        if hold_duration > self.stuck_threshold:
                            self.stuck_detected.add(vk)

            # Display update
            if current_time - last_display >= display_interval:
                self._display_status(current_time)
                last_display = current_time

            time.sleep(0.01)  # 100Hz polling

    def _display_status(self, current_time):
        # Clear screen (Windows)
        KERNEL32.GetStdHandle(-11)
        os.system("cls" if os.name == "nt" else "clear")

        uptime = current_time - self.start_time

        print(f"{Colors.BOLD}{Colors.GREEN}╔══════════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}║{Colors.END}           KEYBOARD MONITOR {Colors.GRAY}(Runtime: {uptime:.1f}s){Colors.END}           {Colors.BOLD}{Colors.GREEN}║{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}╚══════════════════════════════════════════════════════════════════════╝{Colors.END}")

        # Currently pressed keys
        print(f"\n{Colors.BOLD}Currently Pressed:{Colors.END}")
        with self.lock:
            if self.pressed_keys:
                keys_display = []
                for vk in sorted(self.pressed_keys):
                    name = get_vk_name(vk)
                    hold = current_time - self.key_hold_time.get(vk, current_time)

                    if vk in self.stuck_detected:
                        color = Colors.BG_RED + Colors.WHITE
                        status = " STUCK!"
                    elif hold > 1.0:
                        color = Colors.YELLOW
                        status = f" ({hold:.1f}s)"
                    else:
                        color = Colors.GREEN
                        status = ""

                    info = name
                    if self.show_vk:
                        info += f"[VK:{vk:02X}]"
                    if self.show_scancodes:
                        sc = USER32.MapVirtualKeyW(vk, 0)
                        info += f"[SC:{sc:02X}]"

                    keys_display.append(f"{color}{info}{status}{Colors.END}")

                # Print in rows of 4
                for i in range(0, len(keys_display), 4):
                    row = keys_display[i:i+4]
                    print("  " + "  │  ".join(row))
            else:
                print(f"  {Colors.GRAY}(No keys currently pressed){Colors.END}")

        # Stuck keys alert
        with self.lock:
            if self.stuck_detected:
                print(f"\n{Colors.BG_RED}{Colors.WHITE} ⚠ STUCK KEYS DETECTED ⚠ {Colors.END}")
                for vk in self.stuck_detected:
                    hold = current_time - self.key_hold_time.get(vk, current_time)
                    print(f"  {Colors.RED}• {get_vk_name(vk)} held for {hold:.1f} seconds{Colors.END}")

        # Statistics
        print(f"\n{Colors.BOLD}Statistics:{Colors.END}")
        print(f"  Total key presses: {Colors.CYAN}{self.total_presses}{Colors.END}")
        print(f"  Currently held:    {Colors.CYAN}{len(self.pressed_keys)}{Colors.END}")
        print(f"  Stuck detected:    {Colors.RED if self.stuck_detected else Colors.GREEN}{len(self.stuck_detected)}{Colors.END}")
        print(f"  Scancodes:         {Colors.YELLOW if self.show_scancodes else Colors.GRAY}{'ON' if self.show_scancodes else 'OFF'}{Colors.END}")
        print(f"  VK codes:          {Colors.YELLOW if self.show_vk else Colors.GRAY}{'ON' if self.show_vk else 'OFF'}{Colors.END}")
        print(f"  Mouse buttons:     {Colors.YELLOW if not self.filter_mouse else Colors.GRAY}{'ON' if not self.filter_mouse else 'OFF'}{Colors.END}")
        print(f"  Logging:           {Colors.YELLOW if self.log_mode else Colors.GRAY}{'ON' if self.log_mode else 'OFF'}{Colors.END}")

        # Recent history
        print(f"\n{Colors.BOLD}Recent Events (last 10):{Colors.END}")
        with self.lock:
            recent = list(self.key_history)[-10:]
            for evt in recent:
                vk = evt["vk"]
                name = get_vk_name(vk)
                sc = evt["scancode"]
                ev = evt["event"]
                t = evt["time"] - self.start_time

                ev_color = Colors.GREEN if ev == "DOWN" else Colors.RED
                sc_info = f" SC:{sc:02X}" if self.show_scancodes else ""
                vk_info = f" VK:{vk:02X}" if self.show_vk else ""

                print(f"  {Colors.GRAY}[{t:6.2f}s]{Colors.END} {ev_color}{ev:5}{Colors.END} {Colors.WHITE}{name:12}{Colors.END}{vk_info}{sc_info}")

        print(f"\n{Colors.GRAY}Controls: [S]cancode [V]K [M]ouse [L]og [R]eset [Q]uit{Colors.END}")

    def _input_listener(self):
        while self.running:
            try:
                # Check for control keys using GetAsyncKeyState
                time.sleep(0.1)

                if USER32.GetAsyncKeyState(0x51) & 0x8000 or USER32.GetAsyncKeyState(0x1B) & 0x8000:
                    self.running = False
                    break
                elif USER32.GetAsyncKeyState(0x53) & 0x8000:  # S
                    self.show_scancodes = not self.show_scancodes
                    time.sleep(0.3)
                elif USER32.GetAsyncKeyState(0x56) & 0x8000:  # V
                    self.show_vk = not self.show_vk
                    time.sleep(0.3)
                elif USER32.GetAsyncKeyState(0x4D) & 0x8000:  # M
                    self.filter_mouse = not self.filter_mouse
                    time.sleep(0.3)
                elif USER32.GetAsyncKeyState(0x4C) & 0x8000:  # L
                    self.log_mode = not self.log_mode
                    time.sleep(0.3)
                elif USER32.GetAsyncKeyState(0x52) & 0x8000:  # R
                    self._reset_stats()
                    time.sleep(0.3)
            except:
                pass

    def _reset_stats(self):
        with self.lock:
            self.pressed_keys.clear()
            self.key_history.clear()
            self.key_hold_time.clear()
            self.stuck_detected.clear()
            self.total_presses = 0
            self.start_time = time.time()

    def _log_event(self, vk, scancode, event):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "key_monitor.log")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        name = get_vk_name(vk)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {event:5} | {name:12} | VK:0x{vk:02X} | SC:0x{scancode:02X}\n")

    def _print_final_stats(self):
        print(f"\n{Colors.BOLD}{Colors.GREEN}══════════════════════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.BOLD}                         SESSION STATISTICS{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}══════════════════════════════════════════════════════════════════════{Colors.END}")

        uptime = time.time() - self.start_time if self.start_time else 0
        print(f"  Session duration:  {Colors.CYAN}{uptime:.1f}s{Colors.END}")
        print(f"  Total presses:     {Colors.CYAN}{self.total_presses}{Colors.END}")
        print(f"  Stuck events:      {Colors.RED if self.stuck_detected else Colors.GREEN}{len(self.stuck_detected)}{Colors.END}")

        if self.stuck_detected:
            print(f"\n  {Colors.RED}Stuck keys detected during session:{Colors.END}")
            for vk in self.stuck_detected:
                print(f"    • {get_vk_name(vk)} (VK:0x{vk:02X})")

        print(f"{Colors.BOLD}{Colors.GREEN}══════════════════════════════════════════════════════════════════════{Colors.END}\n")


def main():
    monitor = KeyMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
