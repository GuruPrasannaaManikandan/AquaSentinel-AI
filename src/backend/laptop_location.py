"""
Location of the gateway laptop, used as the deployment location of the physical node
(there is no GPS module on the ESP32).

Source: Windows Location (System.Device GeoCoordinateWatcher via PowerShell). The result is
cached for 10 minutes. If Windows Location is off or fails, the location is None and the
dashboard shows N/A; no coordinate is ever invented.
"""
import subprocess
import threading
import time
from typing import Any, Dict, Optional

CACHE_SEC = 600
_FAIL_RETRY_SEC = 60

_PS_SCRIPT = (
    "Add-Type -AssemblyName System.Device;"
    "$w = New-Object System.Device.Location.GeoCoordinateWatcher;"
    "$null = $w.TryStart($false, [TimeSpan]::FromSeconds(10));"
    "$t = 0; while ($w.Position.Location.IsUnknown -and $t -lt 40) { Start-Sleep -Milliseconds 250; $t++ };"
    "$l = $w.Position.Location;"
    "if ($l.IsUnknown) { 'UNKNOWN ' + $w.Permission } else {"
    "  [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0} {1} {2}', $l.Latitude, $l.Longitude, $l.HorizontalAccuracy) };"
    "$w.Stop()"
)

_lock = threading.Lock()
_cache: Dict[str, Any] = {"at": 0.0, "value": None, "error": None}


def _query_windows_location() -> Dict[str, Any]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_SCRIPT],
        capture_output=True, text=True, timeout=25,
    ).stdout.strip()
    if not out or out.startswith("UNKNOWN"):
        perm = out.split(" ", 1)[1] if " " in out else "unknown"
        raise RuntimeError(f"Windows Location returned no fix (permission: {perm}). "
                           "Turn on Settings > Privacy > Location and allow desktop apps.")
    lat, lon, acc = (float(x) for x in out.split()[:3])
    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "accuracy_m": round(acc) if acc == acc else None,  # NaN check
        "source": "WINDOWS_LOCATION",
        "label": f"Location: laptop (Windows Location, ±{round(acc)} m)",
    }


def get_laptop_location(force: bool = False) -> Dict[str, Any]:
    """Returns {"available": bool, latitude, longitude, accuracy_m, source, label, fetched_at, error}."""
    with _lock:
        age = time.time() - _cache["at"]
        ttl = CACHE_SEC if _cache["value"] else _FAIL_RETRY_SEC
        if force or _cache["at"] == 0.0 or age > ttl:
            try:
                _cache["value"] = _query_windows_location()
                _cache["error"] = None
            except Exception as e:
                _cache["value"] = None
                _cache["error"] = str(e)
            _cache["at"] = time.time()
        value: Optional[Dict[str, Any]] = _cache["value"]
        result = {"available": value is not None, "fetched_at": _cache["at"], "error": _cache["error"]}
        if value:
            result.update(value)
        else:
            result.update({"latitude": None, "longitude": None, "accuracy_m": None,
                           "source": None, "label": "Location: N/A (laptop location unavailable)"})
        return result
