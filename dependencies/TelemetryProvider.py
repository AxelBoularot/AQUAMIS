from __future__ import annotations

import math
import time
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Mapping


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", ".")
        return float(text)
    except Exception:
        return default


def _get_any(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


@dataclass
class TelemetrySnapshot:
    speed: float
    ballast: int
    signal: int
    pressure_bar: float
    depth_m: float
    pos_x: float
    pos_y: float
    pos_z: float
    elec_temp_c: float


class TelemetryProvider:
                                                                                        

    def __init__(self):
        self._t0 = time.time()
        self._wifi_last_t = 0.0
        self._wifi_last_val: int | None = None

    def _read_windows_wifi_signal_percent(self) -> int | None:
                                                                              
        now = time.time()
        if now - self._wifi_last_t < 1.0:
            return self._wifi_last_val
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output("netsh wlan show interfaces", startupinfo=startupinfo)
            text = output.decode("utf-8", errors="ignore")
            match = re.search(r"Signal\s*:\s*(\d+)%", text)
            if not match:
                self._wifi_last_val = None
            else:
                self._wifi_last_val = int(match.group(1))
            self._wifi_last_t = now
            return self._wifi_last_val
        except Exception:
            self._wifi_last_t = now
            return None

    def snapshot(self, *, use_phone_sensors: bool, pitch: float, data: Mapping[str, Any] | None) -> TelemetrySnapshot:
        d = data or {}
        t = time.time() - self._t0

        if use_phone_sensors:
            tilt = float(pitch)
            speed = 0.0
            if abs(tilt) > 5:
                normalized = min(1.0, (abs(tilt) - 5) / 40.0)
                speed = (normalized**2) * 15.0
            ballast = 50
            signal = self._read_windows_wifi_signal_percent() or 50
        else:
            speed = _to_float(_get_any(d, "Speed", "speed", "speed_kmh", "vitesse"), 0.0)
            ballast = int(_to_float(_get_any(d, "Ballast", "ballast", "ballast_pct"), 0.0))
            signal = int(_to_float(_get_any(d, "Signal", "signal", "signal_pct"), 0.0))

        if speed == 0.0:
            speed = 2.0 + 1.2 * math.sin(t * 0.35)
        if ballast == 0:
            ballast = int(40 + 10 * math.sin(t * 0.12))
        if signal == 0:
            signal = int(70 + 15 * math.sin(t * 0.2))

        pressure = _to_float(_get_any(d, "Pressure", "pressure", "pressure_bar", "Pression"), 0.0)
        depth = _to_float(_get_any(d, "Depth", "depth", "depth_m", "Profondeur"), 0.0)
        if pressure == 0.0:
            pressure = 1.4 + 0.2 * math.sin(t * 0.09)
        if depth == 0.0:
            depth = 2.3 + 0.8 * math.sin(t * 0.06)

        pos_x = _to_float(_get_any(d, "pos_x", "x", "PosX"), 0.0)
        pos_y = _to_float(_get_any(d, "pos_y", "y", "PosY"), 0.0)
        pos_z = _to_float(_get_any(d, "pos_z", "z", "PosZ"), 0.0)
        if pos_x == 0.0:
            pos_x = 2.0 * math.sin(t * 0.04)
        if pos_y == 0.0:
            pos_y = 1.5 * math.sin(t * 0.03 + 1.0)
        if pos_z == 0.0:
            pos_z = -depth

        temp = _to_float(_get_any(d, "Temp", "temp", "temp_c", "temp_elec", "Temperature"), 0.0)
        if temp == 0.0:
            temp = 38.0 + 3.5 * math.sin(t * 0.08)

        return TelemetrySnapshot(
            speed=float(speed),
            ballast=int(max(0, min(100, ballast))),
            signal=int(max(0, min(100, signal))),
            pressure_bar=float(pressure),
            depth_m=float(depth),
            pos_x=float(pos_x),
            pos_y=float(pos_y),
            pos_z=float(pos_z),
            elec_temp_c=float(temp),
        )
