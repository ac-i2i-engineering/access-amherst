import pytest
from access_amherst_algo.models import Event
from access_amherst_algo.generate_map import (
    create_map,
    add_event_markers,
    generate_heatmap,
)
from django.utils import timezone
import folium
from folium.plugins import HeatMap
import pytz


@pytest.fixture
def create_events():
    """Fixture to create sample events for testing map generation."""
    now = timezone.now()
    Event.objects.create(
        title="Event 1",
        start_time=now,
        end_time=now + timezone.timedelta(hours=1),
        location="Location 1",
        map_location="Map Location 1",
        latitude=42.373611,
        longitude=-72.519444,
        event_description="Description 1",
        categories='["Category1"]',
        pub_date=now,  # Ensure pub_date is set
    )
    Event.objects.create(
        title="Event 2",
        start_time=now,
        end_time=now + timezone.timedelta(hours=2),
        location="Location 2",
        map_location="Map Location 2",
        latitude=42.374611,
        longitude=-72.518444,
        event_description="Description 2",
        categories='["Category2"]',
        pub_date=now,  # Ensure pub_date is set
    )


@pytest.mark.django_db
def test_create_map():
    """Test initializing a map centered on specific coordinates."""
    center_coords = [42.37031303771378, -72.51605520950432]
    folium_map = create_map(center_coords, zoom_start=18)
    assert isinstance(folium_map, folium.Map)
    assert folium_map.location == center_coords
    assert folium_map.options["zoom"] == 18


@pytest.mark.django_db
def test_add_event_markers(create_events):
    """Test adding markers for events on a map."""
    folium_map = create_map([42.37031303771378, -72.51605520950432])
    add_event_markers(folium_map, Event.objects.all())

    # Ensure markers were added by counting children of map object
    marker_count = sum(
        1
        for _ in folium_map._children
        if isinstance(folium_map._children[_], folium.map.Marker)
    )
    assert marker_count == 2


@pytest.mark.django_db
def test_generate_heatmap(create_events):
    """Test generating a heatmap layer on the map."""
    est = pytz.timezone("America/New_York")
    folium_map = generate_heatmap(Event.objects.all(), est)

    # Check if the map object contains a HeatMap layer
    heatmap_layer = any(
        isinstance(child, HeatMap) for child in folium_map._children.values()
    )
    assert heatmap_layer, "HeatMap layer was not added to the map"
