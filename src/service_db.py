from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVICES_FILE = BASE_DIR / "nmap-services"

def load_services(filename=SERVICES_FILE):
    port_map = {}
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            try:
                parts = line.split()
                service = parts[0]
                port_proto = parts[1]
                port, proto = port_proto.split('/')
                port_map[int(port)] = service.upper()
            except Exception as e:
                continue
    return port_map

PORT_SERVICES = load_services()
