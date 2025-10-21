import socket
import time
from .utils import get_logger

logger = get_logger("gps")

# Globale data die door andere modules (webserver) wordt uitgelezen
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
    except Exception as e:
        logger.debug("Kon GGA-zin niet parsen: %s (%s)", line, e)
        return None, None


def start_gps_listener(port: int = 5050):
    """Luistert naar UDP-NMEA zinnen en logt alles wat binnenkomt."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    logger.info("Luistert op UDP-poort %d voor GPS-data", port)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            line = data.decode(errors="ignore").strip()
            if not line:
                continue

            # Debug: log elke ontvangen regel
            logger.info("Ontvangen ruwe GPS-data van %s: %s", addr, line)

            # Alleen GGA of RMC zinnen gebruiken voor positie
            if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                lat, lon = parse_nmea_gga(line)
                if lat and lon:
                    gps_data["lat"] = lat
                    gps_data["lon"] = lon
                    gps_data["last_update"] = time.time()
                    logger.info("GPS-positie ontvangen: %.5f, %.5f", lat, lon)
            elif line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                # Optioneel: RMC-zin voor lat/lon
                parts = line.split(",")
                if len(parts) >= 7:
                    try:
                        lat_raw = parts[3]
                        lon_raw = parts[5]
                        if lat_raw and lon_raw:
                            lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60
                            lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60
                            if parts[4] == "S":
                                lat = -lat
                            if parts[6] == "W":
                                lon = -lon
                            gps_data["lat"] = lat
                            gps_data["lon"] = lon
                            gps_data["last_update"] = time.time()
                            logger.info("GPS-positie ontvangen (RMC): %.5f, %.5f", lat, lon)
                    except Exception as e:
                        logger.debug("Kon RMC-zin niet parsen: %s", e)

        except Exception as e:
            logger.error("Fout bij lezen GPS-data: %s", e)
            time.sleep(1)
