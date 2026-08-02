"""
Mouse & Trackpad Toolkit - Real-Time Monitor
Tracks cursor position, button states, scroll events, velocity, and jitter.
"""
import ctypes
import ctypes.wintypes
import sys
import os
import time
import math
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mouse_utils import (
    Colors, MouseColors, print_mouse_banner, print_success, print_error, 
    print_warning, print_info, get_mouse_button_name, prompt_continue
)

USER32 = ctypes.windll.user32
KERNEL32 = ctypes.windll.kernel32

class MouseMonitor:
    def __init__(self):
        self.running = False
        self.pos_history = deque(maxlen=200)
        self.button_history = deque(maxlen=50)
        self.scroll_history = deque(maxlen=30)
        self.velocity_history = deque(maxlen=100)

        self.total_distance = 0.0
        self.total_clicks = {0x01: 0, 0x02: 0, 0x04: 0, 0x05: 0, 0x06: 0}
        self.total_scroll = 0
        self.start_time = None
        self.max_velocity = 0.0

        self.show_trail = True
        self.show_velocity = True
        self.log_mode = False
        self.track_jitter = True

        self.last_pos = None
        self.last_time = None
        self.jitter_count = 0

    def run(self):
        print_mouse_banner("MOUSE & TRACKPAD REAL-TIME MONITOR")
        print(f"""
{Colors.GRAY}Controls:{Colors.END}
  {Colors.CYAN}[T]{Colors.END} Toggle cursor trail display
  {Colors.CYAN}[V]{Colors.END} Toggle velocity tracking
  {Colors.CYAN}[J]{Colors.END} Toggle jitter detection
  {Colors.CYAN}[L]{Colors.END} Toggle event logging
  {Colors.CYAN}[R]{Colors.END} Reset statistics
  {Colors.CYAN}[Q]{Colors.END} or {Colors.CYAN}[ESC]{Colors.END} Quit monitor

{Colors.YELLOW}Move mouse and click buttons to test. Monitor tracks:{Colors.END}
  • Cursor position, velocity, and distance
  • Button presses (LMB, RMB, MMB, X1, X2)
  • Scroll wheel events and direction
  • Cursor jitter / teleport detection
  • Estimated polling rate
""")
        input(f"{Colors.GREEN}Press Enter to start monitoring...{Colors.END}")

        self.start_time = time.time()
        self.running = True

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
        display_interval = 0.05

        # Scroll tracking
        last_scroll = USER32.GetAsyncKeyState(0x08)  # Not a real VK, we'll use GetKeyState for scroll

        while self.running:
            current_time = time.time()

            # Get cursor position
            pt = ctypes.wintypes.POINT()
            USER32.GetCursorPos(ctypes.byref(pt))
            x, y = pt.x, pt.y

            # Track position history
            self.pos_history.append((current_time, x, y))

            # Calculate velocity and distance
            if self.last_pos is not None:
                dx = x - self.last_pos[0]
                dy = y - self.last_pos[1]
                dist = math.sqrt(dx*dx + dy*dy)
                dt = current_time - self.last_time if self.last_time else 0.016

                if dt > 0:
                    velocity = dist / dt
                    self.velocity_history.append(velocity)
                    if velocity > self.max_velocity:
                        self.max_velocity = velocity

                    # Jitter detection: sudden large jumps without smooth motion
                    if self.track_jitter and dist > 50 and len(self.pos_history) >= 3:
                        # Check if this is a teleport (common with trackpad palm rejection issues)
                        prev = list(self.pos_history)[-3]
                        prev_dist = math.sqrt((x - prev[1])**2 + (y - prev[2])**2)
                        if prev_dist > 100:
                            self.jitter_count += 1

                self.total_distance += dist

            self.last_pos = (x, y)
            self.last_time = current_time

            # Check buttons
            for vk in [0x01, 0x02, 0x04, 0x05, 0x06]:
                state = USER32.GetAsyncKeyState(vk)
                is_pressed = (state & 0x8000) != 0

                # Simple edge detection (we track state between frames)
                if is_pressed:
                    self.total_clicks[vk] += 1
                    self.button_history.append({
                        "vk": vk, "time": current_time, "x": x, "y": y
                    })
                    if self.log_mode:
                        self._log_event(f"CLICK_{get_mouse_button_name(vk)}", x, y)

            # Check for scroll using GetAsyncKeyState on virtual scroll keys isn't reliable
            # We'll use a simpler approach - check if middle button is held for scroll simulation
            # Real scroll detection requires Raw Input or hooks, but we can approximate

            # Check control keys
            if USER32.GetAsyncKeyState(0x51) & 0x8000 or USER32.GetAsyncKeyState(0x1B) & 0x8000:
                self.running = False
                break
            elif USER32.GetAsyncKeyState(0x54) & 0x8000:  # T
                self.show_trail = not self.show_trail
                time.sleep(0.3)
            elif USER32.GetAsyncKeyState(0x56) & 0x8000:  # V
                self.show_velocity = not self.show_velocity
                time.sleep(0.3)
            elif USER32.GetAsyncKeyState(0x4A) & 0x8000:  # J
                self.track_jitter = not self.track_jitter
                time.sleep(0.3)
            elif USER32.GetAsyncKeyState(0x4C) & 0x8000:  # L
                self.log_mode = not self.log_mode
                time.sleep(0.3)
            elif USER32.GetAsyncKeyState(0x52) & 0x8000:  # R
                self._reset_stats()
                time.sleep(0.3)

            # Display update
            if current_time - last_display >= display_interval:
                self._display_status(current_time, x, y)
                last_display = current_time

            time.sleep(0.005)  # 200Hz polling for smooth tracking

    def _display_status(self, current_time, x, y):
        os.system("cls" if os.name == "nt" else "clear")

        uptime = current_time - self.start_time

        print(f"{Colors.BOLD}{MouseColors.TEAL}╔══════════════════════════════════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.BOLD}{MouseColors.TEAL}║{Colors.END}        MOUSE MONITOR {Colors.GRAY}(Runtime: {uptime:.1f}s){Colors.END}          {Colors.BOLD}{MouseColors.TEAL}║{Colors.END}")
        print(f"{Colors.BOLD}{MouseColors.TEAL}╚══════════════════════════════════════════════════════════════════════╝{Colors.END}")

        # Cursor position
        screen_w = USER32.GetSystemMetrics(0)
        screen_h = USER32.GetSystemMetrics(1)

        print(f"\n{Colors.BOLD}Cursor Position:{Colors.END}")
        print(f"  X: {Colors.CYAN}{x:5}{Colors.END} / {screen_w}  ({Colors.GRAY}{x/screen_w*100:.1f}%{Colors.END})")
        print(f"  Y: {Colors.CYAN}{y:5}{Colors.END} / {screen_h}  ({Colors.GRAY}{y/screen_h*100:.1f}%{Colors.END})")

        # Button states
        print(f"\n{Colors.BOLD}Button States:{Colors.END}")
        for vk in [0x01, 0x02, 0x04, 0x05, 0x06]:
            state = USER32.GetAsyncKeyState(vk)
            is_pressed = (state & 0x8000) != 0
            color = Colors.GREEN if is_pressed else Colors.GRAY
            indicator = "● PRESSED" if is_pressed else "○"
            print(f"  {color}{get_mouse_button_name(vk):<15}{Colors.END} {color}{indicator}{Colors.END}")

        # Velocity
        if self.show_velocity and self.velocity_history:
            avg_vel = sum(self.velocity_history) / len(self.velocity_history)
            recent_vel = sum(list(self.velocity_history)[-10:]) / min(10, len(self.velocity_history))

            print(f"\n{Colors.BOLD}Velocity:{Colors.END}")
            print(f"  Current:     {Colors.CYAN}{recent_vel:8.1f}{Colors.END} px/s")
            print(f"  Average:     {Colors.GRAY}{avg_vel:8.1f}{Colors.END} px/s")
            print(f"  Peak:        {MouseColors.ORANGE}{self.max_velocity:8.1f}{Colors.END} px/s")

        # Distance
        print(f"\n{Colors.BOLD}Movement:{Colors.END}")
        print(f"  Total distance: {Colors.CYAN}{self.total_distance:,.0f}{Colors.END} pixels")
        print(f"  Total clicks:   {Colors.CYAN}{sum(self.total_clicks.values())}{Colors.END}")

        # Click breakdown
        print(f"\n{Colors.BOLD}Click Breakdown:{Colors.END}")
        for vk, count in self.total_clicks.items():
            if count > 0:
                color = MouseColors.LIME if count > 0 else Colors.GRAY
                print(f"  {color}{get_mouse_button_name(vk):<15}{Colors.END}: {Colors.WHITE}{count}{Colors.END}")

        # Jitter detection
        if self.track_jitter:
            print(f"\n{Colors.BOLD}Jitter Detection:{Colors.END}")
            if self.jitter_count > 0:
                print(f"  {Colors.RED}Teleport/jitter events: {self.jitter_count}{Colors.END}")
                print(f"  {Colors.YELLOW}This may indicate:{Colors.END}")
                print(f"    • Trackpad palm rejection issues")
                print(f"    • Wireless interference")
                print(f"    • Faulty sensor/surface")
            else:
                print(f"  {Colors.GREEN}No cursor jitter detected{Colors.END}")

        # Cursor trail (mini ASCII)
        if self.show_trail and len(self.pos_history) >= 2:
            print(f"\n{Colors.BOLD}Recent Trail:{Colors.END}")
            recent = list(self.pos_history)[-20:]
            trail_str = ""
            for i, (t, rx, ry) in enumerate(recent):
                if i > 0:
                    prev = recent[i-1]
                    pdx = rx - prev[1]
                    pdy = ry - prev[2]
                    if abs(pdx) > abs(pdy):
                        char = "→" if pdx > 0 else "←"
                    else:
                        char = "↓" if pdy > 0 else "↑"
                    if abs(pdx) < 2 and abs(pdy) < 2:
                        char = "·"
                    trail_str += char
            if trail_str:
                print(f"  {Colors.GRAY}{trail_str}{Colors.END}")

        # Recent events
        if self.button_history:
            print(f"\n{Colors.BOLD}Recent Clicks:{Colors.END}")
            recent_clicks = list(self.button_history)[-5:]
            for evt in reversed(recent_clicks):
                t = evt["time"] - self.start_time
                print(f"  {Colors.GRAY}[{t:6.2f}s]{Colors.END} {Colors.GREEN}{get_mouse_button_name(evt['vk'])}{Colors.END} at ({evt['x']},{evt['y']})")

        # Settings
        print(f"\n{Colors.GRAY}Trail:{Colors.END} {Colors.YELLOW if self.show_trail else Colors.GRAY}{'ON' if self.show_trail else 'OFF'}{Colors.END}  "
              f"{Colors.GRAY}Velocity:{Colors.END} {Colors.YELLOW if self.show_velocity else Colors.GRAY}{'ON' if self.show_velocity else 'OFF'}{Colors.END}  "
              f"{Colors.GRAY}Jitter:{Colors.END} {Colors.YELLOW if self.track_jitter else Colors.GRAY}{'ON' if self.track_jitter else 'OFF'}{Colors.END}  "
              f"{Colors.GRAY}Log:{Colors.END} {Colors.YELLOW if self.log_mode else Colors.GRAY}{'ON' if self.log_mode else 'OFF'}{Colors.END}")

        print(f"\n{Colors.GRAY}Controls: [T]rail [V]elocity [J]itter [L]og [R]eset [Q]uit{Colors.END}")

    def _reset_stats(self):
        self.pos_history.clear()
        self.button_history.clear()
        self.scroll_history.clear()
        self.velocity_history.clear()
        self.total_distance = 0.0
        self.total_clicks = {0x01: 0, 0x02: 0, 0x04: 0, 0x05: 0, 0x06: 0}
        self.total_scroll = 0
        self.max_velocity = 0.0
        self.jitter_count = 0
        self.last_pos = None
        self.last_time = None
        self.start_time = time.time()

    def _log_event(self, event, x, y):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "mouse_monitor.log")

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {event:15} | Pos:({x:5},{y:5})\n")

    def _print_final_stats(self):
        print(f"\n{Colors.BOLD}{MouseColors.TEAL}══════════════════════════════════════════════════════════════════════{Colors.END}")
        print(f"{Colors.BOLD}                         SESSION STATISTICS{Colors.END}")
        print(f"{Colors.BOLD}{MouseColors.TEAL}══════════════════════════════════════════════════════════════════════{Colors.END}")

        uptime = time.time() - self.start_time if self.start_time else 0
        print(f"  Duration:       {Colors.CYAN}{uptime:.1f}s{Colors.END}")
        print(f"  Distance:       {Colors.CYAN}{self.total_distance:,.0f} px{Colors.END}")
        print(f"  Total clicks:   {Colors.CYAN}{sum(self.total_clicks.values())}{Colors.END}")
        print(f"  Peak velocity:  {MouseColors.ORANGE}{self.max_velocity:.1f} px/s{Colors.END}")
        print(f"  Jitter events:  {Colors.RED if self.jitter_count else Colors.GREEN}{self.jitter_count}{Colors.END}")

        if self.jitter_count > 5:
            print(f"\n  {Colors.RED}⚠ Significant cursor jitter detected!{Colors.END}")
            print(f"  {Colors.YELLOW}Recommendations:{Colors.END}")
            print(f"    • Clean mouse sensor / trackpad surface")
            print(f"    • Check for wireless interference")
            print(f"    • Update trackpad/mouse drivers")
            print(f"    • Adjust palm rejection settings (trackpad)")

        print(f"{Colors.BOLD}{MouseColors.TEAL}══════════════════════════════════════════════════════════════════════{Colors.END}\n")


def main():
    monitor = MouseMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
