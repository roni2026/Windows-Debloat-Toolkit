"""
KB Toolkit - Shared Utilities
Common helpers, styling, logging, and Windows API wrappers.
"""
import ctypes
import ctypes.wintypes
import sys
import os
import logging
from datetime import datetime
from enum import IntEnum

# Windows constants
VK_CODES = {
    0x01: "LMB", 0x02: "RMB", 0x03: "CANCEL", 0x04: "MMB",
    0x05: "X1MB", 0x06: "X2MB", 0x08: "BACK", 0x09: "TAB",
    0x0C: "CLEAR", 0x0D: "ENTER", 0x10: "SHIFT", 0x11: "CTRL",
    0x12: "ALT", 0x13: "PAUSE", 0x14: "CAPS", 0x1B: "ESC",
    0x20: "SPACE", 0x21: "PGUP", 0x22: "PGDN", 0x23: "END",
    0x24: "HOME", 0x25: "LEFT", 0x26: "UP", 0x27: "RIGHT",
    0x28: "DOWN", 0x2C: "PRTSC", 0x2D: "INSERT", 0x2E: "DELETE",
    0x2F: "HELP", 0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3",
    0x34: "4", 0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8",
    0x39: "9", 0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D",
    0x45: "E", 0x46: "F", 0x47: "G", 0x48: "H", 0x49: "I",
    0x4A: "J", 0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N",
    0x4F: "O", 0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S",
    0x54: "T", 0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X",
    0x59: "Y", 0x5A: "Z", 0x5B: "LWIN", 0x5C: "RWIN",
    0x5D: "APPS", 0x60: "NUM0", 0x61: "NUM1", 0x62: "NUM2",
    0x63: "NUM3", 0x64: "NUM4", 0x65: "NUM5", 0x66: "NUM6",
    0x67: "NUM7", 0x68: "NUM8", 0x69: "NUM9", 0x6A: "MULT",
    0x6B: "ADD", 0x6C: "SEP", 0x6D: "SUB", 0x6E: "DEC",
    0x6F: "DIV", 0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8", 0x78: "F9",
    0x79: "F10", 0x7A: "F11", 0x7B: "F12", 0x7C: "F13",
    0x7D: "F14", 0x7E: "F15", 0x7F: "F16", 0x80: "F17",
    0x81: "F18", 0x82: "F19", 0x83: "F20", 0x84: "F21",
    0x85: "F22", 0x86: "F23", 0x87: "F24", 0x90: "NUMLOCK",
    0x91: "SCROLL", 0xA0: "LSHIFT", 0xA1: "RSHIFT",
    0xA2: "LCTRL", 0xA3: "RCTRL", 0xA4: "LALT", 0xA5: "RALT",
    0xAD: "VOL_MUTE", 0xAE: "VOL_DOWN", 0xAF: "VOL_UP",
    0xB0: "MEDIA_NEXT", 0xB1: "MEDIA_PREV", 0xB2: "MEDIA_STOP",
    0xB3: "MEDIA_PLAY", 0xBA: "SEMICOLON", 0xBB: "PLUS",
    0xBC: "COMMA", 0xBD: "MINUS", 0xBE: "PERIOD", 0xBF: "SLASH",
    0xC0: "TILDE", 0xDB: "LBRACKET", 0xDC: "BACKSLASH",
    0xDD: "RBRACKET", 0xDE: "QUOTE", 0xDF: "OEM_8",
    0xE2: "BACKSLASH_102", 0xE5: "PROCESSKEY",
    0xF6: "ATTN", 0xF7: "CRSEL", 0xF8: "EXSEL", 0xF9: "EREOF",
    0xFA: "PLAY", 0xFB: "ZOOM", 0xFE: "PA1"
}

# Common scancodes for remapping (Set 1 Make codes)
SCANCODES = {
    "ESC": 0x01, "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05,
    "5": 0x06, "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A,
    "0": 0x0B, "MINUS": 0x0C, "PLUS": 0x0D, "BACK": 0x0E,
    "TAB": 0x0F, "Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13,
    "T": 0x14, "Y": 0x15, "U": 0x16, "I": 0x17, "O": 0x18,
    "P": 0x19, "LBRACKET": 0x1A, "RBRACKET": 0x1B, "ENTER": 0x1C,
    "LCTRL": 0x1D, "A": 0x1E, "S": 0x1F, "D": 0x20, "F": 0x21,
    "G": 0x22, "H": 0x23, "J": 0x24, "K": 0x25, "L": 0x26,
    "SEMICOLON": 0x27, "QUOTE": 0x28, "TILDE": 0x29, "LSHIFT": 0x2A,
    "BACKSLASH": 0x2B, "Z": 0x2C, "X": 0x2D, "C": 0x2E, "V": 0x2F,
    "B": 0x30, "N": 0x31, "M": 0x32, "COMMA": 0x33, "PERIOD": 0x34,
    "SLASH": 0x35, "RSHIFT": 0x36, "NUMMULT": 0x37, "LALT": 0x38,
    "SPACE": 0x39, "CAPS": 0x3A, "F1": 0x3B, "F2": 0x3C, "F3": 0x3D,
    "F4": 0x3E, "F5": 0x3F, "F6": 0x40, "F7": 0x41, "F8": 0x42,
    "F9": 0x43, "F10": 0x44, "NUMLOCK": 0x45, "SCROLL": 0x46,
    "NUM7": 0x47, "NUM8": 0x48, "NUM9": 0x49, "NUMSUB": 0x4A,
    "NUM4": 0x4B, "NUM5": 0x4C, "NUM6": 0x4D, "NUMADD": 0x4E,
    "NUM1": 0x4F, "NUM2": 0x50, "NUM3": 0x51, "NUM0": 0x52,
    "NUMDEC": 0x53, "F11": 0x57, "F12": 0x58, "F13": 0x64,
    "F14": 0x65, "F15": 0x66, "F16": 0x67, "F17": 0x68,
    "F18": 0x69, "F19": 0x6A, "F20": 0x6B, "F21": 0x6C,
    "F22": 0x6D, "F23": 0x6E, "F24": 0x76, "NUMENTER": 0x11C,
    "RCTRL": 0x11D, "NUMDIV": 0x135, "PRTSC": 0x137, "RALT": 0x138,
    "HOME": 0x147, "UP": 0x148, "PGUP": 0x149, "LEFT": 0x14B,
    "RIGHT": 0x14D, "END": 0x14F, "DOWN": 0x150, "PGDN": 0x151,
    "INSERT": 0x152, "DELETE": 0x153, "LWIN": 0x15B, "RWIN": 0x15C,
    "APPS": 0x15D, "PAUSE": 0x21D, "MEDIA_NEXT": 0x119,
    "MEDIA_PREV": 0x110, "MEDIA_STOP": 0x124, "MEDIA_PLAY": 0x122,
    "VOL_MUTE": 0x120, "VOL_DOWN": 0x12E, "VOL_UP": 0x130
}

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    MAGENTA = "\033[95m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"

def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"kb_toolkit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def print_banner(title, color=Colors.CYAN):
    width = 70
    print(f"\n{color}{'═' * width}{Colors.END}")
    print(f"{color}{'║':<1}{title:^{width-2}}{'║':>1}{Colors.END}")
    print(f"{color}{'═' * width}{Colors.END}\n")

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.END}")
    print(f"{Colors.GRAY}{'─' * 60}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")

def get_vk_name(vk_code):
    return VK_CODES.get(vk_code, f"VK_{vk_code:02X}")

def get_scancode_name(code):
    for name, sc in SCANCODES.items():
        if sc == code:
            return name
    return f"0x{code:03X}"

def prompt_continue():
    input(f"\n{Colors.GRAY}Press Enter to continue...{Colors.END}")

def format_bytes(size):
    """Human-readable byte size, e.g. 1536 -> '1.5 KB'."""
    try:
        size = float(size)
    except (TypeError, ValueError):
        return str(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def print_progress_bar(current, total, prefix="", suffix="", length=36, fill="█", empty="░"):
    """
    Renders/updates a single-line progress bar in place using carriage return.
    Call repeatedly with increasing `current`; a newline is emitted once current >= total.
    """
    total = max(total, 1)
    fraction = min(max(current / total, 0), 1)
    filled = int(length * fraction)
    bar = fill * filled + empty * (length - filled)
    pct = fraction * 100
    color = Colors.GREEN if pct >= 100 else Colors.CYAN
    end = "\n" if current >= total else ""
    line = f"\r  {prefix}{color}[{bar}]{Colors.END} {pct:5.1f}%  {suffix}"
    # Pad to clear any leftover characters from a longer previous line
    print(line + " " * 6, end=end, flush=True)

def print_stat(label, value, color=None, label_width=30):
    color = color or Colors.WHITE
    print(f"  {Colors.GRAY}{label:<{label_width}}{Colors.END} {color}{value}{Colors.END}")

def print_divider(char="─", width=70, color=None):
    color = color or Colors.GRAY
    print(f"{color}{char * width}{Colors.END}")

def print_task_header(step, total_steps, title):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}[{step}/{total_steps}]{Colors.END} {Colors.BOLD}{title}{Colors.END}")


class Spinner:
    """
    Animated spinner for indeterminate-length operations (service restarts,
    external commands, etc.). Use as a context manager:

        with Spinner("Flushing DNS cache") as sp:
            do_work()
        # or, to control the final message/outcome explicitly:
        sp = Spinner("Emptying Recycle Bin"); sp.start()
        ok = do_work()
        sp.stop(success=ok, final_message="Recycle Bin emptied" if ok else "Recycle Bin empty/skipped")
    """
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message):
        self.message = message
        self._running = False
        self._thread = None

    def start(self):
        import threading
        import time as _time
        self._running = True

        def _spin():
            i = 0
            while self._running:
                frame = self.FRAMES[i % len(self.FRAMES)]
                print(f"\r  {Colors.CYAN}{frame}{Colors.END} {self.message}...", end="", flush=True)
                i += 1
                _time.sleep(0.08)

        self._thread = threading.Thread(target=_spin, daemon=True)
        self._thread.start()

    def stop(self, success=True, final_message=None):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        msg = final_message or self.message
        icon = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
        print(f"\r  {icon} {msg}" + " " * 24)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(success=exc_type is None)
        return False

