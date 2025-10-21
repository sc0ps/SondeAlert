import socket
import time
from .utils import get_logger

logger = get_logger("gps")

# Globale GPS-status die door webserver en proximity wordt gelezen
gps_data = {
    "lat": None,
    "lon": None,
    "last_update": 0
}


def parse_nmea_gga(line: str):
    """Parseer een $GPGGA of $GNGGA NMEA-zin en retourneer (lat, lon)."""
    try:
        parts = line.split(",")
        if len(parts) < 6:
            return None, None

        lat_raw = parts[2]
        lon_raw = parts[4]
        if not lat_raw or not lon_raw:
            return None, None

        lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60
        lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60

        if parts[3] == "S":
            lat = -lat
        if parts[5] == "W":
            lon = -lon

        return lat, lon
    except Exception:
        return None, None


def parse_nmea_rmc(line: str):
    """Parseer een $GPRMC of $GNRMC NMEA-zin en retourneer (lat, lon)."""
    try:
        parts = line.split(",")
        if len(parts) < 7:
            return None, None

        lat_raw = parts[3]
        lon_raw = parts[5]
        if not lat_raw or not lon_raw:
            return None, None

        lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60
        lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60

        if parts[4] == "S":
            lat = -lat
        if parts[6] == "W":
            lon = -lon

        return lat, lon
    except Exception:
        return None, None


def start_gps_listener(port: int = 5050):
    """Luistert naar UDP-NMEA zinnen en werkt gps_data bij."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    logger.info("Luistert op UDP-poort %d voor GPS-data", port)

    while True:
        try:
            data, _ = sock.recvfrom(1024)
            line = data.decode(errors="ignore").strip()
            if not line:
                continue

            lat, lon = None, None

            if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                lat, lon = parse_nmea_gga(line)
            elif line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                lat, lon = parse_nmea_rmc(line)

            if lat and lon:
                gps_data["lat"] = lat
                gps_data["lon"] = lon
                gps_data["last_update"] = time.time()
                logger.info("Positie ontvangen: %.5f, %.5f", lat, lon)

        except Exception as e:
            logger.error("Fout bij lezen GPS-data: %s", e)
            time.sleep(1)
