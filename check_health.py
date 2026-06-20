import urllib.request

ports = {
    8000: "Council Core",
    8001: "Palantir Lake",
    8008: "Law Finance Core",
    8009: "Market Logistics",
    8010: "PAC Core",
    4001: "Real Estate Core",
    3000: "Onitas Market Core",
    9000: "Maroon Market Core"
}

for port, name in ports.items():
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = response.read().decode('utf-8')
            print(f"[{name}] (Port {port}): ONLINE -> {data[:100]}")
    except urllib.error.URLError as e:
        print(f"[{name}] (Port {port}): OFFLINE / TIMEOUT -> {e.reason}")
    except Exception as e:
        print(f"[{name}] (Port {port}): ERROR -> {e}")
