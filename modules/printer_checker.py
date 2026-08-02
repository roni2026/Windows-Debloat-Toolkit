"""
KB Toolkit - Printer Checker Module
Diagnoses installed printers, spooler service health, ports, drivers, and queued jobs.
"""
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue
)

PRINTER_STATUS_CODES = {
    "1": "Other", "2": "Unknown", "3": "Idle", "4": "Printing",
    "5": "Warmup", "6": "Stopped Printing", "7": "Offline",
}

DETECTED_ERROR_STATE_CODES = {
    "0": "Unknown", "1": "Other", "2": "No Error", "3": "Low Paper",
    "4": "No Paper", "5": "Low Toner", "6": "No Toner", "7": "Door Open",
    "8": "Jammed", "9": "Service Requested", "10": "Output Bin Full",
    "11": "Paper Problem", "12": "Cannot Print Page",
    "13": "User Intervention Required", "14": "Out of Memory",
    "15": "Server Unknown", "16": "Power Save",
}


class PrinterChecker:
    def __init__(self):
        self.printers = []
        self.issues = []

    def run(self):
        print_banner("PRINTER DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_spooler_service()
        self.check_installed_printers()
        self.check_printer_status_detail()
        self.check_print_queue()
        self.check_ports()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=15
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def check_spooler_service(self):
        print_section("Print Spooler Service")
        stdout, stderr, rc = self._run_cmd("sc query spooler")
        if rc == 0:
            state = self._extract_value(stdout, "STATE")
            if state and "RUNNING" in state.upper():
                print_success(f"Print Spooler service is {Colors.GREEN}{state.strip()}{Colors.END}")
            else:
                print_error(f"Print Spooler service state: {state}")
                self.issues.append("Print Spooler service is not running")
                print_info("Fix: run 'net start spooler' as Administrator")
        else:
            print_error(f"Could not query spooler service: {stderr[:100]}")

        stdout, _, rc = self._run_cmd("sc qc spooler")
        if rc == 0:
            start_type = self._extract_value(stdout, "START_TYPE")
            if start_type:
                print(f"  Startup Type: {Colors.GRAY}{start_type.strip()}{Colors.END}")

    def check_installed_printers(self):
        print_section("Installed Printers")
        stdout, stderr, rc = self._run_cmd(
            'wmic printer get Name, Default, Local, Network, Shared, PrinterStatus, WorkOffline /FORMAT:LIST'
        )
        if rc != 0 or not stdout.strip():
            print_error(f"WMI query failed: {stderr[:100]}")
            return

        entries = self._parse_wmic_list(stdout)
        if not entries:
            print_warning("No printers found via WMI")
            return

        for i, prn in enumerate(entries, 1):
            name = prn.get("Name", "Unknown")
            default = prn.get("Default", "").strip().upper() == "TRUE"
            local = prn.get("Local", "").strip().upper() == "TRUE"
            offline = prn.get("WorkOffline", "").strip().upper() == "TRUE"
            status_code = prn.get("PrinterStatus", "").strip()
            status_name = PRINTER_STATUS_CODES.get(status_code, "Unknown")

            default_tag = f" {Colors.CYAN}[DEFAULT]{Colors.END}" if default else ""
            kind = "Local" if local else "Network/Shared"

            print(f"{Colors.BOLD}Printer {i}:{Colors.END} {Colors.WHITE}{name}{Colors.END}{default_tag}")
            print(f"  Type: {Colors.GRAY}{kind}{Colors.END}   Status: {self._color_status(status_name)}")
            if offline:
                print_warning("  Set to work offline")
                self.issues.append(f"{name}: set to work offline")

            self.printers.append(prn)

        if not any(p.get("Default", "").strip().upper() == "TRUE" for p in entries):
            self.issues.append("No default printer is set")

    def check_printer_status_detail(self):
        print_section("Driver & Port Details")
        stdout, _, rc = self._run_cmd(
            'wmic printer get Name, DriverName, PortName, Location /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for prn in entries:
                name = prn.get("Name", "Unknown")
                driver = prn.get("DriverName", "Unknown").strip()
                port = prn.get("PortName", "Unknown").strip()
                location = prn.get("Location", "").strip()

                print(f"{Colors.WHITE}{name}{Colors.END}")
                print(f"  Driver: {Colors.GRAY}{driver}{Colors.END}")
                print(f"  Port: {Colors.GRAY}{port}{Colors.END}")
                if location:
                    print(f"  Location: {Colors.GRAY}{location}{Colors.END}")

                if not driver or driver.lower() == "unknown":
                    self.issues.append(f"{name}: driver not reported (may need reinstall)")

    def check_print_queue(self):
        print_section("Print Queue / Pending Jobs")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_PrintJob get Document, JobStatus, Owner, PagesPrinted, JobId /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            if entries:
                for job in entries:
                    doc = job.get("Document", "Unknown")
                    status = job.get("JobStatus", "Unknown")
                    owner = job.get("Owner", "Unknown")
                    job_id = job.get("JobId", "")
                    print(f"  {Colors.CYAN}Job {job_id}{Colors.END}: {Colors.WHITE}{doc}{Colors.END} — {Colors.GRAY}{owner}{Colors.END} [{self._color_status(status)}]")
                    if status and status.lower() in ("error", "paused", "offline"):
                        self.issues.append(f"Print job stuck in queue: {doc} ({status})")
            else:
                print_success("No pending print jobs")
        else:
            print_info("Could not enumerate print queue (may require elevated access)")

    def check_ports(self):
        print_section("Printer Ports")
        stdout, _, rc = self._run_cmd('wmic path Win32_TCPIPPrinterPort get Name, HostAddress, PortNumber /FORMAT:LIST')
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for port in entries:
                name = port.get("Name", "Unknown")
                host = port.get("HostAddress", "").strip()
                num = port.get("PortNumber", "").strip()
                if host:
                    print(f"  {Colors.WHITE}{name}{Colors.END}: {Colors.GRAY}{host}:{num or '9100'}{Colors.END}")
        else:
            print_info("No TCP/IP printer ports found (USB/local ports not listed here)")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        if self.printers:
            print_success(f"Detected {len(self.printers)} printer(s)")
        else:
            print_error("No printers detected!")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No critical issues detected")

        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")

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
        if s in ("idle", "printing", "no error", "ok", "warmup"):
            return f"{Colors.GREEN}{status}{Colors.END}"
        elif s in ("offline", "stopped printing", "error", "jammed", "no toner", "no paper"):
            return f"{Colors.RED}{status}{Colors.END}"
        elif s in ("paused", "low paper", "low toner", "unknown"):
            return f"{Colors.YELLOW}{status}{Colors.END}"
        return f"{Colors.WHITE}{status}{Colors.END}"


def main():
    checker = PrinterChecker()
    checker.run()

if __name__ == "__main__":
    main()
