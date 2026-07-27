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
    import re
    import subprocess
    ips: list[str] = []
    seen: set[str] = set()
    try:
        out = subprocess.check_output(['ip', '-4', 'addr', 'show'], text=True, timeout=2)
        for ip in re.findall(r'inet (\d+\.\d+\.\d+\.\d+)', out):
            if not ip.startswith('127.') and ip not in seen:
                seen.add(ip)
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        # Fallback: probe routing table with multiple destinations
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


def _naoqi_version_label(robot_type: str, naoqi_ver: str) -> str:
    """Convert a NAOqi version string (e.g. '2.8.6.23') to a generation label."""
    try:
        major, minor = (int(x) for x in naoqi_ver.split('.')[:2])
    except Exception:
        return ''
    if robot_type == 'nao':
        return 'v6' if (major, minor) >= (2, 8) else 'v5'
    if robot_type == 'pepper':
        # Pepper body generation maps roughly to NAOqi major.minor
        if (major, minor) >= (2, 9):
            return 'v2'
        if (major, minor) >= (2, 5):
            return 'v1.8'
        return 'v1'
    return ''


def _http_fetch(ip: str, port: int, timeout: float = 0.5) -> bytes:
    """Fetch the root HTTP page from ip:port; return raw response bytes or b''."""
    try:
        with socket.create_connection((ip, port), timeout=timeout) as s:
            s.sendall(b'GET / HTTP/1.0\r\nHost: robot\r\nConnection: close\r\n\r\n')
            data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 16384:
                    break
        return data
    except Exception:
        return b''


def _naoqi_banner(ip: str) -> bytes:
    """Read the first bytes NAOqi sends after a raw TCP connect on port 9559."""
    try:
        with socket.create_connection((ip, 9559), timeout=0.5) as s:
            return s.recv(256)
    except Exception:
        return b''


def _detect_naoqi_type_and_version(ip: str, hostname: str) -> tuple[str, str]:
    """Return (robot_type, version_label) for a reachable NAOqi host (port 9559).

    Priority for type:
      1. Reverse-DNS hostname keywords (pepper / aldebaran / nao)
      2. HTTP response on port 80 or 8080 — look for 'pepper' in body
      3. NAOqi binary banner on port 9559 — robot name embedded in handshake
      4. Default 'nao'
    Version extracted from the 4-part version string in the HTTP response.
    """
    import re

    low = hostname.lower()
    if 'pepper' in low:
        robot_type = 'pepper'
    elif 'aldebaran' in low and 'nao' not in low:
        # Pepper robots register under Aldebaran's internal domain; NAO robots don't.
        robot_type = 'pepper'
    elif 'nao' in low:
        robot_type = 'nao'
    else:
        robot_type = None

    version_label = ''
    http_data = b''

    if robot_type is None or not version_label:
        for port in (80, 8080):
            data = _http_fetch(ip, port)
            if data:
                http_data = data
                break

    if http_data:
        body = http_data.lower()
        if robot_type is None:
            robot_type = 'pepper' if b'pepper' in body else None
        m = re.search(rb'(\d+\.\d+\.\d+\.\d+)', http_data)
        if m:
            version_label = _naoqi_version_label(robot_type or 'nao', m.group(1).decode())

    # Last resort: read the NAOqi binary handshake — it embeds the robot name
    if robot_type is None:
        banner = _naoqi_banner(ip)
        if b'pepper' in banner.lower():
            robot_type = 'pepper'

    return (robot_type or 'nao', version_label)


def _probe(ip: str, port: int, robot_type: str) -> dict | None:
    """Return a robot entry if ip:port accepts a TCP connection."""
    try:
        with socket.create_connection((ip, port), timeout=_PROBE_TIMEOUT):
            pass
        try:
            name = socket.gethostbyaddr(ip)[0].rstrip('.')
        except Exception:
            name = ip
        version = ''
        if port == 9559 and robot_type == 'nao':
            robot_type, version = _detect_naoqi_type_and_version(ip, name)
        return {'ip': ip, 'port': port, 'robot_type': robot_type, 'name': name, 'version': version}
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
