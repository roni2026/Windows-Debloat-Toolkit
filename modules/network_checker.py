"""
KB Toolkit - Network Diagnostics Module
Adapter configuration, connectivity (ping/gateway/DNS), link speed, and a
lightweight traceroute — the "why is my internet broken" checklist.
"""
import subprocess
import socket
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_utils import (
    Colors, print_banner, print_section, print_success,
    print_error, print_warning, print_info, is_admin, prompt_continue,
    print_progress_bar, print_stat, Spinner
)

DNS_TEST_DOMAINS = ["www.google.com", "www.microsoft.com", "www.cloudflare.com"]
PING_TARGETS = [("8.8.8.8", "Google DNS"), ("1.1.1.1", "Cloudflare DNS")]


class NetworkChecker:
    def __init__(self):
        self.adapters = []
        self.gateway = None
        self.issues = []

    def run(self):
        print_banner("NETWORK DIAGNOSTIC SUITE", Colors.BLUE)

        self.check_adapters()
        self.check_adapter_speed()
        self.check_gateway_connectivity()
        self.check_internet_connectivity()
        self.check_dns_resolution()
        self.check_traceroute()

        self.print_summary()
        prompt_continue()

    def _run_cmd(self, cmd, shell=True, timeout=30):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, shell=shell,
                encoding="utf-8", errors="ignore", timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), -1

    # ---------------------------------------------------------------- adapters
    def check_adapters(self):
        print_section("Network Adapters (ipconfig /all)")
        stdout, stderr, rc = self._run_cmd("ipconfig /all")
        if rc != 0 or not stdout.strip():
            print_error(f"ipconfig failed: {stderr[:100]}")
            return

        blocks = re.split(r"\r?\n\r?\n(?=\S)", stdout)
        for block in blocks:
            lines = block.splitlines()
            if not lines or ":" not in block:
                continue
            header = lines[0].strip().rstrip(":")
            if "adapter" not in header.lower():
                continue

            info = {"name": header}
            for line in lines[1:]:
                if "Media State" in line and "Disconnected" in line:
                    info["media_state"] = "Disconnected"
                if "DHCP Enabled" in line:
                    info["dhcp"] = line.split(":", 1)[-1].strip()
                if re.search(r"IPv4 Address", line):
                    info["ipv4"] = line.split(":", 1)[-1].strip().replace("(Preferred)", "").strip()
                if "Default Gateway" in line:
                    gw = line.split(":", 1)[-1].strip()
                    if gw:
                        info["gateway"] = gw
                        if not self.gateway:
                            self.gateway = gw
                if "DNS Servers" in line:
                    info["dns"] = line.split(":", 1)[-1].strip()

            connected = info.get("media_state") != "Disconnected"
            print(f"{Colors.BOLD}{header}{Colors.END}")
            if not connected and "ipv4" not in info:
                print(f"  Status: {Colors.GRAY}Media disconnected (no cable/not associated){Colors.END}")
            else:
                if "ipv4" in info:
                    print(f"  IPv4: {Colors.WHITE}{info['ipv4']}{Colors.END}   DHCP: {Colors.GRAY}{info.get('dhcp', 'Unknown')}{Colors.END}")
                if "gateway" in info:
                    print(f"  Gateway: {Colors.GRAY}{info['gateway']}{Colors.END}")
                if "dns" in info:
                    print(f"  DNS: {Colors.GRAY}{info['dns']}{Colors.END}")

            self.adapters.append(info)

        if not self.gateway:
            self.issues.append("No default gateway found on any adapter — likely no active connection")

    def check_adapter_speed(self):
        print_section("Adapter Link Speed")
        stdout, stderr, rc = self._run_cmd(
            'wmic path Win32_NetworkAdapter WHERE "NetEnabled=TRUE" get Name, Speed /FORMAT:LIST'
        )
        if rc == 0 and stdout.strip():
            entries = self._parse_wmic_list(stdout)
            for adapter in entries:
                name = adapter.get("Name", "Unknown")
                speed = adapter.get("Speed", "").strip()
                if not speed or speed == "0":
                    continue
                try:
                    mbps = int(speed) / 1_000_000
                except ValueError:
                    continue
                color = Colors.GREEN if mbps >= 100 else Colors.YELLOW
                print(f"  {Colors.WHITE}{name}{Colors.END}: {color}{mbps:.0f} Mbps{Colors.END}")
                if 0 < mbps < 100 and "wi-fi" not in name.lower() and "wireless" not in name.lower():
                    self.issues.append(f"{name}: link speed unusually low ({mbps:.0f} Mbps) — check cable/port")
        else:
            print_warning("Could not query adapter link speeds")

    # ---------------------------------------------------------------- connectivity
    def _ping(self, target, count=4):
        stdout, _, rc = self._run_cmd(f"ping -n {count} -w 1000 {target}", timeout=15)
        loss_match = re.search(r"\((\d+)% loss\)", stdout)
        avg_match = re.search(r"Average = (\d+)ms", stdout)
        loss = int(loss_match.group(1)) if loss_match else (100 if rc != 0 else None)
        avg_ms = int(avg_match.group(1)) if avg_match else None
        return loss, avg_ms

    def check_gateway_connectivity(self):
        print_section("Default Gateway Connectivity")
        if not self.gateway:
            print_warning("No gateway to test")
            return

        with Spinner(f"Pinging gateway {self.gateway}") as sp:
            loss, avg_ms = self._ping(self.gateway)

        if loss is None:
            print_warning("Could not determine packet loss")
        elif loss == 0:
            print_success(f"Gateway reachable — avg {avg_ms}ms" if avg_ms is not None else "Gateway reachable")
        elif loss < 100:
            print_warning(f"Partial packet loss to gateway: {loss}%")
            self.issues.append(f"Gateway {self.gateway}: {loss}% packet loss")
        else:
            print_error("Gateway unreachable (100% loss)")
            self.issues.append(f"Gateway {self.gateway} unreachable")

    def check_internet_connectivity(self):
        print_section("Internet Connectivity")
        for i, (target, label) in enumerate(PING_TARGETS, 1):
            print_progress_bar(i - 1, len(PING_TARGETS), prefix="Testing: ", suffix=f"{label} ({target})")
            loss, avg_ms = self._ping(target)
            print_progress_bar(i, len(PING_TARGETS), prefix="Testing: ", suffix=f"{label} ({target})")

            if loss == 0:
                print_success(f"{label}: reachable — avg {avg_ms}ms" if avg_ms is not None else f"{label}: reachable")
            elif loss is not None and loss < 100:
                print_warning(f"{label}: {loss}% packet loss")
                self.issues.append(f"{label} ({target}): {loss}% packet loss")
            else:
                print_error(f"{label}: unreachable")
                self.issues.append(f"{label} ({target}): unreachable")

    def check_dns_resolution(self):
        print_section("DNS Resolution")
        socket.setdefaulttimeout(3)
        failures = 0
        for i, domain in enumerate(DNS_TEST_DOMAINS, 1):
            print_progress_bar(i - 1, len(DNS_TEST_DOMAINS), prefix="Resolving: ", suffix=domain)
            try:
                ip = socket.gethostbyname(domain)
                print_progress_bar(i, len(DNS_TEST_DOMAINS), prefix="Resolving: ", suffix=domain)
                print_success(f"{domain} → {ip}")
            except (socket.gaierror, socket.timeout):
                print_progress_bar(i, len(DNS_TEST_DOMAINS), prefix="Resolving: ", suffix=domain)
                print_error(f"{domain}: resolution failed")
                failures += 1

        if failures == len(DNS_TEST_DOMAINS):
            self.issues.append("DNS resolution failing for all test domains — check DNS server settings")
        elif failures > 0:
            self.issues.append(f"DNS resolution failed for {failures}/{len(DNS_TEST_DOMAINS)} test domain(s)")

    def check_traceroute(self):
        print_section("Traceroute to 8.8.8.8 (max 10 hops)")
        with Spinner("Tracing route") as sp:
            stdout, stderr, rc = self._run_cmd("tracert -h 10 -w 500 8.8.8.8", timeout=25)

        if rc != 0 or not stdout.strip():
            print_warning("Traceroute produced no output")
            return

        hop_lines = [l for l in stdout.splitlines() if re.match(r"\s*\d+", l)]
        for line in hop_lines:
            timed_out = "Request timed out" in line
            color = Colors.GRAY if not timed_out else Colors.YELLOW
            print(f"  {color}{line.strip()}{Colors.END}")

        timeouts = sum(1 for l in hop_lines if "Request timed out" in l)
        if hop_lines and timeouts == len(hop_lines):
            self.issues.append("All traceroute hops timed out — possible firewall/ICMP blocking")

    # ---------------------------------------------------------------- summary
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'═' * 70}{Colors.END}")
        print(f"{Colors.BOLD}                         DIAGNOSTIC SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'═' * 70}{Colors.END}")

        active = [a for a in self.adapters if a.get("ipv4")]
        print_stat("Active adapters", len(active))
        print_stat("Default gateway", self.gateway or "None detected")

        if self.issues:
            print_warning(f"Found {len(self.issues)} issue(s):")
            for issue in self.issues:
                print(f"  {Colors.RED}• {issue}{Colors.END}")
        else:
            print_success("No connectivity issues detected")

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


def main():
    checker = NetworkChecker()
    checker.run()

if __name__ == "__main__":
    main()
