"""
Modul de Fotogrammetrie pentru DJI Mini 3.
Transformă coordonatele pixelilor din detecțiile AI în coordonate GPS reale.
"""

import math
from typing import Tuple, List, Dict

# ==========================================
# CONSTANTE HARDWARE (DJI Mini 3 Standard)
# ==========================================
SENSOR_WIDTH_MM = 9.6  # Lățimea fizică a senzorului (mm)
FOCAL_LENGTH_MM = 6.72  # Distanța focală reală a lentilei (mm)
EARTH_RADIUS_M = 6371000.0  # Raza medie a Pământului (metri)


def calculate_coordinates(
        x_ai: float,
        y_ai: float,
        lat_drone: float,
        lon_drone: float,
        yaw_drone: float,
        pitch_camera: float,
        h: float = 2.0,
        rezolutie: str = "1080p"
) -> Tuple[float, float]:
    """
    Calculează coordonata GPS absolută pentru o singură detecție AI.
    """
    # 1. Setare rezoluție
    if rezolutie == "1080p":
        img_w, img_h = 1920, 1080
    elif rezolutie == "720p":
        img_w, img_h = 1280, 720
    else:
        raise ValueError("Rezoluție nesuportată. Alege '1080p' sau '720p'.")

    # 2. Calcul GSD (Metri/Pixel)
    gsd = (h * SENSOR_WIDTH_MM) / (FOCAL_LENGTH_MM * img_w)

    # 3. Conversie din Pixeli în Metri (față de centrul imaginii)
    dx_px = x_ai - (img_w / 2.0)
    dy_px = (img_h / 2.0) - y_ai  # Inversare axa Y

    dist_x_m = dx_px * gsd

    # 4. Corecția de unghi a camerei (Pitch)
    theta_rad = math.radians(90.0 - pitch_camera)
    d_centru = h * math.tan(theta_rad)

    dist_y_m = d_centru + (dy_px * gsd)

    # 5. Calcul distanță totală și unghi pe sol
    d_final = math.sqrt(dist_x_m ** 2 + dist_y_m ** 2)
    unghi_offset_grade = math.degrees(math.atan2(dist_x_m, dist_y_m))
    alpha_final_rad = math.radians(yaw_drone + unghi_offset_grade)

    # 6. Transformare în GPS (Lat/Lon)
    lat_rad = math.radians(lat_drone)

    delta_lat = (d_final * math.cos(alpha_final_rad) / EARTH_RADIUS_M) * (180.0 / math.pi)
    delta_lon = (d_final * math.sin(alpha_final_rad) / (EARTH_RADIUS_M * math.cos(lat_rad))) * (180.0 / math.pi)

    lat_obiect = lat_drone + delta_lat
    lon_obiect = lon_drone + delta_lon

    return lat_obiect, lon_obiect


