import json
import os
from typing import Dict, Optional, Tuple, Any
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString
import pyproj
from shapely.ops import transform


class AirportMap:
    """
    Airport Reference Data Layer using GeoPandas & Shapely.
    Provides geospatial validation functions against airport boundary, runways, and taxiways.
    """

    def __init__(self, geojson_path: str):
        if not os.path.exists(geojson_path):
            raise FileNotFoundError(f"GeoJSON reference file not found at: {geojson_path}")
        
        self.geojson_path = geojson_path
        self.gdf = gpd.read_file(geojson_path)
        
        # Extract features by type
        self.boundary_gdf = self.gdf[self.gdf["type"] == "boundary"]
        self.runways_gdf = self.gdf[self.gdf["type"] == "runway"]
        self.taxiways_gdf = self.gdf[self.gdf["type"] == "taxiway"]
        
        # Coordinate Transformer (WGS84 -> World Mercator EPSG:3857 for metric distances)
        self.wgs84_to_metric = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform

    def _point_in_metric(self, lat: float, lon: float) -> Point:
        """Helper to convert WGS84 (lat, lon) to metric Shapely Point (x=lon, y=lat)."""
        x, y = self.wgs84_to_metric(lon, lat)
        return Point(x, y)

    def is_inside_airport_boundary(self, lat: float, lon: float) -> bool:
        """Returns True if (lat, lon) is within the airport boundary polygon."""
        point = Point(lon, lat)
        for _, row in self.boundary_gdf.iterrows():
            if row.geometry.contains(point):
                return True
        return False

    def distance_from_runway(self, lat: float, lon: float) -> float:
        """Calculates distance in meters from the point to the nearest runway center line."""
        if self.runways_gdf.empty:
            return float("inf")
        
        point_m = self._point_in_metric(lat, lon)
        min_dist = float("inf")
        
        for _, row in self.runways_gdf.iterrows():
            geom_m = transform(self.wgs84_to_metric, row.geometry)
            dist = geom_m.distance(point_m)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def distance_from_taxiway(self, lat: float, lon: float) -> float:
        """Calculates distance in meters from the point to the nearest taxiway center line."""
        if self.taxiways_gdf.empty:
            return float("inf")
        
        point_m = self._point_in_metric(lat, lon)
        min_dist = float("inf")
        
        for _, row in self.taxiways_gdf.iterrows():
            geom_m = transform(self.wgs84_to_metric, row.geometry)
            dist = geom_m.distance(point_m)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def is_on_valid_runway(self, lat: float, lon: float, buffer_m: float = 50.0) -> bool:
        """Checks whether position is within buffer_m meters of any runway."""
        return self.distance_from_runway(lat, lon) <= buffer_m

    def is_on_valid_taxiway(self, lat: float, lon: float, buffer_m: float = 30.0) -> bool:
        """Checks whether position is within buffer_m meters of any taxiway."""
        return self.distance_from_taxiway(lat, lon) <= buffer_m

    def nearest_runway(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Returns metadata of the nearest runway to the given coordinate."""
        if self.runways_gdf.empty:
            return None
        
        point_m = self._point_in_metric(lat, lon)
        min_dist = float("inf")
        nearest_feature = None
        
        for _, row in self.runways_gdf.iterrows():
            geom_m = transform(self.wgs84_to_metric, row.geometry)
            dist = geom_m.distance(point_m)
            if dist < min_dist:
                min_dist = dist
                nearest_feature = {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "heading_deg": row.get("heading_deg"),
                    "distance_m": round(dist, 2)
                }
        return nearest_feature

    def nearest_taxiway(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Returns metadata of the nearest taxiway to the given coordinate."""
        if self.taxiways_gdf.empty:
            return None
        
        point_m = self._point_in_metric(lat, lon)
        min_dist = float("inf")
        nearest_feature = None
        
        for _, row in self.taxiways_gdf.iterrows():
            geom_m = transform(self.wgs84_to_metric, row.geometry)
            dist = geom_m.distance(point_m)
            if dist < min_dist:
                min_dist = dist
                nearest_feature = {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "distance_m": round(dist, 2)
                }
        return nearest_feature
