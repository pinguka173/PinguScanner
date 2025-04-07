#!/usr/bin/env python3
import socket
import re
import os
import requests
import argparse
import json
from service_db import PORT_SERVICES
import sys
from urllib.parse import urlparse

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ANSI Color Codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"   # Resets color to original

if len(sys.argv) > 1 and sys.argv[1] in ("--help"):
    print("""
Usage: pinguscan -s <target> -p <preset> [-t <timeout>]
Example: pinguscan -s scanme.nmap.org -p web -t 20

Use pinguscan --commands for commands list
        """)
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] in ("--commands"):
    print()
    print("--help                     |   Displays basic information about the program")
    print("--commands                 |   Displays all available commands and usage")
    print("--presets                  |   Displays all available presets")
    print("--presets-details {preset} |   Displays the given preset's content")
    print("--update                   |   Updates to the newest version")
    print("-V, --version              |   Displays current version")
    print("-s {target}                |   Sets a target IP/Domain for the scan")
    print("-p {preset}                |   Sets a port preset")
    print("-t {value}                 |   Sets a timeout for the scan")
    print()
    sys.exit(0)

if len(sys.argv) > 0 and sys.argv[1] in ("-V") or len(sys.argv) > 0 and sys.argv[1] in ("--version"):
    print("PinguScan/v1.2.0")
    print("Release date: 04-07-2025")
    sys.exit(0)

def list_presets():
    presets_path = os.path.join(os.path.dirname(__file__), "presets", "port_presets.json")
    if not os.path.exists(presets_path):
        print("Presets file not found.")
        sys.exit(1)

    with open(presets_path, "r") as f:
        try:
            presets = json.load(f)
        except json.JSONDecodeError:
            print("Malformed presets.json, you absolute clown.")
            sys.exit(1)

    for name in presets:
        print(name)
    sys.exit(0)





def is_domain_correct(domain):
    pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,6}$"
    return re.match(pattern, domain) is not None

def is_domain_real(domain):
    try:
        ip = socket.gethostbyname(domain)
        print(GREEN + f"Domain resolves to {ip}" + RESET)
        return True
    except:
        print(RED + f"Domain does not resolve to IP." + RESET)
        return False

def validate_and_fetch(input_domain, timeout):
    # Parse the input URL to determine if a scheme is present.
    parsed = urlparse(input_domain)
    if not parsed.scheme:
        # No scheme provided, default to https.
        domain = "https://" + input_domain
        parsed = urlparse(domain)
    else:
        domain = input_domain

    # Extract hostname for further processing.
    hostname = parsed.netloc if parsed.netloc else parsed.path

    # Remove any trailing slashes.
    hostname = hostname.rstrip("/")

    # Attempt HTTPS connection first.
    try:
        test_url = f"https://{hostname}"
        print(f"Trying HTTPS for {hostname}...")
        response = requests.get(test_url, timeout=timeout)
        response.raise_for_status()
        print(f"Successfully connected to {test_url}")
        return hostname

    except Exception as e_https:
        print(f"HTTPS failed: {e_https}")
        print(f"Trying HTTP for {hostname}...")

        try:
            test_url = f"http://{hostname}"
            response = requests.get(test_url, timeout=timeout)
            response.raise_for_status()
            print(f"Connected via HTTP to {test_url}")
            return hostname
        except Exception as e_http:
            print(f"HTTP also failed: {e_http}")
            print(YELLOW + "Warning: Domain is not reachable via HTTP(S). Proceeding anyway." + RESET)
            return hostname


def load_presets_from_json(path):
    try:
        with open(path, "r") as f:
            presets = json.load(f)
            print(GREEN + f"Loaded presets from {path}" + RESET)
            return presets
    except Exception as e:
        print(RED + f"Failed to load JSON presets: {e}" + RESET)
        exit(1)

def Connect(ip, hostname, ports, timeout, services_db):
    open_ports = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((ip, port))
                print(GREEN + f"[+] Open port {port} on {ip}" + RESET)
                open_ports.append(port)

                service = services_db.get(port, "Unknown")
                print(f"[+] Service: {service}")

                received_data = b""
                try:
                    while True:
                        chunk = s.recv(1024)
                        if not chunk:
                            break
                        received_data += chunk
                except:
                    pass

                decoded = received_data.decode("utf-8", errors="replace")
                if decoded:
                    print(YELLOW + f"Received data on port {port}:\n{decoded}" + RESET)
                else:
                    print("No banner or data received.")

            except socket.timeout:
                print(RED + f"[-] Port {port} timed out." + RESET)
            except socket.error as e:
                print(RED + f"[-] Port {port} connection error: {e}" + RESET)
    return open_ports

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PinguScan")
    parser.add_argument("-s", "--site", required=True, help="Target domain or IP address")
    parser.add_argument("-p", "--preset", required=True, help="Port preset name from the JSON file")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Connection timeout (seconds)")
    parser.add_argument("--presets", default="presets.json", help="Path to JSON file with port presets")

    args = parser.parse_args()

    preset_path = args.presets
    if not os.path.isfile(preset_path):
        preset_path = os.path.join(ROOT_DIR, args.presets)

    port_presets = load_presets_from_json(preset_path)

    if args.preset not in port_presets:
        print(RED + f"Preset '{args.preset}' not found in {args.presets}!" + RESET)
        exit(1)

    target = validate_and_fetch(args.site, args.timeout)
    if not target:
        print(RED + "Domain validation failed. Exiting." + RESET)
        exit(1)

    try:
        ip = socket.gethostbyname(target)
        hostname, _, _ = socket.gethostbyaddr(ip)
        print(f"Reverse DNS: {ip} → {hostname}")
    except socket.herror:
        hostname = ip
        print(f"No reverse DNS for {ip}")

    ports = port_presets[args.preset]
    print(YELLOW + f"Scanning {ip} ({hostname}) with preset: {args.preset}" + RESET)

    Connect(ip, hostname, ports, args.timeout, PORT_SERVICES)

    parser.add_argument("--list-presets", action="store_true", help="List available presets and exit")
    args = parser.parse_args()

    if args.list_presets:
        try:
            with open("presets/port_presets.json", "r") as f:
                presets = json.load(f)
            print("Available presets:")
            for preset in presets.keys():
                print(preset)
        except Exception as e:
            print(f"Failed to load presets: {e}")
        sys.exit(0)


