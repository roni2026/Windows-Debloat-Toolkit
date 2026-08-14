"""
KB Toolkit - Tweak Engine
Shared engine for reversible registry/Group Policy tweaks. Every tweak
provides an apply(), revert(), and check() function, so any change made
here can be verified and undone from inside the toolkit.

This module only reads/writes well-documented Windows registry values and
official Group Policy keys (the same settings exposed through gpedit.msc
and Microsoft's own admx templates) — nothing here touches system files.
"""
import os
import sys
import json
import winreg
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import Colors, print_success, print_error, print_warning, print_info

HIVES = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKU": winreg.HKEY_USERS,
}

REG_TYPES = {
    "DWORD": winreg.REG_DWORD,
    "SZ": winreg.REG_SZ,
    "BINARY": winreg.REG_BINARY,
    "EXPAND_SZ": winreg.REG_EXPAND_SZ,
}

STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
STATE_FILE = os.path.join(STATE_DIR, "tweak_state.json")


# --------------------------------------------------------------------- regops
def _split_path(full_path):
    hive_name, sub_path = full_path.split("\\", 1)
    return HIVES[hive_name], sub_path


def reg_read(full_path, value_name):
    """Returns the current value, or None if the key/value doesn't exist."""
    try:
        hive, sub_path = _split_path(full_path)
        with winreg.OpenKey(hive, sub_path, 0, winreg.KEY_READ) as key:
            data, _ = winreg.QueryValueEx(key, value_name)
            return data
    except FileNotFoundError:
        return None
    except OSError:
        return None


def reg_write(full_path, value_name, data, value_type="DWORD"):
    try:
        hive, sub_path = _split_path(full_path)
        with winreg.CreateKeyEx(hive, sub_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, value_name, 0, REG_TYPES[value_type], data)
        return True
    except OSError as e:
        raise RuntimeError(f"Failed to write {full_path}\\{value_name}: {e}")


def reg_delete_value(full_path, value_name):
    try:
        hive, sub_path = _split_path(full_path)
        with winreg.OpenKey(hive, sub_path, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, value_name)
        return True
    except FileNotFoundError:
        return True  # already gone — treat as success
    except OSError as e:
        raise RuntimeError(f"Failed to delete {full_path}\\{value_name}: {e}")


def reg_delete_key(full_path):
    try:
        hive, sub_path = _split_path(full_path)
        winreg.DeleteKey(hive, sub_path)
        return True
    except FileNotFoundError:
        return True
    except OSError as e:
        raise RuntimeError(f"Failed to delete key {full_path}: {e}")


def reg_matches(full_path, value_name, expected):
    """True if the value currently equals `expected`."""
    return reg_read(full_path, value_name) == expected


def run_cmd(cmd, timeout=60):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1


# --------------------------------------------------------------------- tweak
class Tweak:
    """
    A single reversible setting.
      key         short unique id, e.g. "privacy_telemetry"
      name        display name
      description one-line explanation of what it does
      apply       callable, applies the tweak
      revert      callable, restores the previous/default state
      check       callable -> bool, True if currently applied
      needs_admin whether HKLM/system-level writes are involved
      risk        "" | "reboot" | "caution" — shown next to the tweak
    """
    def __init__(self, key, name, description, apply, revert, check,
                 needs_admin=True, risk=""):
        self.key = key
        self.name = name
        self.description = description
        self.apply = apply
        self.revert = revert
        self.check = check
        self.needs_admin = needs_admin
        self.risk = risk

    def status(self):
        try:
            return self.check()
        except Exception:
            return None  # unknown / couldn't determine


# --------------------------------------------------------------------- state
def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def record_applied(tweak_key, applied):
    state = load_state()
    state[tweak_key] = {
        "applied": applied,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    save_state(state)


def write_state_report(all_tweaks):
    """Writes a plain-text summary of every known tweak's current state."""
    os.makedirs(STATE_DIR, exist_ok=True)
    report_path = os.path.join(STATE_DIR, "tweak_state_report.txt")
    lines = [f"KB Toolkit — Tweak State Report", f"Generated: {datetime.now().isoformat(timespec='seconds')}", ""]
    for category, tweaks in all_tweaks.items():
        lines.append(f"[{category}]")
        for t in tweaks:
            state = t.status()
            label = "ON " if state is True else ("OFF" if state is False else "?  ")
            lines.append(f"  {label}  {t.name}")
        lines.append("")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return report_path
    except Exception:
        return None


# --------------------------------------------------------------------- restore
def create_restore_point(description="KB Toolkit Tweak"):
    """
    Attempts to create a System Restore checkpoint before applying tweaks.
    Returns (ok: bool, message: str). Never raises — a failed restore point
    should warn the caller, not block the tweak from running.
    """
    ps_cmd = (
        "powershell -NoProfile -Command "
        f"\"Checkpoint-Computer -Description '{description}' "
        "-RestorePointType MODIFY_SETTINGS\""
    )
    stdout, stderr, rc = run_cmd(ps_cmd, timeout=90)
    if rc == 0:
        return True, "Restore point created."
    reason = (stderr or stdout or "unknown error").strip().splitlines()[-1] if (stderr or stdout) else "unknown error"
    return False, f"Could not create a restore point ({reason}). System Protection may be off, " \
                   "or Windows is rate-limiting checkpoints (one per day by default)."


# --------------------------------------------------------------------- runner
def apply_tweaks(tweaks, make_restore_point=True):
    """Applies a list of Tweak objects, returns (applied, skipped, failed) name lists."""
    applied, skipped, failed = [], [], []

    if make_restore_point:
        ok, msg = create_restore_point("KB Toolkit - Before Tweaks")
        (print_success if ok else print_warning)(msg)

    for t in tweaks:
        try:
            already = t.status()
            if already is True:
                skipped.append(t.name)
                print_info(f"Already applied: {t.name}")
                continue
            t.apply()
            record_applied(t.key, True)
            applied.append(t.name)
            print_success(f"Applied: {t.name}")
        except Exception as e:
            failed.append(t.name)
            print_error(f"Failed: {t.name} — {e}")

    return applied, skipped, failed


def revert_tweaks(tweaks):
    reverted, skipped, failed = [], [], []
    for t in tweaks:
        try:
            already = t.status()
            if already is False:
                skipped.append(t.name)
                print_info(f"Already at default: {t.name}")
                continue
            t.revert()
            record_applied(t.key, False)
            reverted.append(t.name)
            print_success(f"Reverted: {t.name}")
        except Exception as e:
            failed.append(t.name)
            print_error(f"Failed to revert: {t.name} — {e}")

    return reverted, skipped, failed
