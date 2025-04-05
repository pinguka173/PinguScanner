import socket
import re
import json
import requests
import ssl
from service_db import PORT_SERVICES

# ANSI Color Codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset to default color

def is_domain_correct(domain):
    pattern = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,6}$"  # Matches valid domains
    return re.match(pattern, domain) is not None

def is_domain_real(domain):
    try:
        ip = socket.gethostbyname(domain)
        print(GREEN + "Domain resolves to", ip, "IP." + RESET)
        return True
    except:
        print(RED + "Domain does not resolve to IP." + RESET)
        return False
        
DOMAIN = input("Please enter an IP or domain\n")
if not DOMAIN.startswith("http://") and not DOMAIN.startswith("https://"):
    DOMAIN = "https://" + DOMAIN 
response = requests.get(DOMAIN)
DOMAIN = DOMAIN.removeprefix("http://").removeprefix("https://").removesuffix("/")
if not is_domain_real(DOMAIN):
    print(RED + "Invalid domain!" + RESET)
elif not is_domain_correct(DOMAIN):
    print(RED + "Domain does not resolve to DNA!" + RESET)
else:
    print(GREEN + "Everything's fine, go ahead." + RESET)

print(response.status_code)

PORTS = []
OPEN_PORTS = []
Details = {}

Port_presets = input("Which preset would you like to use? Type 'help' for help or 'create' to create new: ").strip().lower()

with open("presets/port_presets.json") as f:
    Port_preset = json.load(f)

if Port_presets == "help":
    print(GREEN + "Available presets:" + RESET)
    for name in Port_preset:
        print(f" - {name}")
    exit()

elif Port_presets == "create":
    CPPP_temp = []
    Custom_port_preset_name = input("Please provide a name for your preset: ").strip()
    while True:
        Custom_port_preset_ports = input("Please enter the ports you'd like to add to your preset. Type 'done' if finished: ").strip()
        if not Custom_port_preset_ports.isdigit() and Custom_port_preset_ports.lower() != "done":
            print(RED + "Invalid input. Please enter a valid numeric port." + RESET)
            continue
        elif Custom_port_preset_ports.isdigit():
            CPPP_temp.append(int(Custom_port_preset_ports))
        elif Custom_port_preset_ports.lower() == "done":
            break

    Custom_port_preset_temp = {Custom_port_preset_name: CPPP_temp}
    Port_preset.update(Custom_port_preset_temp)

    try:
        with open("presets/port_presets.json", "w") as f:
            json.dump(Port_preset, f, indent=4)
        print(GREEN + "Custom preset saved successfully!" + RESET)
    except Exception as e:
        print(RED + f"Failed to save custom preset. Exception: {e}" + RESET)
        exit()

    PORTS.extend(CPPP_temp)

elif Port_presets in Port_preset:
    PORTS.extend(Port_preset[Port_presets])

else:
    print(RED + "Preset not found. Try 'help' to see available presets." + RESET)
    exit()

TO = input("Please enter a timeout value (sec). Type 'none' if you'd like not to have any artificial timeout\n")
if TO.isdigit():
    TO = int(TO)
    socket.setdefaulttimeout(TO)
elif TO.lower() == "none":
    pass
else:
    print("Error, please enter a valid timeout value.\n")

IP = socket.gethostbyname(DOMAIN)

for PORT in PORTS:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(TO)
        try:
            s.connect((DOMAIN, PORT))
            print(GREEN + f"[+] Open port detected at port {PORT} on IP/domain {DOMAIN}" + RESET)
            OPEN_PORTS.append(PORT)

            service = PORT_SERVICES.get(PORT, "Unknown")
            print(f"[+] Open port {PORT} ({service})")

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
                print(YELLOW + f"Received data on port {PORT} of {DOMAIN}, {IP}:\n{decoded}" + RESET)
            else:
                print("No data received.")
            
            if PORT == PORTS[0]:
                try:
                    HOST = socket.gethostbyaddr(IP)
                    print(f"Host for {DOMAIN} detected: {HOST}")
                except Exception as e:
                    print(f"Could not resolve host for {DOMAIN}: {e}")
        except socket.timeout:
            print(RED + f"[-] Port {PORT} timed out." + RESET)
        except socket.error as e:
            print(RED + f"[-] Failed to connect to port {PORT}. Error: {e}" + RESET)

print(f"Open ports: {OPEN_PORTS}")
input("Press \"Enter\" to exit...")
