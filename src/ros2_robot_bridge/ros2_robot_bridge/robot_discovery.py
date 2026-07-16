"""
robot_discovery.py — Network discovery for NAO/Pepper/QT robots.

Strategy:
  1. mDNS/Bonjour (zeroconf) — passive, instant when robots broadcast.
  2. Port-scan fallback — scans the local /24 subnet for open NAOqi (9559)
     and QT (9090) ports. Runs once at startup and every SCAN_INTERVAL seconds.

Thread-safe; call start() once, read .robots at any time.
"""
import ipaddress
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SCAN_INTERVAL = 60          # seconds between automatic subnet rescans
_PROBE_TIMEOUT = 0.30       # seconds per host per port
_MAX_WORKERS   = 128

_PORTS = [
    (9559, 'nao'),
    (9090, 'qtrobot'),
]

try:
    from zeroconf import ServiceBrowser, Zeroconf
    _HAS_ZEROCONF = True
except ImportError:
    _HAS_ZEROCONF = False


def _local_ips() -> list[str]:
    """Return all non-loopback local IPv4 addresses across all interfaces."""
    seen: set[str] = set()
    ips: list[str] = []
    # Probe several destinations to capture IPs on different interfaces/subnets
    for dest in ('10.0.0.0', '192.168.0.0', '172.16.0.0', '8.8.8.8'):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.connect((dest, 80))
                ip = s.getsockname()[0]
                if not ip.startswith('127.') and ip not in seen:
                    seen.add(ip)
                    ips.append(ip)
            except Exception:
                pass
    return ips


def _probe(ip: str, port: int, robot_type: str) -> dict | None:
    """Return a robot entry if ip:port accepts a TCP connection."""
    try:
        with socket.create_connection((ip, port), timeout=_PROBE_TIMEOUT):
            pass
        try:
            name = socket.gethostbyaddr(ip)[0].rstrip('.')
        except Exception:
            name = ip
        return {'ip': ip, 'port': port, 'robot_type': robot_type, 'name': name}
    except Exception:
        return None


def _scan_subnet(network: ipaddress.IPv4Network) -> list[dict]:
    results = []
    tasks = [
        (str(host), port, rtype)
        for host in network.hosts()
        for port, rtype in _PORTS
    ]
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        futures = {ex.submit(_probe, ip, port, rtype): None for ip, port, rtype in tasks}
        for fut in as_completed(futures):
            r = fut.result()
            if r:
                results.append(r)
    return results


class RobotDiscovery:
    """Discover robots on the local network via mDNS and port scanning."""

    def __init__(self):
        self._lock        = threading.Lock()
        self._mdns: dict  = {}    # service_name → entry (from zeroconf)
        self._scan: list  = []    # entries from last port scan
        self._scanning    = False
        self._zc          = None
        self._stop_event  = threading.Event()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if _HAS_ZEROCONF:
            self._zc = Zeroconf()
            ServiceBrowser(self._zc, '_naoqi._tcp.local.', self)
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def stop(self):
        self._stop_event.set()
        if self._zc:
            self._zc.close()

    # ── mDNS listener ─────────────────────────────────────────────────────────

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if not info or not info.addresses:
            return
        try:
            ip = str(ipaddress.ip_address(info.addresses[0]))
        except Exception:
            return
        server = (info.server or ip).rstrip('.')
        entry = {'ip': ip, 'port': info.port,
                 'robot_type': 'pepper' if 'pepper' in server.lower() else 'nao',
                 'name': server, 'source': 'mdns'}
        with self._lock:
            self._mdns[name] = entry

    def remove_service(self, zc, type_, name):
        with self._lock:
            self._mdns.pop(name, None)

    def update_service(self, zc, t, n):
        self.add_service(zc, t, n)

    # ── Port-scan loop ────────────────────────────────────────────────────────

    def _scan_loop(self):
        while not self._stop_event.is_set():
            self._run_scan()
            self._stop_event.wait(SCAN_INTERVAL)

    def _run_scan(self):
        with self._lock:
            self._scanning = True
        try:
            locals_ = _local_ips()
            if not locals_:
                return
            results = []
            seen_nets: set[str] = set()
            for local in locals_:
                net = ipaddress.ip_network(f'{local}/24', strict=False)
                if str(net) in seen_nets:
                    continue
                seen_nets.add(str(net))
                results.extend(_scan_subnet(net))
            with self._lock:
                self._scan = results
        finally:
            with self._lock:
                self._scanning = False

    def refresh(self):
        """Trigger an immediate background rescan."""
        threading.Thread(target=self._run_scan, daemon=True).start()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def scanning(self) -> bool:
        return self._scanning

    @property
    def robots(self) -> list:
        with self._lock:
            # Merge mDNS + scan; deduplicate by IP
            seen: dict[str, dict] = {}
            for e in list(self._mdns.values()) + self._scan:
                seen[e['ip']] = e
            return list(seen.values())
