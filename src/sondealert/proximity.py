# /app/src/sondealert/proximity.py
import json, math, time, logging, os
from .config import SONDES_FILE
from .state import get_gps, set_nearest

def _deg2rad(d): return d*math.pi/180.0
def haversine(lat1, lon1, lat2, lon2):
    R=6371000.0
    dLat=_deg2rad(lat2-lat1); dLon=_deg2rad(lon2-lon1)
    a=math.sin(dLat/2)**2+math.cos(_deg2rad(lat1))*math.cos(_deg2rad(lat2))*math.sin(dLon/2)**2
    return R*2*math.atan2(math.sqrt(a), math.sqrt(1-a))

def load_sondes():
    if not os.path.exists(SONDES_FILE): return {"generated":0,"count":0,"items":[]}
    with open(SONDES_FILE,"r") as f:
        return json.load(f)

def compute_nearest(settings):
    gps = get_gps()
    if not gps.get("fix"): 
        set_nearest(None, None, None); 
        return

    data = load_sondes()
    items = data.get("items", [])
    if not items:
        set_nearest(None, None, None); 
        return

    glat, glon = gps["lat"], gps["lon"]
    best, best_d = None, None
    for it in items:
        d = haversine(glat, glon, it["lat"], it["lon"])
        if best_d is None or d < best_d:
            best, best_d = it, d

    # ring-level per 2 km
    thr = float(settings["NEAR_THRESHOLD_M"])
    if best_d is None or best_d > thr:
        set_nearest(None, None, None); 
        return

    ring = max(1, int((thr - best_d) // 2000) + 1)  # 2km ringen, dichterbij = hogere ring
    set_nearest(best, best_d, ring)

def proximity_loop(settings):
    logging.info("[proximity] Afstandsbepaling gestart (radius %.1f km)", float(settings["NEAR_THRESHOLD_M"])/1000.0)
    while True:
        try:
            compute_nearest(settings)
        except Exception as e:
            logging.warning("[proximity] Fout: %s", e)
        time.sleep(1)
