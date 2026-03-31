"""
Geospatial Service — Shoelace formula, convex hull, territory logic.
Core computational geometry for RunConquer.
"""
import math
from typing import List, Tuple

Point = Tuple[float, float]  # (lat, lng)


def haversine_distance(p1: Point, p2: Point) -> float:
    """Calculate distance between two GPS points in meters using Haversine formula."""
    R = 6371000  # Earth's radius in meters
    lat1, lng1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lng2 = math.radians(p2[0]), math.radians(p2[1])

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def total_path_distance(points: List[Point]) -> float:
    """Calculate total path distance in km."""
    if len(points) < 2:
        return 0.0
    total = sum(haversine_distance(points[i], points[i + 1]) for i in range(len(points) - 1))
    return total / 1000.0  # Convert to km


def shoelace_area(polygon: List[Point]) -> float:
    """
    Calculate polygon area using the Shoelace (Gauss) formula.
    Coordinates are projected to meters first for accuracy.
    Returns area in square meters.
    """
    if len(polygon) < 3:
        return 0.0

    # Project lat/lng to approximate meters using equirectangular projection
    ref_lat = polygon[0][0]
    cos_lat = math.cos(math.radians(ref_lat))

    def to_meters(p: Point) -> Tuple[float, float]:
        x = (p[1] - polygon[0][1]) * cos_lat * 111320
        y = (p[0] - polygon[0][0]) * 110540
        return (x, y)

    projected = [to_meters(p) for p in polygon]

    # Shoelace formula
    n = len(projected)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += projected[i][0] * projected[j][1]
        area -= projected[j][0] * projected[i][1]
    return abs(area) / 2.0


def cross(o: Point, a: Point, b: Point) -> float:
    """Cross product of vectors OA and OB."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: List[Point]) -> List[Point]:
    """
    Compute convex hull using Andrew's monotone chain algorithm.
    Returns vertices in counter-clockwise order.
    """
    if len(points) < 3:
        return points[:]

    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    # Build lower hull
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def path_to_territory(path_points: List[Point], min_area: float = 500.0) -> dict:
    """
    Convert a run path into a territory polygon.
    
    Strategy:
    1. Close the path (connect end to start)
    2. Compute convex hull of all points
    3. Calculate area
    4. Return polygon if area >= min_area
    
    Returns: {"polygon": [...], "area_sqm": float} or None if too small
    """
    if len(path_points) < 4:
        return None

    # Use convex hull of the path points
    hull = convex_hull(path_points)
    if len(hull) < 3:
        return None

    area = shoelace_area(hull)
    if area < min_area:
        return None

    return {
        "polygon": hull,
        "area_sqm": area
    }


def point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    """Ray casting algorithm for point-in-polygon test."""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def polygons_overlap(poly1: List[Point], poly2: List[Point]) -> bool:
    """Check if two polygons overlap (simplified: check if any vertex is inside the other)."""
    for p in poly1:
        if point_in_polygon(p, poly2):
            return True
    for p in poly2:
        if point_in_polygon(p, poly1):
            return True
    return False


def calculate_speed(p1: Point, p2: Point, time_delta_seconds: float) -> float:
    """Calculate speed in km/h between two points."""
    if time_delta_seconds <= 0:
        return 0.0
    dist_m = haversine_distance(p1, p2)
    return (dist_m / 1000.0) / (time_delta_seconds / 3600.0)
