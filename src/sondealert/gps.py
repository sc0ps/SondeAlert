import socket
import threading
import logging
import re

logger = logging.getLogger("gps")

# Globale GPS-status
last_position = {
    "lat": None,
    "lon": None,
    "fix": False
}

def parse_nmea_latlon(lat_str, ns, lon_str, ew):
    """Converteer NMEA latitude/longitude naar decimale graden."""
    try:
        lat_deg = float(lat_str[:2])
        lat_min = float(lat_str[2:])
        lon_deg = float(lon_str[:3])
        lon_min = float(lon_str[3:])
        lat = lat_deg + lat_min / 60.0
        lon = lon_deg + lon_min / 60.0
        if ns == "S":
            lat = -lat
        if ew == "W":
            lon = -lon
        return lat, lon
    except Exception:
        return None, None


def process_nmea_sentence(data):
    """Verwerk één NMEA-zin en update de laatste GPS-positie."""
    global last_position

    # Match GGA of RMC
    if data.startswith(("$GNGGA", "$GPGGA")):
        parts = data.split(",")
        if len(parts) > 5 and parts[2] and parts[4]:
            lat, lon = parse_nmea_latlon(parts[2], parts[3], parts[4], parts[5])
            if lat and lon:
                last_position["lat"] = lat
                last_position["lon"] = lon
                last_position["fix"] = parts[6] not in ("0", "")
                logger.info(f"Received GPS position: {lat:.5f}, {lon:.5f} (fix={last_position['fix']})")

    elif data.startswith(("$GNRMC", "$GPRMC")):
        parts = data.split(",")
        if len(parts) > 6 and parts[3] and parts[5]:
            lat, lon = parse_nmea_latlon(parts[3], parts[4], parts[5], parts[6])
            if lat and lon:
                last_position["lat"] = lat
                last_position["lon"] = lon
                last_position["fix"] = parts[2] == "A"
                logger.info(f"Received GPS position (RMC): {lat:.5f}, {lon:.5f}")


def start_gps_thread(settings):
    """Start een achtergrondthread die luistert op UDP 5050."""
    port = settings.get("GPS_PORT", 5050)
    thread = threading.Thread(target=gps_listener, args=(port,), daemon=True)
    thread.start()
    logger.info("GPS thread started.")


def gps_listener(port):
    """Luister op de ingestelde UDP-poort naar NMEA-data."""
    global last_position
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    logger.info(f"Listening on UDP port {port} for GPS data")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            line = data.decode(errors="ignore").strip()
            logger.debug(f"Received raw GPS data from {addr}: {line}")
            process_nmea_sentence(line)
        except Exception as e:
            logger.warning(f"Error in GPS listener: {e}")


def get_last_position():
    """Geef de laatst bekende GPS-positie."""
    return last_position
