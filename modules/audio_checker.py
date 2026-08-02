"""
KB Toolkit - Audio Checker Module
Diagnoses playback/recording devices (internal speakers, headphones, earphones,
external speakers, microphones), audio services, and drivers — laptop or desktop.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)

# Keywords used to classify a device name into a friendly category
DEVICE_KEYWORDS = [
    ("Headphones/Earphones", ["headphone", "headset", "earphone", "earbud", "airpods"]),
    ("Bluetooth Audio", ["bluetooth", "bt audio", "hands-free"]),
    ("Internal Speakers", ["internal speakers", "realtek", "conexant", "laptop speaker", "speakers/hp"]),
    ("External Speakers", ["speakers", "soundbar", "external"]),
    ("HDMI/DisplayPort Audio", ["hdmi", "displayport", "nvidia high definition audio", "amd high definition audio"]),
    ("Microphone", ["microphone", "mic array", "webcam mic"]),
]


class AudioChecker:
    def __init__(self):
        self.playback_devices = []
        self.recording_devices = []
        self.issues = []

    def run(self):
        print_banner("AUDIO DEVICE DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_audio_services()
        self.check_sound_devices_wmi()
        self.check_playback_devices()
        self.check_recording_devices()
        self.check_driver_details()
        self.check_volume_mute_state()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=20
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def check_audio_services(self):
        print_section("Audio Service Status")
        services = [
            ("AudioSrv", "Windows Audio"),
            ("AudioEndpointBuilder", "Windows Audio Endpoint Builder"),
            ("MMCSS", "Multimedia Class Scheduler"),
        ]
        for svc_id, svc_name in services:
            stdout, _, rc = self._run_cmd(f"sc query {svc_id}")
            if rc == 0:
                state = self._extract_value(stdout, "STATE")
                if state and "RUNNING" in state.upper():
                    print_success(f"{svc_name} is {Colors.GREEN}{state.strip()}{Colors.END}")
                else:
                    print_error(f"{svc_name} state: {state}")
                    self.issues.append(f"{svc_name} service not running")
            else:
                print_warning(f"Could not query {svc_name}")

    def check_sound_devices_wmi(self):
        print_section("Sound Device Enumeration (WMI)")
        stdout, stderr, rc = self._run_cmd(
            'wmic sounddev get Name, Status, Manufacturer, ConfigManagerErrorCode /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"WMI query failed: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_warning("No sound devices found via WMI")
            return

        for i, dev in enumerate(entries, 1):
            name = dev.get("Name", "Unknown")
            status = dev.get("Status", "Unknown")
            manufacturer = dev.get("Manufacturer", "").strip()
            err_code = dev.get("ConfigManagerErrorCode", "")
            category = self._classify_device(name)

            print(f"{Colors.BOLD}Device {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}")
            print(f"  Category: {Colors.CYAN}{category}{Colors.END}   Status: {self._color_status(status)}")
            if manufacturer:
                print(f"  Manufacturer: {Colors.GRAY}{manufacturer}{Colors.END}")
            if err_code and err_code != "0":
                print(f"  Error Code: {Colors.RED}{err_code}{Colors.END}")
                self.issues.append(f"{name}: Error {err_code}")

    def check_playback_devices(self):
        print_section("Playback Devices (Speakers / Headphones)")
        ps_cmd = (
            'powershell -NoProfile -Command "'
            'Get-CimInstance -Namespace root/cimv2 -ClassName Win32_SoundDevice | '
            'Select-Object Name, Status | Format-List"'
        )
        stdout, stderr, rc = self._run_cmd(ps_cmd)

        # Fallback / supplementary: AudioDeviceCmdlets-free enumeration via registry render endpoints
        reg_cmd = (
            r'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render" /s /f "DeviceState" 2>nul'
        )
        r_stdout, _, r_rc = self._run_cmd(reg_cmd)

        name_cmd = (
            r'powershell -NoProfile -Command "Get-ItemProperty -Path '
            r'\'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\*\Properties\' '
            r'-Name \'{a45c254e-df1c-4efd-8020-67d146a850e0},2\' -ErrorAction SilentlyContinue | '
            r'Select-Object -ExpandProperty \'{a45c254e-df1c-4efd-8020-67d146a850e0},2\'"'
        )
        n_stdout, _, n_rc = self._run_cmd(name_cmd)

        if n_rc == 0 and n_stdout.strip():
            names = [l.strip() for l in n_stdout.splitlines() if l.strip()]
            if names:
                for name in names:
                    category = self._classify_device(name)
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {Colors.CYAN}{category}{Colors.END}")
                    self.playback_devices.append(name)
            else:
                print_info("No named playback endpoints resolved via registry")
        else:
            print_info("Could not enumerate playback endpoint names directly — see WMI list above")

        if not self.playback_devices:
            print_warning("Unable to confirm a distinct default output device")

    def check_recording_devices(self):
        print_section("Recording Devices (Microphones)")
        name_cmd = (
            r'powershell -NoProfile -Command "Get-ItemProperty -Path '
            r'\'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture\*\Properties\' '
            r'-Name \'{a45c254e-df1c-4efd-8020-67d146a850e0},2\' -ErrorAction SilentlyContinue | '
            r'Select-Object -ExpandProperty \'{a45c254e-df1c-4efd-8020-67d146a850e0},2\'"'
        )
        n_stdout, _, n_rc = self._run_cmd(name_cmd)

        if n_rc == 0 and n_stdout.strip():
            names = [l.strip() for l in n_stdout.splitlines() if l.strip()]
            if names:
                for name in names:
                    print(f"  {Colors.WHITE}{name}{Colors.END} — {Colors.CYAN}Microphone{Colors.END}")
                    self.recording_devices.append(name)
            else:
                print_info("No named recording endpoints resolved via registry")
        else:
            print_info("Could not enumerate recording endpoint names directly")

    def check_driver_details(self):
        print_section("Audio Driver Files")
        driver_files = [
            ("HD Audio Bus Driver", r"C:\Windows\System32\drivers\HDAudBus.sys"),
            ("USB Audio Class Driver", r"C:\Windows\System32\drivers\usbaudio.sys"),
            ("Bluetooth Audio Driver", r"C:\Windows\System32\drivers\BthA2dp.sys"),
        ]
        for name, path in driver_files:
            if os.path.exists(path):
                print_success(f"{name} present")
            else:
                print_info(f"{name} not found (may be N/A on this system)")

    def check_volume_mute_state(self):
        print_section("System Volume / Mute State")
        ps_cmd = (
            'powershell -NoProfile -Command '
            '"(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue) '
            '| Out-Null; Write-Output \'checked\'"'
        )
        # Endpoint volume isn't exposed cleanly without extra modules; report what's practical.
        print_info("Volume/mute level requires the endpoint volume API — not exposed via built-in WMI/PowerShell")
        print_info("If audio devices show above but produce no sound, check Volume Mixer per-app mute state")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.playback_devices:
            print_success(f"Detected {len(self.playback_devices)} playback device(s)")
        else:
            print_warning("Could not confirm named playback devices (see WMI list above)")

        if self.recording_devices:
            print_success(f"Detected {len(self.recording_devices)} recording device(s)")
        else:
            print_warning("No recording devices confirmed")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No critical issues detected")

        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")

    def _classify_device(self, name):
        n = name.lower()
        for category, keywords in DEVICE_KEYWORDS:
            if any(kw in n for kw in keywords):
                return category
        return "Other Audio Device"

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

    def _extract_value(self, text, key):
        for line in text.splitlines():
            if key in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None

    def _color_status(self, status):
        s = status.lower() if status else ""
        if "ok" in s:
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif "error" in s or "failed" in s or "degraded" in s:
            return f"{Colors.RED}{status}{Colors.END}"
        elif "warning" in s or "unknown" in s:
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    checker = AudioChecker()
    checker.run()

if __name__ == "__main__":
    main()
