from datetime import datetime, timedelta
from django.utils import timezone
import json
import os
import difflib
from access_amherst_algo.models import Event
from django.db.models import Q
import pytz


def load_json_file(folder_path):
    """
    Load the most recent JSON file from the specified folder.

    This function scans the given directory for JSON files, identifies the most 
    recently modified JSON file, and loads its contents. If no JSON files are found, 
    it returns None.

    Parameters
    ----------
    folder_path : str
        The directory path where JSON files are stored.

    Returns
    -------
    dict or list or None
        The parsed JSON data if a file is found, otherwise None.

    Examples
    --------
    >>> data = load_json_file("json_outputs")
    >>> if data:
    >>>     print(data)
    [{'title': 'Literature Speaker Event', 'date': '2024-11-05', 'location': 'Keefe Campus Center'}]
    """
    try:
        json_files = [
            f for f in os.listdir(folder_path) if f.endswith(".json")
        ]
        if not json_files:
            print("No JSON files found in the specified directory")
            return None

        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(folder_path, latest_file)

        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None


def parse_datetime(date_str, pub_date=None):
    """
    Parse datetime strings and convert them to UTC with an EST (UTC-5) offset.

    This function attempts to parse a given date string using multiple formats, including 
    standard date, ISO 8601, and RFC formats. If only a time is provided, it combines 
    it with `pub_date` (if available) to create a full datetime object. The resulting 
    datetime is then converted to UTC.

    Parameters
    ----------
    date_str : str
        The date or time string to be parsed.
    pub_date : str or datetime, optional
        A reference date to be used when parsing a time-only string.

    Returns
    -------
    datetime or None
        A timezone-aware datetime object converted to UTC or None if parsing fails.

    Examples
    --------
    >>> parse_datetime("2024-11-05T18:00:00")
    datetime.datetime(2024, 11, 5, 13, 0, tzinfo=<UTC>)

    >>> parse_datetime("18:00:00", "2024-11-05")
    datetime.datetime(2024, 11, 5, 13, 0, tzinfo=<UTC>)
    """
    if not date_str:
        return None

    try:
        # First try parsing as full datetime
        formats = [
            "%Y-%m-%d",  # YYYY-MM-DD
            "%Y-%m-%dT%H:%M:%S",  # ISO format
            "%a, %d %b %Y %H:%M:%S %Z",  # RFC format
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Apply 5-hour offset for EST conversion
                dt = dt - timedelta(hours=5)
                return pytz.utc.localize(dt)
            except ValueError:
                continue

        # If that fails, try parsing as time only
        try:
            time = datetime.strptime(date_str, "%H:%M:%S").time()

            if pub_date:
                if isinstance(pub_date, str):
                    pub_date = parse_datetime(pub_date)

                if pub_date:
                    dt = datetime.combine(pub_date.date(), time)
                    # Apply 5-hour offset for EST conversion
                    dt = dt - timedelta(hours=5)
                    return pytz.utc.localize(dt)

            dt = datetime.combine(timezone.now().date(), time)
            # Apply 5-hour offset for EST conversion
            dt = dt - timedelta(hours=5)
            return pytz.utc.localize(dt)

        except ValueError:
            raise ValueError(f"Unable to parse date string: {date_str}")

    except Exception as e:
        print(f"Error parsing date: {e}")
        return None


def is_similar_event(event_data):
    """
    Check if a similar event exists using timezone-aware datetime comparison.

    This function compares the event's start and end times with existing database 
    records to determine if a similar event already exists. It also checks for 
    title similarity using a string similarity ratio.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details such as title, start time, and end time.

    Returns
    -------
    bool
        True if a similar event exists, otherwise False.

    Examples
    --------
    >>> event_data = {
    >>>     "title": "Literature Speaker Event",
    >>>     "starttime": "2024-11-05T18:00:00",
    >>>     "endtime": "2024-11-05T20:00:00",
    >>> }
    >>> is_similar_event(event_data)
    False
    """
    try:
        # Try to parse the times, using pub_date as reference for time-only formats
        pub_date = parse_datetime(event_data.get("pub_date"))
        start_time = parse_datetime(event_data.get("starttime"), pub_date)
        end_time = parse_datetime(event_data.get("endtime"), pub_date)

        # Build query dynamically based on available times
        query = Q()
        if start_time is not None:
            query &= Q(start_time=start_time)
        if end_time is not None:
            query &= Q(end_time=end_time)

        # Get similar events
        similar_events = Event.objects.all()
        if query:
            similar_events = similar_events.filter(query)

        # Check title similarity for matching events
        for event in similar_events:
            title_similarity = difflib.SequenceMatcher(
                None, 
                event_data.get("title", "").lower(),
                event.title.lower()
            ).ratio()
            if title_similarity > 0.8:
                return True

        return False

    except Exception as e:
        print(f"Error checking for similar events: {e}")
        return False


def save_event_to_db(event_data):
    """
    Save an event to the database, allowing nullable start and end times.

    This function processes event data by generating a unique ID, parsing 
    date fields, and saving or updating the event in the database.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details, including title, start and end times, 
        location, categories, and other metadata.

    Returns
    -------
    None
        This function does not return any value but prints a success or failure message.

    Examples
    --------
    >>> event_data = {
    >>>     "title": "Literature Speaker Event",
    >>>     "starttime": "2024-11-05T18:00:00",
    >>>     "endtime": "2024-11-05T20:00:00",
    >>>     "location": "Keefe Campus Center",
    >>>     "categories": ["Lecture", "Workshop"]
    >>> }
    >>> save_event_to_db(event_data)
    Successfully saved/updated event: Literature Speaker Event
    """
    try:
        # Generate a unique ID for email-sourced events
        event_id = str(
            600_000_000 + hash(str(event_data["title"])) % 100_000_000
        )

        # Parse dates
        pub_date = parse_datetime(event_data.get("pub_date")) or timezone.now()
        start_time = parse_datetime(event_data.get("starttime"), pub_date)
        end_time = parse_datetime(event_data.get("endtime"), pub_date)

        # Ensure 'link' and 'event_description' have default values
        link = event_data.get("link", "https://www.amherst.edu")
        description = event_data.get("event_description", "")

        # Update or create the event
        Event.objects.update_or_create(
            id=event_id,
            defaults={
                "title": event_data["title"],
                "author_name": event_data.get("author_name", ""),
                "pub_date": pub_date,
                "host": json.dumps(event_data.get("host", [])),
                "link": link,
                "picture_link": event_data.get("picture_link", ""),
                "event_description": description,
                "start_time": start_time,
                "end_time": end_time,
                "location": event_data.get("location", "TBD"),
                "categories": json.dumps(event_data.get("categories", [])),
                "latitude": None,
                "longitude": None,
                "map_location": "Other",
            },
        )
        print(f"Successfully saved/updated event: {event_data['title']}")
    except Exception as e:
        print(f"Error saving event to database: {e}")
        raise


# Process each event with updated logging
def process_email_events():
    """
    Process and save events extracted from email JSON data.

    This function loads the most recent JSON file containing extracted email event data, 
    checks for duplicate events, and saves new events to the database.

    Returns
    -------
    None
        This function does not return any value but prints processing status messages.

    Examples
    --------
    >>> process_email_events()
    Skipping similar event: Literature Speaker Event
    Successfully saved/updated event: New Music Festival
    """
    # Get the current directory
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(curr_dir, "json_outputs")

    # Load the JSON data
    events_data = load_json_file(json_folder)
    if not events_data:
        print("No events data to process")
        return

    # Process each event
    for event in events_data:
        try:
            if not is_similar_event(event):
                save_event_to_db(event)
            else:
                print(f"Skipping similar event: {event['title']}")
        except Exception as e:
            print(
                f"Error processing event '{event.get('title', 'Unknown')}': {e}"
            )