import json, os, time, threading
from .utils import state_lock, haversine
from .config import OUT_JSON

# --- GPIO setup (buzzer) ---
try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)
    HAVE_GPIO = True
except Exception as e:
    print(f"[!] GPIO niet beschikbaar: {e}")
    HAVE_GPIO = False

# --- Globale status ---
nearest, nearest_d_m = None, None

def blelele_pattern_for_distance(d):
    """
    Retourneert het patroon voor afstand:
    (aantal herhalingen, pauze_tussen_signalen_ms, blok_pauze_s)
    """
    if not d:
        return 0, 0, 10
    if d > 5000:
        return 1, 250, 10
    elif d > 2000:
        return 2, 200, 10
    elif d > 500:
        return 3, 180, 10
    else:
        return 5, 140, 10

def _load_items():
    """Laad sondes uit JSON-bestand"""
    if not os.path.exists(OUT_JSON):
        return []
    try:
        j = json.load(open(OUT_JSON))
        return j.get("items", [])
    except Exception:
        return []

def start_proximity(settings: dict, gps_module):
    """
    Start threads voor:
    - berekenen van dichtstbijzijnde sonde
    - aansturen van buzzer
    """
    thr = float(settings.get("NEAR_THRESHOLD_M", 15000.0))

    def nearest_loop():
        global nearest, nearest_d_m
        while True:
            with state_lock:
                have = gps_module.gps_have
                glat = gps_module.gps_lat
                glon = gps_module.gps_lon

            lst = _load_items()
            if have and lst:
                best = min(lst, key=lambda it: haversine(glat, glon, it["lat"], it["lon"]))
                d = haversine(glat, glon, best["lat"], best["lon"])
                with state_lock:
                    nearest, nearest_d_m = (best, d) if d <= thr else (None, None)
            else:
                with state_lock:
                    nearest, nearest_d_m = None, None
            time.sleep(1)

    def buzzer_loop():
        """Stuurt buzzer aan volgens afstandspatroon"""
        if not HAVE_GPIO:
            return
        while True:
            with state_lock:
                enabled = bool(settings.get("BUZZER_ENABLED", True))
                n = nearest
                d = nearest_d_m

            if enabled and n and d:
                reps, inner_ms, block_s = blelele_pattern_for_distance(d)
                for _ in range(reps):
                    for _ in range(6):  # 6 korte piepjes per blok
                        GPIO.output(18, GPIO.HIGH)
                        time.sleep(0.015)
                        GPIO.output(18, GPIO.LOW)
                        time.sleep(0.010)
                    time.sleep(inner_ms / 1000)
                time.sleep(block_s)
            else:
                time.sleep(0.2)

    threading.Thread(target=nearest_loop, daemon=True).start()
    threading.Thread(target=buzzer_loop, daemon=True).start()
