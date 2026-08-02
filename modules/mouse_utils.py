"""
Mouse & Trackpad Toolkit - Shared Utilities
"""
import ctypes
import ctypes.wintypes
import sys
import os
import logging
from datetime import datetime
from enum import IntEnum

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import Colors, print_banner, print_section, print_success, print_error, print_warning, print_info, is_admin, prompt_continue

# Mouse button VK codes
MOUSE_VK = {
    0x01: "LMB",
    0x02: "RMB", 
    0x04: "MMB",
    0x05: "X1 (BACK)",
    0x06: "X2 (FORWARD)",
}

# Common mouse/trackpad PNP IDs
TRACKPAD_VENDORS = {
    "SYN": "Synaptics",
    "ELAN": "Elan",
    "ALPS": "Alps Electric",
    "CYP": "Cypress",
    "ATMEL": "Atmel",
    "WACOM": "Wacom",
    "MSFT": "Microsoft",
    "LOGI": "Logitech",
    "RZR": "Razer",
    "COR": "Corsair",
    "STEEL": "SteelSeries",
    "GLOR": "Glorious",
    "HPIX": "HP",
    "DELL": "Dell",
    "LEN": "Lenovo",
    "ASUP": "ASUS",
    "ACR": "Acer",
}

class MouseColors:
    ORANGE = "\033[38;5;208m"
    MAGENTA = "\033[35m"
    TEAL = "\033[38;5;51m"
    PINK = "\033[38;5;205m"
    LIME = "\033[38;5;118m"

def print_mouse_banner(title):
    width = 70
    print(f"\n{MouseColors.TEAL}{'═' * width}{Colors.END}")
    print(f"{MouseColors.TEAL}{'║':<1}{title:^{width-2}}{'║':>1}{Colors.END}")
    print(f"{MouseColors.TEAL}{'═' * width}{Colors.END}\n")

def get_mouse_button_name(vk):
    return MOUSE_VK.get(vk, f"BTN_{vk:02X}")

def get_vendor_from_pnp(pnp_id):
    pnp_upper = pnp_id.upper()
    for prefix, name in TRACKPAD_VENDORS.items():
        if prefix in pnp_upper:
            return name
    return "Unknown"

def setup_mouse_logging():
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"mouse_toolkit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
        ]
    )
    return log_file
