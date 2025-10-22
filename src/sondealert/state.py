# /app/src/sondealert/state.py
import threading, time

_lock = threading.Lock()

_state = {
    "gps": {"lat": None, "lon": None, "fix": False, "ts": 0},
    "nearest": {"item": None, "distance_m": None, "ring_level": None},
    "last_update": 0,      # epoch sec (sondes)
    "sondes_count": 0
}

def set_gps(lat, lon, fix):
    with _lock:
        _state["gps"] = {"lat": lat, "lon": lon, "fix": bool(fix), "ts": int(time.time())}

def get_gps():
    with _lock:
        return dict(_state["gps"])

def set_nearest(item, d_m, ring_level):
    with _lock:
        _state["nearest"] = {"item": item, "distance_m": d_m, "ring_level": ring_level}

def get_nearest():
    with _lock:
        return dict(_state["nearest"])

def set_last_update(ts, count):
    with _lock:
        _state["last_update"] = ts
        _state["sondes_count"] = count

def get_meta():
    with _lock:
        return {"last_update": _state["last_update"], "sondes_count": _state["sondes_count"]}
