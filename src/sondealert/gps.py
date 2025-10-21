# src/sondealert/gps.py
import socket
import threading
import time
from .utils import state_lock, get_logger

logger = get_logger("gps")

# Gedeelde GPS-data (laatste positie)
gps_data = {"lat": None, "lon": None, "last_update": 0}


def parse_nmea(line: str):
    """
    Eenvoudige parser voor NMEA-zinnen (GPRMC of GPGGA).
    Retourneert (lat, lon) of None als ongeldige zin.
    """
    try:
        if line.startswith("$GPRMC"):
            parts = line.split(",")
            if parts[3] and parts[5]:
                lat = float(parts[3][:2]) + float(parts[3][2:]) / 60.0
                lon = float(parts[5][:3]) + float(parts[5][3:]) / 60.0
                if parts[4] == "S":
                    lat *= -1
                if parts[6] == "W":
                    lon *= -1
                return lat, lon

        elif line.startswith("$GPGGA"):
            parts = line.split(",")
            if parts[2] and parts[4]:
                lat = float(parts[2][:2]) + float(parts[2][2:]) / 60.0
                lon = float(parts[4][:3]) + float(parts[4][3:]) / 60.0
                if parts[3] == "S":
                    lat *= -1
                if parts[5] == "W":
                    lon *= -1
                return lat, lon
    except Exception as e:
        logger.debug("Parserfout: %s", e)

    return None


def start_gps_listener(port: int = 5050):
    """
    Luistert op de opgegeven UDP-poort naar NMEA-gegevens en
    werkt gps_data bij met de laatste bekende positie.
    """
    logger.info("Luistert op UDP-poort %d voor GPS-data", port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(5.0)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            line = data.decode("utf-8", errors="ignore").strip()

            pos = parse_nmea(line)
            if pos:
                lat, lon = pos
                with state_lock:
                    gps_data["lat"] = lat
                    gps_data["lon"] = lon
                    gps_data["last_update"] = time.time()

                logger.info("GPS-positie ontvangen: %.5f, %.5f", lat, lon)
            else:
                logger.debug("Ongeldige of incomplete NMEA-zin: %s", line[:40])

        except socket.timeout:
            now = time.time()
            with state_lock:
                if gps_data["last_update"] and now - gps_data["last_update"] > 15:
                    logger.warning("Geen GPS-data ontvangen in 15 seconden.")
            continue
        except Exception as e:
            logger.exception("Fout in GPS-listener: %s", e)
            time.sleep(2)
