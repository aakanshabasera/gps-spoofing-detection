import os
import pytest
from geospatial.airport_map import AirportMap


@pytest.fixture
def airport_map():
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "reference", "del_airport.geojson")
    return AirportMap(geojson_path)


def test_is_inside_airport_boundary(airport_map):
    # Center of DEL airport
    assert airport_map.is_inside_airport_boundary(28.5562, 77.1000) is True
    # Way outside DEL airport (e.g. Mumbai)
    assert airport_map.is_inside_airport_boundary(19.0760, 72.8777) is False


def test_runway_distances(airport_map):
    # Point directly on Runway 09/27
    on_runway_lat, on_runway_lon = 28.5450, 77.1000
    dist = airport_map.distance_from_runway(on_runway_lat, on_runway_lon)
    assert dist < 10.0
    assert airport_map.is_on_valid_runway(on_runway_lat, on_runway_lon) is True


def test_nearest_runway(airport_map):
    nearest = airport_map.nearest_runway(28.5450, 77.1000)
    assert nearest is not None
    assert "Runway" in nearest["name"]
