# /app/src/sondealert/buzzer.py
import time, logging

try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)
    HAVE_GPIO = True
except Exception as e:
    logging.info("[buzzer] GPIO niet beschikbaar: %s", e)
    HAVE_GPIO = False

from .state import get_nearest

def pattern_for_ring(ring):
    # ring: hoe dichterbij, hoe hoger (bijv. 1..N)
    # Stel basispatronen in (je kunt dit naar wens tunen)
    if not ring or ring <= 1:   # buitenste ring of net binnen
        return 1, 0.25, 8   # 1x "ble", pauze 250ms, rust 8s
    elif ring <= 3:
        return 2, 0.20, 6   # 2x ble, 200ms, rust 6s
    elif ring <= 5:
        return 3, 0.18, 4   # 3x ble, 180ms, rust 4s
    else:
        return 5, 0.14, 3   # 5x ble, 140ms, rust 3s

def _ble():
    GPIO.output(18, GPIO.HIGH); time.sleep(0.015)
    GPIO.output(18, GPIO.LOW);  time.sleep(0.010)

def buzzer_loop(settings):
    if not HAVE_GPIO:
        logging.info("[buzzer] Overgeslagen (geen GPIO).")
        while True: time.sleep(2)

    logging.info("[buzzer] Gestart.")
    while True:
        try:
            if not settings.get("BUZZER_ENABLED", True):
                time.sleep(0.5); continue

            n = get_nearest()
            item, ring = n.get("item"), n.get("ring_level")
            if not item or not ring:
                time.sleep(0.5); continue

            reps, inner_s, block_s = pattern_for_ring(ring)
            for _ in range(reps):
                for __ in range(6):  # kleine triller
                    _ble()
                time.sleep(inner_s)
            time.sleep(block_s)
        except Exception:
            time.sleep(0.5)
