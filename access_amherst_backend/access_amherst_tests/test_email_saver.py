import pytest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from django.utils import timezone
import json
import os
from access_amherst_algo.email_scraper.email_saver import (
    load_json_file,
    parse_datetime,
    is_similar_event,
    save_event_to_db,
    process_email_events,
)

# Sample test data
sample_event = {
    "title": "Test Event",
    "pub_date": "2024-11-07",
    "starttime": "09:00:00",
    "endtime": "10:00:00",
    "location": "Test Hall",
    "event_description": "Test description",
    "host": ["Test Host"],
    "link": "https://test.com",
    "picture_link": "https://test.com/image.jpg",
    "categories": ["Test Category"],
    "author_name": "Test Author",
    "author_email": "test@example.com",
}

# Sample list of events for testing
sample_events_list = [sample_event]


@pytest.fixture
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def mock_event_queryset():
    """Create a mock queryset that simulates Django's queryset behavior."""
    mock_event = MagicMock()
    mock_event.title = "Test Event"

    mock_qs = MagicMock()
    mock_qs.all.return_value = mock_qs
    mock_qs.filter.return_value = [
        mock_event
    ]  # Return list with our mock event

    return mock_qs


@pytest.fixture
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def mock_event_model(mock_event_queryset):
    """Create a mock Event model with proper queryset behavior."""
    with patch(
        "access_amherst_algo.email_scraper.email_saver.Event"
    ) as mock_event:
        mock_event.objects = mock_event_queryset
        yield mock_event

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_true(mock_event_model):
    """Test detection of similar events when one exists."""
    result = is_similar_event(sample_event)

    # Verify the queryset was filtered correctly
    mock_event_model.objects.filter.assert_called()

    # Verify we got True as the result
    assert result is True

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_false(mock_event_model, mock_event_queryset):
    """Test detection of similar events when none exist."""
    # Create a mock event with different title
    mock_event = MagicMock()
    mock_event.title = "Completely Different Event"
    mock_event_queryset.filter.return_value = [mock_event]

    result = is_similar_event(sample_event)
    assert result is False

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_no_times(mock_event_model, mock_event_queryset):
    """Test similar event detection with missing time data."""
    event_no_times = sample_event.copy()
    del event_no_times["starttime"]
    del event_no_times["endtime"]

    mock_event = MagicMock()
    mock_event.title = "Test Event"
    mock_event_queryset.all.return_value = [mock_event]

    result = is_similar_event(event_no_times)
    assert result is True

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_error(mock_event_model):
    """Test error handling in similar event detection."""
    mock_event_model.objects.all.side_effect = Exception("Database error")

    result = is_similar_event(sample_event)
    assert result is False

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_save_event_to_db(mock_event_model):
    """Test saving event to database."""
    save_event_to_db(sample_event)

    mock_event_model.objects.update_or_create.assert_called_once()
    call_args = mock_event_model.objects.update_or_create.call_args[1]

    assert "defaults" in call_args
    defaults = call_args["defaults"]
    assert defaults["title"] == sample_event["title"]
    assert defaults["location"] == sample_event["location"]
    assert json.loads(defaults["host"]) == sample_event["host"]
    assert json.loads(defaults["categories"]) == sample_event["categories"]


@patch("access_amherst_algo.email_scraper.email_saver.load_json_file")
@patch("access_amherst_algo.email_scraper.email_saver.is_similar_event")
@patch("access_amherst_algo.email_scraper.email_saver.save_event_to_db")
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_process_email_events_success(mock_save, mock_is_similar, mock_load):
    """Test successful processing of email events."""
    # Setup mocks
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False

    # Run the function
    process_email_events()

    # Verify calls
    mock_load.assert_called_once()
    mock_is_similar.assert_called_once_with(sample_event)
    mock_save.assert_called_once_with(sample_event)


@patch("access_amherst_algo.email_scraper.email_saver.load_json_file")
@patch("access_amherst_algo.email_scraper.email_saver.is_similar_event")
@patch("access_amherst_algo.email_scraper.email_saver.save_event_to_db")
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_process_email_events_error_handling(
    mock_save, mock_is_similar, mock_load
):
    """Test error handling during event processing."""
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False
    mock_save.side_effect = Exception("Test error")

    # This should not raise an exception
    process_email_events()

    mock_load.assert_called_once()
    mock_is_similar.assert_called_once()
    mock_save.assert_called_once()


@patch("access_amherst_algo.email_scraper.email_saver.load_json_file")
@patch("access_amherst_algo.email_scraper.email_saver.is_similar_event")
@patch("access_amherst_algo.email_scraper.email_saver.save_event_to_db")
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_process_email_events_error_handling(
    mock_save, mock_is_similar, mock_load
):
    """Test error handling during event processing."""
    mock_load.return_value = sample_events_list
    mock_is_similar.return_value = False
    mock_save.side_effect = Exception("Test error")

    # This should not raise an exception
    process_email_events()

    mock_load.assert_called_once()
    mock_is_similar.assert_called_once()
    mock_save.assert_called_once()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_parse_datetime_full_date():
    """Test parsing of a full date string."""
    result = parse_datetime("2024-11-07")
    assert result.date() == datetime(2024, 11, 7).date()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_parse_datetime_iso_format():
    """Test parsing of an ISO format datetime string."""
    result = parse_datetime("2024-11-07T09:00:00")
    assert result.date() == datetime(2024, 11, 7).date()
    assert result.time() == datetime.strptime("09:00:00", "%H:%M:%S").time()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_parse_datetime_rfc_format():
    """Test parsing of an RFC format datetime string."""
    result = parse_datetime("Thu, 07 Nov 2024 09:00:00 GMT")
    assert result.date() == datetime(2024, 11, 7).date()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_parse_datetime_time_only_with_pub_date():
    """Test parsing of time-only string with pub_date."""
    pub_date = "2024-11-07"
    result = parse_datetime("09:00:00", pub_date)
    assert result.date() == datetime(2024, 11, 7).date()
    assert result.time() == datetime.strptime("09:00:00", "%H:%M:%S").time()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_parse_datetime_time_only_without_pub_date():
    """Test parsing of time-only string without pub_date."""
    result = parse_datetime("09:00:00")
    assert result.date() == timezone.now().date()


@patch("os.listdir")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(sample_events_list),
)
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_load_json_file_success(mock_open_file, mock_listdir):
    """Test loading the latest JSON file successfully."""
    mock_listdir.return_value = ["events1.json", "events2.json"]
    result = load_json_file("some_folder")
    assert result == sample_events_list


@patch("os.listdir")
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_load_json_file_no_files(mock_listdir):
    """Test when no JSON files are present."""
    mock_listdir.return_value = []
    result = load_json_file("some_folder")
    assert result is None


@patch("os.listdir", side_effect=Exception("Filesystem error"))
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_load_json_file_error(mock_listdir):
    """Test handling of errors during JSON loading."""
    result = load_json_file("some_folder")
    assert result is None

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_save_event_to_db_missing_optional_fields(mock_event_model):
    """Test saving an event with missing optional fields."""
    event_data = sample_event.copy()
    del event_data["link"]
    del event_data["event_description"]

    save_event_to_db(event_data)
    mock_event_model.objects.update_or_create.assert_called_once()
    call_args = mock_event_model.objects.update_or_create.call_args[1]
    defaults = call_args["defaults"]

    assert defaults["link"] == "https://www.amherst.edu"
    assert defaults["event_description"] == ""


@patch("access_amherst_algo.email_scraper.email_saver.load_json_file")
@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_process_email_events_no_events(mock_load):
    """Test processing when no events are loaded."""
    mock_load.return_value = None
    process_email_events()
    mock_load.assert_called_once()

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_empty_db(mock_event_model):
    """Test similarity detection with an empty database."""
    mock_event_model.objects.all.return_value = []
    result = is_similar_event(sample_event)
    assert result is False

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_exact_match(mock_event_model, mock_event_queryset):
    """Test similarity detection with an exact match."""
    mock_event = MagicMock()
    mock_event.title = sample_event["title"]
    mock_event_queryset.filter.return_value = [mock_event]

    result = is_similar_event(sample_event)
    assert result is True

@pytest.mark.skip(reason="Migrating to Postgres will be tested in Render CI/CD")
def test_is_similar_event_low_similarity(
    mock_event_model, mock_event_queryset
):
    """Test similarity detection with low similarity."""
    mock_event = MagicMock()
    mock_event.title = "Completely Unrelated Event"
    mock_event_queryset.filter.return_value = [mock_event]

    result = is_similar_event(sample_event)
    assert result is False


if __name__ == "__main__":
    pytest.main()
