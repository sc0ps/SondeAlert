import socket
import threading
import logging
import json

logger = logging.getLogger("gps")
latest_gps = {"lat": None, "lon": None, "fix": False}

def parse_nmea(data):
    try:
        parts = data.split(',')
        if parts[0].endswith("RMC") and parts[2] == "A":  # valid fix
            lat = float(parts[3][:2]) + float(parts[3][2:]) / 60
            if parts[4] == 'S': lat = -lat
            lon = float(parts[5][:3]) + float(parts[5][3:]) / 60
            if parts[6] == 'W': lon = -lon
            return lat, lon, True
        return None, None, False
    except Exception:
        return None, None, False

def gps_listener(port=5050):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    logger.info("Listening on UDP port %d for GPS data", port)
    while True:
        data, _ = sock.recvfrom(1024)
        msg = data.decode(errors='ignore').strip()
        lat, lon, fix = parse_nmea(msg)
        if lat and lon:
            latest_gps.update({"lat": lat, "lon": lon, "fix": fix})
            logger.info("Received GPS position: %.5f, %.5f (fix=%s)", lat, lon, fix)

def start_gps_listener(port=5050):
    t = threading.Thread(target=gps_listener, args=(port,), daemon=True)
    t.start()
    logger.info("GPS thread started.")

def get_last_position():
    return latest_gps
