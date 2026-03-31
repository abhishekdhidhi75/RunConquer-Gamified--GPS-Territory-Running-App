/**
 * RunConquer — Geospatial Utilities (Frontend)
 * Haversine distance, convex hull, Shoelace area — all in JS.
 */

/**
 * Calculate Haversine distance between two points in meters.
 * @param {number[]} p1 - [lat, lng]
 * @param {number[]} p2 - [lat, lng]
 * @returns {number} Distance in meters
 */
function haversineDistance(p1, p2) {
  const R = 6371000;
  const toRad = deg => deg * Math.PI / 180;
  
  const lat1 = toRad(p1[0]), lng1 = toRad(p1[1]);
  const lat2 = toRad(p2[0]), lng2 = toRad(p2[1]);
  
  const dlat = lat2 - lat1;
  const dlng = lng2 - lng1;
  
  const a = Math.sin(dlat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlng / 2) ** 2;
  const c = 2 * Math.asin(Math.sqrt(a));
  return R * c;
}

/**
 * Calculate total path distance in km.
 * @param {number[][]} points - Array of [lat, lng]
 * @returns {number} Distance in km
 */
function calculateTotalDistance(points) {
  if (points.length < 2) return 0;
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) {
    total += haversineDistance(points[i], points[i + 1]);
  }
  return total / 1000;
}

/**
 * Cross product of vectors OA and OB.
 */
function cross(o, a, b) {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

/**
 * Compute convex hull using Andrew's monotone chain.
 * @param {number[][]} points - Array of [lat, lng]
 * @returns {number[][]} Hull vertices in order
 */
function computeConvexHull(points) {
  if (points.length < 3) return points.slice();
  
  const pts = [...new Set(points.map(p => p.join(',')))].map(s => s.split(',').map(Number));
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  
  if (pts.length < 3) return pts;
  
  // Lower hull
  const lower = [];
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  }
  
  // Upper hull
  const upper = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], pts[i]) <= 0) {
      upper.pop();
    }
    upper.push(pts[i]);
  }
  
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

/**
 * Calculate polygon area using Shoelace formula (projected to meters).
 * @param {number[][]} polygon - Array of [lat, lng]
 * @returns {number} Area in square meters
 */
function shoelaceArea(polygon) {
  if (polygon.length < 3) return 0;
  
  const refLat = polygon[0][0];
  const cosLat = Math.cos(refLat * Math.PI / 180);
  
  const projected = polygon.map(p => [
    (p[1] - polygon[0][1]) * cosLat * 111320,
    (p[0] - polygon[0][0]) * 110540
  ]);
  
  let area = 0;
  const n = projected.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    area += projected[i][0] * projected[j][1];
    area -= projected[j][0] * projected[i][1];
  }
  
  return Math.abs(area) / 2;
}
