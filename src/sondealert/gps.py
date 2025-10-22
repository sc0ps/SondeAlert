import socket
import threading
import logging

logger = logging.getLogger("gps")

_last_gps = {"lat": None, "lon": None, "fix": False}


def parse_nmea_latlon(nmea_lat, nmea_ns, nmea_lon, nmea_ew):
    """Converteer NMEA-formaat (DDMM.MMMM) naar decimale graden."""
    try:
        lat_deg = float(nmea_lat[:2])
        lat_min = float(nmea_lat[2:])
        lon_deg = float(nmea_lon[:3])
        lon_min = float(nmea_lon[3:])
        lat = lat_deg + lat_min / 60.0
        lon = lon_deg + lon_min / 60.0
        if nmea_ns == "S":
            lat = -lat
        if nmea_ew == "W":
            lon = -lon
        return lat, lon
    except Exception:
        return None, None


def start_gps_thread(settings):
    """Start de thread die GPS-data luistert via UDP."""
    t = threading.Thread(target=_gps_listener, args=(settings,), daemon=True)
    t.start()
    logger.info("GPS thread started.")


def _gps_listener(settings):
    """Luistert continu naar NMEA-GPS-data via UDP."""
    gps_port = int(settings.get("GPS_PORT", 5050))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", gps_port))
    logger.info(f"Listening on UDP port {gps_port} for GPS data")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            line = data.decode("utf-8", errors="ignore").strip()
            if not line.startswith("$GP") and not line.startswith("$GN"):
                continue

            # --- RMC-zin (aanbevolen voor positie)
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                parts = line.split(",")
                if len(parts) > 6 and parts[2] == "A":  # A = valid fix
                    lat, lon = parse_nmea_latlon(parts[3], parts[4], parts[5], parts[6])
                    if lat and lon:
                        _last_gps.update({"lat": lat, "lon": lon, "fix": True})
                        logger.info(f"Received GPS position: {lat:.5f}, {lon:.5f} (fix=True)")
            # --- GGA-zin (ook geldig)
            elif line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                parts = line.split(",")
                if len(parts) > 6 and parts[6] != "0":  # fix indicator not 0
                    lat, lon = parse_nmea_latlon(parts[2], parts[3], parts[4], parts[5])
                    if lat and lon:
                        _last_gps.update({"lat": lat, "lon": lon, "fix": True})
                        logger.info(f"Received GPS position: {lat:.5f}, {lon:.5f} (fix=True)")

        except Exception as e:
            logger.warning(f"GPS receive error: {e}")


def get_last_position():
    """Retourneer de laatst bekende GPS-positie."""
    return _last_gps
