import pytest
from django.utils import timezone
from access_amherst_algo.models import Event
from access_amherst_algo.parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
)
import pytz

@pytest.fixture
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def create_events():
    """Fixture to create sample events for testing."""
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
        pub_date=now,
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
        pub_date=now,
    )


@pytest.mark.django_db
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_filter_events(create_events):
    """Test filtering events by title, location, and date range."""
    # Test filtering by title
    events = filter_events(query="Event 1")
    assert events.count() == 1
    assert events.first().title == "Event 1"

    # Test filtering by location
    events = filter_events(locations=["Map Location 2"])
    assert events.count() == 1
    assert events.first().map_location == "Map Location 2"

    # Test filtering by date range
    timezone_est = pytz.timezone("America/New_York")
    start_date = timezone.now().astimezone(timezone_est).date()
    end_date = start_date + timezone.timedelta(days=1)
    events = filter_events(start_date=start_date, end_date=end_date)
    assert events.count() == 2  # Assuming both events fall within the range

@pytest.mark.django_db
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_get_unique_locations(create_events):
    """Test retrieving unique map locations."""
    unique_locations = get_unique_locations()
    assert len(unique_locations) == 2
    assert "Map Location 1" in unique_locations
    assert "Map Location 2" in unique_locations

@pytest.mark.django_db
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_get_events_by_hour(create_events):
    """Test grouping events by hour."""
    timezone_est = pytz.timezone("America/New_York")
    events_by_hour = get_events_by_hour(Event.objects.all(), timezone_est)
    assert len(events_by_hour) > 0
    for event in events_by_hour:
        assert "hour" in event
        assert "event_count" in event

@pytest.mark.django_db
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_get_category_data(create_events):
    """Test parsing category data and grouping by hour."""
    timezone_est = pytz.timezone("America/New_York")
    category_data = get_category_data(Event.objects.all(), timezone_est)
    assert len(category_data) > 0
    assert all("category" in data and "hour" in data for data in category_data)
