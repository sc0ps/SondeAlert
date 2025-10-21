import math, threading

# Gedeelde thread-lock (voorkomt dat meerdere threads tegelijk data wijzigen)
state_lock = threading.Lock()

def deg2rad(d):
    """Graden naar radialen"""
    return d * math.pi / 180.0

def haversine(lat1, lon1, lat2, lon2):
    """Bereken afstand in meter tussen twee GPS-coördinaten"""
    R = 6371000.0  # aardstraal in meter
    dLat = deg2rad(lat2 - lat1)
    dLon = deg2rad(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.sin(dLon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))