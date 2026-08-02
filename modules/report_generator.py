"""
KB Toolkit - One-Click Diagnostic Report Module
Runs the toolkit's read-only checker modules back-to-back, headlessly,
and exports a single consolidated text + HTML report — useful for handing
to a technician or comparing before/after an optimization pass.

Only non-destructive "checker" modules are included here. Optimizer,
System Health, Repair Toolkit (they take action / need live confirmation)
and the monitor/remapper tools (they need live interactive input) are
intentionally excluded.
"""
import importlib
import io
import os
import re
import sys
import contextlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_stat, print_task_header
)

# (module_name, class_name, display_title)
REPORT_MODULES = [
    ("kb_checker", "KeyboardChecker", "Keyboard"),
    ("mouse_checker", "MouseChecker", "Mouse"),
    ("storage_checker", "StorageChecker", "Storage (SMART)"),
    ("ram_checker", "RamChecker", "RAM"),
    ("printer_checker", "PrinterChecker", "Printer"),
    ("scanner_checker", "ScannerChecker", "Scanner"),
    ("audio_checker", "AudioChecker", "Audio"),
    ("hardware_checker", "HardwareChecker", "Full Hardware Scan"),
    ("network_checker", "NetworkChecker", "Network"),
    ("startup_checker", "StartupChecker", "Startup & Performance"),
    ("eventlog_checker", "EventLogChecker", "Event Log"),
    ("display_checker", "DisplayChecker", "Display / GPU"),
    ("battery_checker", "BatteryChecker", "Battery Health"),
    ("backup_checker", "BackupChecker", "Backup & Restore"),
    ("driver_checker", "DriverChecker", "Driver Age"),
]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class ReportGenerator:
    def __init__(self):
        self.sections = []
        self.errors = []

    def run(self):
        print_banner("ONE-CLICK DIAGNOSTIC REPORT", Colors.BLUE)
        print_info("Runs read-only checkers back-to-back and saves a combined report")
        print_info("Optimizer, System Health, and interactive tools are excluded — see module notes")

        selected = self._select_modules()
        if not selected:
            print_info("No checks selected — nothing to do")
            prompt_continue()
            return

        print()
        for i, (mod_name, class_name, title) in enumerate(selected, 1):
            print_task_header(i, len(selected), f"Running {title} Checker")
            text, issues, error = self._run_module_capture(mod_name, class_name)
            self.sections.append({"title": title, "text": text, "issues": issues})
            if error:
                self.errors.append(f"{title}: {error}")
                print_error(f"  Failed: {error}")
            elif issues:
                print_warning(f"  Done — {len(issues)} issue(s) noted")
            else:
                print_success("  Done — no issues noted")

        report_paths = self._write_reports()
        self.print_summary(report_paths)
        prompt_continue()

    # ---------------------------------------------------------------- selection
    def _select_modules(self):
        print_section("Select Checks To Include")
        for i, (mod_name, class_name, title) in enumerate(REPORT_MODULES, 1):
            print(f"  {Colors.CYAN}{i}.{Colors.END} {title}")
        print(f"\n  {Colors.GRAY}Enter numbers separated by commas, 'a' for all (recommended), or Enter to cancel{Colors.END}")

        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()
        if not choice:
            return []
        if choice == "a":
            return list(REPORT_MODULES)

        selected = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(REPORT_MODULES):
                selected.append(REPORT_MODULES[int(part) - 1])
        return selected

    # ---------------------------------------------------------------- execution
    def _run_module_capture(self, mod_name, class_name):
        buf = io.StringIO()
        error = None
        issues = []
        try:
            module = importlib.import_module(mod_name)
            # Neutralize the interactive "Press Enter to continue..." pause
            module.prompt_continue = lambda: None
            cls = getattr(module, class_name)
            instance = cls()
            with contextlib.redirect_stdout(buf):
                instance.run()
            issues = list(getattr(instance, "issues", []) or [])
        except Exception as e:
            error = str(e)
        text = self._clean_output(buf.getvalue())
        return text, issues, error

    def _clean_output(self, text):
        text = ANSI_RE.sub("", text)
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            if "\r" in line:
                line = line.split("\r")[-1]
            cleaned.append(line)
        return "\n".join(cleaned)

    # ---------------------------------------------------------------- reports
    def _write_reports(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            log_dir = os.environ.get("TEMP", ".")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(log_dir, f"diagnostic_report_{timestamp}.txt")
        html_path = os.path.join(log_dir, f"diagnostic_report_{timestamp}.html")

        all_issues = []
        for sec in self.sections:
            for issue in sec["issues"]:
                all_issues.append(f"[{sec['title']}] {issue}")

        self._write_text_report(txt_path, all_issues)
        self._write_html_report(html_path, all_issues)

        return {"txt": txt_path, "html": html_path, "issues": all_issues}

    def _write_text_report(self, path, all_issues):
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write("KB TOOLKIT - ONE-CLICK DIAGNOSTIC REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Computer: {os.environ.get('COMPUTERNAME', 'Unknown')}\n")
            f.write("=" * 78 + "\n\n")

            f.write(f"ISSUES FOUND ACROSS ALL CHECKS ({len(all_issues)})\n")
            f.write("-" * 78 + "\n")
            if all_issues:
                for issue in all_issues:
                    f.write(f"  - {issue}\n")
            else:
                f.write("  No issues detected.\n")
            f.write("\n" + "=" * 78 + "\n")

            for sec in self.sections:
                f.write(f"\n{'#' * 78}\n# {sec['title'].upper()}\n{'#' * 78}\n")
                f.write(sec["text"])
                f.write("\n")

    def _write_html_report(self, path, all_issues):
        parts = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'>",
            "<title>KB Toolkit Diagnostic Report</title><style>",
            "body{background:#0d1117;color:#c9d1d9;font-family:Consolas,'Courier New',monospace;padding:24px;}",
            "h1{color:#58a6ff;} h2{color:#79c0ff;border-bottom:1px solid #30363d;padding-bottom:6px;margin-top:36px;}",
            ".meta{color:#8b949e;margin-bottom:24px;}",
            ".issues{background:#161b22;border:1px solid #f85149;border-radius:6px;padding:16px;margin-bottom:24px;}",
            ".issues.none{border-color:#3fb950;}",
            "pre{white-space:pre-wrap;background:#161b22;border:1px solid #30363d;border-radius:6px;padding:16px;overflow-x:auto;font-size:13px;}",
            "li{margin-bottom:4px;}",
            "</style></head><body>",
            "<h1>KB Toolkit &mdash; One-Click Diagnostic Report</h1>",
            f"<div class='meta'>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"on {self._escape_html(os.environ.get('COMPUTERNAME', 'Unknown'))}</div>",
        ]

        if all_issues:
            parts.append(f"<div class='issues'><h2 style='margin-top:0;border:none;'>&#9888; {len(all_issues)} Issue(s) Found</h2><ul>")
            for issue in all_issues:
                parts.append(f"<li>{self._escape_html(issue)}</li>")
            parts.append("</ul></div>")
        else:
            parts.append("<div class='issues none'><h2 style='margin-top:0;border:none;'>&#10003; No Issues Detected</h2></div>")

        for sec in self.sections:
            parts.append(f"<h2>{self._escape_html(sec['title'])}</h2>")
            parts.append(f"<pre>{self._escape_html(sec['text'])}</pre>")

        parts.append("</body></html>")

        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write("\n".join(parts))

    def _escape_html(self, text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # ---------------------------------------------------------------- summary
    def print_summary(self, report_paths):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         REPORT COMPLETE{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        print_stat("Checks run", len(self.sections))
        issue_color = Colors.YELLOW if report_paths["issues"] else Colors.GREEN
        print_stat("Total issues found", len(report_paths["issues"]), issue_color)
        print_success(f"Text report:  {report_paths['txt']}")
        print_success(f"HTML report:  {report_paths['html']}")

        if self.errors:
            print_warning(f"{len(self.errors)} check(s) failed to run:")
            for e in self.errors:
                print(f"  {Colors.RED}• {e}{Colors.END}")

        try:
            open_choice = input(f"\n  {Colors.CYAN}Open the HTML report now? [y/N]: {Colors.END}").strip().lower()
            if open_choice == "y":
                os.startfile(report_paths["html"])
        except Exception:
            print_info(f"Open it manually: {report_paths['html']}")

        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}\n")


def main():
    generator = ReportGenerator()
    generator.run()

if __name__ == "__main__":
    main()
