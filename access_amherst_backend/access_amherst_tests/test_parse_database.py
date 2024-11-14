import pytest
from django.utils import timezone
from django.db.models import QuerySet
from access_amherst_algo.models import Event
from access_amherst_algo.parse_database import (
    filter_events,
    get_unique_locations,
    get_events_by_hour,
    get_category_data,
    filter_events_by_category, 
    get_unique_categories, 
    clean_category
)
import pytz


@pytest.fixture
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


@pytest.fixture
def event_factory(db):
    """
    Factory fixture for creating Event instances.

    Parameters
    ----------
    db : pytest fixture
        Ensures access to the database during tests.

    Returns
    -------
    callable
        A function to create `Event` instances with customizable attributes.
    """
    def create_event(**kwargs):
        return Event.objects.create(
            title=kwargs.get("title", "Test Event"),
            start_time=kwargs.get("start_time", None),
            end_time=kwargs.get("end_time", None),
            location=kwargs.get("location", "Test Location"),
            categories=kwargs.get("categories", ""),
            picture_link=kwargs.get("picture_link", None),
            link=kwargs.get("link", None),
        )
    return create_event


@pytest.mark.django_db
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
    start_date = timezone.now().date()
    end_date = start_date + timezone.timedelta(days=1)
    events = filter_events(start_date=start_date, end_date=end_date)
    assert events.count() == 2  # Assuming both events fall within the range


@pytest.mark.django_db
def test_get_unique_locations(create_events):
    """Test retrieving unique map locations."""
    unique_locations = get_unique_locations()
    assert len(unique_locations) == 2
    assert "Map Location 1" in unique_locations
    assert "Map Location 2" in unique_locations


@pytest.mark.django_db
def test_get_events_by_hour(create_events):
    """Test grouping events by hour."""
    events_by_hour = get_events_by_hour(Event.objects.all())
    assert len(events_by_hour) > 0
    for event in events_by_hour:
        assert "hour" in event
        assert "event_count" in event


@pytest.mark.django_db
def test_get_category_data(create_events):
    """Test parsing category data and grouping by hour."""
    category_data = get_category_data(Event.objects.all())
    assert len(category_data) > 0
    assert all("category" in data and "hour" in data for data in category_data)


@pytest.mark.django_db
def test_filter_events_by_category(event_factory):
    # Arrange: Create events with different categories
    event_factory(title="Event 1", categories="Music, Sports")
    event_factory(title="Event 2", categories="Music")
    event_factory(title="Event 3", categories="Sports")
    event_factory(title="Event 4", categories="Art")

    # Act: Retrieve all events and filter by specific categories
    all_events = Event.objects.all()
    filtered_events = filter_events_by_category(all_events, ["Music", "Art"])

    # Assert: Ensure the filtered events match the categories
    assert isinstance(filtered_events, QuerySet), "The result should be a QuerySet."
    assert filtered_events.count() == 3, "Three events should match the categories."
    titles = [event.title for event in filtered_events]
    assert "Event 1" in titles
    assert "Event 2" in titles
    assert "Event 4" in titles
    assert "Event 3" not in titles, "Event 3 should not be included."


@pytest.mark.django_db
def test_get_unique_categories(event_factory):
    """
    Test the get_unique_categories function.
    """
    # Create test events with categories
    event_factory(categories="Workshop, Lecture")
    event_factory(categories="Seminar")
    event_factory(categories="Workshop, Networking")
    
    # Get unique categories
    unique_categories = get_unique_categories()
    assert isinstance(unique_categories, list)
    assert len(unique_categories) == 4  # ["Workshop", "Lecture", "Seminar", "Networking"]
    assert set(unique_categories) == {"Workshop", "Lecture", "Seminar", "Networking"}


def test_clean_category():
    """
    Test the clean_category function.
    """
    # Test various category strings
    assert clean_category(" Workshop ") == "Workshop"
    assert clean_category("!!!Lecture!!!") == "Lecture"
    assert clean_category("(Seminar)") == "Seminar"
    assert clean_category("Conference-123") == "Conference-123"
    assert clean_category("!@#Special_Event$%") == "Special_Event"
    assert clean_category("") == ""  # Edge case: Empty string
    assert clean_category("   ") == ""  # Edge case: Whitespace only