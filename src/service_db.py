def load_services(filename="nmap-services"):
    port_map = {}
    with open(filename, "r") as f:
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
