"""
KB Toolkit - System Optimizer Module
Temp file / Prefetch / cache cleanup and other safe, reversible-free
Windows optimizations, with a visual progress bar + spinner UI.

All actions here only touch well-known, Windows-regenerated cache/temp
locations (user & system Temp, Prefetch, thumbnail cache, Windows Update
download cache, Recycle Bin, DNS resolver cache). Nothing in Program Files,
user documents, or the registry is touched.
"""
import subprocess
import sys
import os
import time
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    format_bytes, print_progress_bar, print_stat, print_divider,
    print_task_header, Spinner
)

TASKS = [
    ("user_temp",     "User Temp Folder (%TEMP%)",              False),
    ("system_temp",   "System Temp Folder (C:\\Windows\\Temp)", True),
    ("prefetch",      "Prefetch Cache (*.pf)",                  True),
    ("thumbnails",    "Thumbnail Cache",                        False),
    ("wer_reports",   "Windows Error Reporting Queue",          False),
    ("recycle_bin",   "Recycle Bin",                            False),
    ("wu_cache",      "Windows Update Download Cache",          True),
    ("dns_cache",     "DNS Resolver Cache",                     False),
]


class SystemOptimizer:
    def __init__(self):
        self.bytes_freed = 0
        self.files_removed = 0
        self.files_skipped = 0
        self.tasks_run = []
        self.tasks_skipped = []
        self.errors = []

    def run(self):
        print_banner("SYSTEM OPTIMIZATION SUITE", Colors.BLUE)

        if not is_admin():
            print_warning("Not running as Administrator — System Temp, Prefetch, and Windows")
            print_warning("Update cache cleanup will be skipped (user-level cleanup still runs)")
            print_info("Choose 'A' from the main menu to relaunch elevated for full cleanup")

        selected = self._select_tasks()
        if not selected:
            print_info("No tasks selected — nothing to do")
            prompt_continue()
            return

        print()
        print_divider("═")
        print(f"{Colors.BOLD}  Running {len(selected)} optimization task(s)...{Colors.END}")
        print_divider("═")

        for i, key in enumerate(selected, 1):
            label = next(t[1] for t in TASKS if t[0] == key)
            print_task_header(i, len(selected), label)
            try:
                getattr(self, f"_task_{key}")()
                self.tasks_run.append(label)
            except Exception as e:
                self.errors.append(f"{label}: {e}")
                print_error(f"Task failed: {e}")

        self.directory_tree_report()
        self.print_summary()
        prompt_continue()

    # ------------------------------------------------------------ selection
    def _select_tasks(self):
        print_section("Select Optimizations")
        for i, (key, label, needs_admin) in enumerate(TASKS, 1):
            admin_tag = f" {Colors.YELLOW}[admin]{Colors.END}" if needs_admin else ""
            skip_tag = ""
            if needs_admin and not is_admin():
                skip_tag = f" {Colors.GRAY}(will be skipped — not elevated){Colors.END}"
            print(f"  {Colors.CYAN}{i}.{Colors.END} {label}{admin_tag}{skip_tag}")
        print(f"\n  {Colors.GRAY}Enter numbers separated by commas, 'a' for all, or Enter to cancel{Colors.END}")

        choice = input(f"  {Colors.CYAN}Select: {Colors.END}").strip().lower()
        if not choice:
            return []
        if choice == "a":
            return [t[0] for t in TASKS if not (t[2] and not is_admin())]

        selected = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(TASKS):
                key, label, needs_admin = TASKS[int(part) - 1]
                if needs_admin and not is_admin():
                    print_warning(f"Skipping '{label}' — requires Administrator")
                    continue
                selected.append(key)
        return selected

    # ------------------------------------------------------------ helpers
    def _run_cmd(self, cmd, shell=True, timeout=60):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    def _scan_folder(self, path):
        """Returns list of file paths and total byte size under `path`."""
        files = []
        total = 0
        if not path or not os.path.isdir(path):
            return files, total
        for root, dirs, filenames in os.walk(path):
            for fn in filenames:
                fp = os.path.join(root, fn)
                try:
                    total += os.path.getsize(fp)
                    files.append(fp)
                except OSError:
                    continue
        return files, total

    def _clean_files(self, files, label):
        """Deletes files with a live progress bar; tallies freed bytes/skips."""
        if not files:
            print_info(f"{label}: nothing to clean")
            return

        total = len(files)
        freed = 0
        removed = 0
        skipped = 0

        for idx, fp in enumerate(files, 1):
            try:
                size = os.path.getsize(fp)
                os.remove(fp)
                freed += size
                removed += 1
            except OSError:
                skipped += 1
            print_progress_bar(
                idx, total,
                prefix=f"{label}: ",
                suffix=f"{idx}/{total} files  ({format_bytes(freed)} freed)"
            )

        self._remove_empty_dirs(files)

        self.bytes_freed += freed
        self.files_removed += removed
        self.files_skipped += skipped

        if skipped:
            print_warning(f"{skipped} file(s) skipped (in use or access denied)")
        print_success(f"{label}: freed {format_bytes(freed)} across {removed} file(s)")

    def _remove_empty_dirs(self, cleaned_files):
        dirs = {os.path.dirname(f) for f in cleaned_files}
        for d in sorted(dirs, key=len, reverse=True):
            try:
                if os.path.isdir(d) and not os.listdir(d):
                    os.rmdir(d)
            except OSError:
                pass

    # ------------------------------------------------------------ tasks
    def _task_user_temp(self):
        path = os.environ.get("TEMP") or os.environ.get("TMP")
        if not path:
            print_warning("Could not resolve %TEMP% path")
            return
        print_info(f"Scanning {path}")
        files, total_bytes = self._scan_folder(path)
        print_stat("Files found", f"{len(files)}  ({format_bytes(total_bytes)})")
        self._clean_files(files, "User Temp")

    def _task_system_temp(self):
        path = r"C:\Windows\Temp"
        print_info(f"Scanning {path}")
        files, total_bytes = self._scan_folder(path)
        print_stat("Files found", f"{len(files)}  ({format_bytes(total_bytes)})")
        self._clean_files(files, "System Temp")

    def _task_prefetch(self):
        path = r"C:\Windows\Prefetch"
        files = []
        if os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".pf")]
        total_bytes = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        print_stat("Prefetch files found", f"{len(files)}  ({format_bytes(total_bytes)})")
        print_info("Windows automatically rebuilds Prefetch data — safe to clear")
        self._clean_files(files, "Prefetch")

    def _task_thumbnails(self):
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Explorer")
        files = []
        if os.path.isdir(base):
            files = [os.path.join(base, f) for f in os.listdir(base) if f.lower().startswith("thumbcache_")]
        total_bytes = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        print_stat("Thumbnail cache files", f"{len(files)}  ({format_bytes(total_bytes)})")
        if files:
            print_info("If a file is locked, close File Explorer windows and re-run")
        self._clean_files(files, "Thumbnail Cache")

    def _task_wer_reports(self):
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER")
        all_files = []
        for sub in ("ReportQueue", "ReportArchive"):
            files, _ = self._scan_folder(os.path.join(base, sub))
            all_files.extend(files)
        total_bytes = sum(os.path.getsize(f) for f in all_files if os.path.exists(f))
        print_stat("Error report files", f"{len(all_files)}  ({format_bytes(total_bytes)})")
        self._clean_files(all_files, "Error Reporting Queue")

    def _task_recycle_bin(self):
        with Spinner("Emptying Recycle Bin") as sp:
            stdout, stderr, rc = self._run_cmd(
                'powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"'
            )
        ok = rc == 0
        print_success("Recycle Bin emptied") if ok else print_warning("Recycle Bin may already be empty, or partial cleanup occurred")

    def _task_wu_cache(self):
        print_info("Stopping Windows Update service to release the cache folder")
        with Spinner("Stopping wuauserv / bits") as sp:
            self._run_cmd("net stop wuauserv", timeout=30)
            self._run_cmd("net stop bits", timeout=30)

        path = r"C:\Windows\SoftwareDistribution\Download"
        files, total_bytes = self._scan_folder(path)
        print_stat("Update cache files", f"{len(files)}  ({format_bytes(total_bytes)})")
        self._clean_files(files, "Windows Update Cache")

        with Spinner("Restarting wuauserv / bits") as sp:
            self._run_cmd("net start wuauserv", timeout=30)
            self._run_cmd("net start bits", timeout=30)

    def _task_dns_cache(self):
        sp = Spinner("Flushing DNS resolver cache")
        sp.start()
        stdout, stderr, rc = self._run_cmd("ipconfig /flushdns")
        sp.stop(success=(rc == 0), final_message="DNS resolver cache flushed" if rc == 0 else "DNS flush reported an issue")

    # ------------------------------------------------------------ tree report
    def directory_tree_report(self):
        print_section("Directory Tree Report")
        target = os.environ.get("TEMP") or r"C:\Windows\Temp"
        print_info(f"Generating folder structure for: {target}")

        with Spinner("Running tree") as sp:
            stdout, stderr, rc = self._run_cmd(f'tree "{target}" /A', timeout=30)

        if rc != 0 or not stdout.strip():
            print_warning("tree command produced no output (folder may now be empty — that's a good sign)")
            return

        lines = stdout.splitlines()
        preview = lines[:25]
        for line in preview:
            print(f"  {Colors.GRAY}{line}{Colors.END}")
        if len(lines) > 25:
            print(f"  {Colors.GRAY}... ({len(lines) - 25} more lines){Colors.END}")

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            out_path = os.path.join(log_dir, "directory_tree_report.txt")
            with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(stdout)
            print_success(f"Full tree saved to {out_path}")
        except OSError as e:
            print_warning(f"Could not save tree report: {e}")

    # ------------------------------------------------------------ summary
    def print_summary(self):
        print()
        print_divider("═")
        print(f"{Colors.BOLD}{'OPTIMIZATION SUMMARY':^70}{Colors.END}")
        print_divider("═")

        print_progress_bar(1, 1, prefix="Overall: ", suffix="Complete")
        print()
        print_stat("Tasks completed", len(self.tasks_run), Colors.GREEN)
        print_stat("Total space freed", format_bytes(self.bytes_freed), Colors.GREEN)
        print_stat("Files removed", self.files_removed, Colors.WHITE)
        if self.files_skipped:
            print_stat("Files skipped (in use)", self.files_skipped, Colors.YELLOW)

        if self.tasks_run:
            print(f"\n  {Colors.BOLD}Completed:{Colors.END}")
            for t in self.tasks_run:
                print(f"    {Colors.GREEN}✓{Colors.END} {t}")

        if self.errors:
            print(f"\n  {Colors.BOLD}Errors:{Colors.END}")
            for e in self.errors:
                print(f"    {Colors.RED}✗{Colors.END} {e}")

        print_divider("═")
        print()


def main():
    optimizer = SystemOptimizer()
    optimizer.run()

if __name__ == "__main__":
    main()
