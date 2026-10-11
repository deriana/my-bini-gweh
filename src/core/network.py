import os
import socket
import struct
import urllib.request
from typing import Optional


def get_windows_host_ip() -> str:
    """
    Detects the Windows host IP address from WSL2 routing table (/proc/net/route)
    or resolv.conf. Falls back to 127.0.0.1 if not in WSL2.
    """
    try:
        if os.path.exists("/proc/net/route"):
            with open("/proc/net/route", "r") as f:
                for line in f:
                    fields = line.strip().split()
                    if len(fields) > 2 and fields[1] == "00000000":  # Default gateway
                        return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
    except Exception:
        pass

    try:
        if os.path.exists("/etc/resolv.conf"):
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.strip().startswith("nameserver"):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            return parts[1]
    except Exception:
        pass

    return "127.0.0.1"


def resolve_service_url(url: str, probe_path: str = "", timeout: float = 0.5) -> str:
    """
    If running under WSL2 and the URL references localhost/127.0.0.1,
    tests if localhost responds. If not, automatically resolves to the
    Windows host gateway IP so services on Windows (Ollama, VOICEVOX) work out-of-the-box.
    """
    if not url:
        return url

    clean_url = url.strip()
    if "127.0.0.1" not in clean_url and "localhost" not in clean_url:
        return clean_url

    # Check if localhost works directly
    test_target = clean_url if not probe_path else f"{clean_url.rstrip('/')}/{probe_path.lstrip('/')}"
    try:
        req = urllib.request.Request(test_target, headers={"User-Agent": "VTuber-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status < 500:
                return clean_url
    except Exception:
        pass

    # Localhost failed, attempt Windows host gateway resolution
    host_ip = get_windows_host_ip()
    if host_ip and host_ip != "127.0.0.1":
        resolved_url = clean_url.replace("127.0.0.1", host_ip).replace("localhost", host_ip)
        return resolved_url

    return clean_url
