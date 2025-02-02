from datetime import datetime
from django.utils import timezone
from dateutil import parser
import json
import os
import difflib
import logging
from access_amherst_algo.models import Event
from django.db.models import Q
import pytz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random
import re

# Define location buckets with keywords as keys and dictionaries containing full names, latitude, and longitude as values
location_buckets = {
    "Keefe": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Queer": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Multicultural": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Friedmann": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528,
    },
    "Ford": {
        "name": "Ford Hall",
        "latitude": 42.36923506234738,
        "longitude": -72.51529130962976,
    },
    "SCCE": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447,
    },
    "Science Center": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447,
    },
    "Chapin": {
        "name": "Chapin Hall",
        "latitude": 42.371771820543486,
        "longitude": -72.51572746604714,
    },
    "Gym": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Cage": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Lefrak": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Middleton Gym": {
        "name": "Alumni Gym",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099,
    },
    "Frost": {
        "name": "Frost Library",
        "latitude": 42.37183195277655,
        "longitude": -72.51699336789369,
    },
    "Paino": {
        "name": "Beneski Museum of Natural History",
        "latitude": 42.37209277500926,
        "longitude": -72.51422459549485,
    },
    "Powerhouse": {
        "name": "Powerhouse",
        "latitude": 42.372109655195466,
        "longitude": -72.51309270030836,
    },
    "Converse": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
    "Assembly Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
    "Red Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017,
    },
}

# Define categories
CATEGORY_DESCRIPTIONS = {
    'Social': 'social gathering party meetup networking friendship community hangout celebration',
    'Group Business': 'business meeting organization planning committee board administrative professional',
    'Athletics': 'sports game match competition athletic fitness exercise tournament physical team',
    'Meeting': 'meeting discussion forum gathering assembly conference consultation',
    'Community Service': 'volunteer service community help charity outreach support donation drive',
    'Arts': 'art exhibition gallery creative visual performance theater theatre display',
    'Concert': 'music concert performance band orchestra choir singing musical live',
    'Arts and Craft': 'crafts making creating DIY hands-on artistic craft project workshop art supplies',
    'Workshop': 'workshop training seminar learning skills development hands-on practical education',
    'Cultural': 'cultural diversity international multicultural heritage tradition celebration ethnic',
    'Thoughtful Learning': 'lecture academic learning educational intellectual discussion research scholarly',
    'Spirituality': 'spiritual religious meditation faith worship prayer mindfulness wellness'
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("calendar_events_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_calendar_json(folder_path):
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
    >>> data = load_calendar_json("calendar_json_outputs")
    >>> if data:
    >>>     print(data)
    [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefe Campus Center"}]
    """
    try:
        json_files = [
            f for f in os.listdir(folder_path) if f.endswith(".json")
        ]
        if not json_files:
            logger.warning("No JSON files found in the specified directory")
            return None

        latest_file = sorted(json_files)[-1]
        file_path = os.path.join(folder_path, latest_file)
        logger.info(f"Loading JSON file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return None


def parse_calendar_datetime(date_str, pub_date=None):
    """
    Parse datetime strings and convert them to UTC.

    This function attempts to parse a given date string using ISO 8601 as the 
    primary format. If the parsed datetime lacks timezone information, it assumes 
    Eastern Time (ET) and converts it to UTC.

    Parameters
    ----------
    date_str : str
        The date or time string to be parsed.
    pub_date : str or datetime, optional
        A reference date used when parsing a time-only string.

    Returns
    -------
    datetime or None
        A timezone-aware datetime object converted to UTC or None if parsing fails.

    Examples
    --------
    >>> parse_calendar_datetime("2024-11-10T18:00:00")
    datetime.datetime(2024, 11, 10, 23, 0, tzinfo=<UTC>)

    >>> parse_calendar_datetime("18:00:00", "2024-11-10")
    datetime.datetime(2024, 11, 10, 23, 0, tzinfo=<UTC>)
    """
    if not date_str:
        return None

    try:
        dt = parser.parse(date_str)

        if dt.tzinfo is None:
            dt = pytz.timezone("America/New_York").localize(dt)
        
        return dt.astimezone(pytz.UTC)
    except parser.ParserError as e:
        logger.warning(f"Error parsing date string '{date_str}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing date '{date_str}': {e}")
        return None


def preprocess_title(title):
    """
    Preprocess an event title for better similarity comparison.

    This function converts the title to lowercase, removes special characters, 
    and trims extra whitespace to standardize event title formatting.

    Parameters
    ----------
    title : str
        The event title to preprocess.

    Returns
    -------
    str
        The cleaned and standardized event title.

    Examples
    --------
    >>> preprocess_title("  Guest Lecture: AI & Future  ")
    'guest lecture ai future'
    """
    if not isinstance(title, str):
        return ""
    # Convert to lowercase and remove special characters
    title = re.sub(r'[^\w\s]', '', title.lower())
    # Remove extra whitespace
    return " ".join(title.split())


def is_calendar_event_similar(event_data):
    """
    Check if a similar event exists using start time and title similarity.

    This function searches for existing events that have the same start time 
    and compares their titles using a TF-IDF similarity score. If a similar 
    event is found, it returns True.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details such as title and start time.

    Returns
    -------
    bool
        True if a similar event exists, otherwise False.

    Examples
    --------
    >>> event_data = {
    >>>     "title": "Guest Lecture: AI & Future",
    >>>     "start_time": "2024-11-10T18:00:00"
    >>> }
    >>> is_calendar_event_similar(event_data)
    False
    """
    try:
        # Get and validate new title
        new_title = event_data.get("title", "")
        if not new_title:
            logger.warning("Empty title provided")
            return False

        # Get start time only
        pub_date = parse_calendar_datetime(event_data.get("pub_date"))
        start_time = parse_calendar_datetime(event_data.get("start_time"), pub_date)

        if not start_time:
            logger.warning("No valid start time provided")
            return False

        # Query events with same start time only
        similar_events = list(Event.objects.filter(start_time=start_time))
        if not similar_events:
            return False

        # Preprocess all titles
        existing_titles = [preprocess_title(event.title) for event in similar_events]
        new_title_processed = preprocess_title(new_title)

        # Remove empty titles
        existing_titles = [title for title in existing_titles if title]
        if not existing_titles:
            return False

        # Create and configure TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            min_df=1,
            ngram_range=(1, 2),
            strip_accents='unicode',
            lowercase=True
        )

        # Calculate TF-IDF matrices
        try:
            all_titles = existing_titles + [new_title_processed]
            tfidf_matrix = vectorizer.fit_transform(all_titles)
        except ValueError as e:
            logger.error(f"Vectorizer error: {e}")
            return False

        # Calculate similarities
        new_vector = tfidf_matrix[-1:]
        existing_matrix = tfidf_matrix[:-1]
        similarities = cosine_similarity(new_vector, existing_matrix)[0]

        # Check similarity threshold
        SIMILARITY_THRESHOLD = 0.57
        if similarities.size > 0 and np.max(similarities) > SIMILARITY_THRESHOLD:
            similar_index = int(np.argmax(similarities))
            most_similar_event = similar_events[similar_index]
            logger.info(
                f"Similar event found: '{most_similar_event.title}' "
                f"(similarity: {similarities[similar_index]:.2f})"
            )
            return True

        return False

    except Exception as e:
        logger.error(f"Error in similarity check for '{event_data.get('title', 'Unknown')}': {e}")
        return False


def categorize_location(location):
    """
    Categorize a location based on predefined keyword mappings.

    This function searches the location string for known keywords and assigns 
    a corresponding category. If no match is found, it defaults to "Other."

    Parameters
    ----------
    location : str
        The location description to categorize.

    Returns
    -------
    str
        The mapped location category.

    Examples
    --------
    >>> categorize_location("Friedmann Room")
    'Keefe Campus Center'
    """
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            return info["name"]
    return "Other"


def get_lat_lng(location):
    """
    Retrieve the latitude and longitude for a given location.

    This function searches the `location` string for any keyword defined in the
    `location_buckets` dictionary. If a keyword is found, it returns the associated 
    latitude and longitude. If no keyword is matched, it returns `(None, None)`.

    Parameters
    ----------
    location : str
        The location description to search for latitude and longitude.

    Returns
    -------
    tuple
        A tuple containing:
        - `latitude` (float or None): The latitude of the location if a match is found, otherwise None.
        - `longitude` (float or None): The longitude of the location if a match is found, otherwise None.

    Examples
    --------
    >>> get_lat_lng("Friedmann Room")
    (42.37141504481807, -72.51479991450528)
    """
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            return info["latitude"], info["longitude"]
    return None, None


def add_random_offset(lat, lng):
    """
    Add a small random offset to latitude and longitude coordinates.

    This function applies a random offset within a small range to both the latitude
    and longitude values provided. The offset range can be adjusted as needed based
    on the map scale to create minor variations in coordinates, which is useful for
    visual distinction on maps.

    Parameters
    ----------
    lat : float
        The original latitude coordinate.
    lng : float
        The original longitude coordinate.

    Returns
    -------
    tuple
        A tuple containing:
        - `lat` (float): The latitude with a random offset applied.
        - `lng` (float): The longitude with a random offset applied.

    Examples
    --------
    >>> add_random_offset(42.37141504481807, -72.51479991450528)
    (42.37149564586236, -72.51478632450079)  # Results may vary due to randomness
    """
    offset_range = 0.00015
    lat += random.uniform(-offset_range, offset_range)
    lng += random.uniform(-offset_range, offset_range) 
    return lat, lng


def assign_categories(event_data):
    """
    Assign the best-matching category to an event based on textual similarity.

    This function compares event details against predefined category descriptions 
    using TF-IDF similarity scoring to determine the most relevant category.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details such as title, description, and host.

    Returns
    -------
    list
        A list containing a single best-matching category.

    Examples
    --------
    >>> event_data = {"title": "Literature Speaker Event", "event_description": "Join us in discussing our speaker's latest novel."}
    >>> assign_categories(event_data)
    ['Meeting']
    """
    try:
        # Combine relevant event fields into single text
        event_text = ' '.join(filter(None, [
            event_data.get('title', ''),
            event_data.get('event_description', ''),
            event_data.get('host', ''),
            event_data.get('location', '')
        ])).lower()

        if not event_text.strip():
            logger.warning("Empty event text, returning default category")
            return ['Other']

        # Prepare texts for comparison
        texts = [event_text] + list(CATEGORY_DESCRIPTIONS.values())
        
        # Calculate TF-IDF similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
            
            # Get category with highest similarity
            if len(similarities) > 0:
                best_match_idx = similarities.argmax()
                best_match_score = similarities[best_match_idx]
                
                if best_match_score > 0.02:  # Minimum similarity threshold
                    best_category = list(CATEGORY_DESCRIPTIONS.keys())[best_match_idx]
                    logger.info(f"Assigned category '{best_category}' with score {best_match_score:.3f}")
                    return [best_category]
            
            logger.info("No category met similarity threshold")
            return ['Other']
            
        except Exception as e:
            logger.error(f"Vectorizer error: {e}")
            return ['Other']
            
    except Exception as e:
        logger.error(f"Category assignment error: {e}")
        return ['Other']


# Modify save_calendar_event_to_db:
def save_calendar_event_to_db(event_data):
    """
    Save an event to the database with location and category validation.

    This function processes event details, assigns categories, generates a 
    unique event ID, and updates or creates a database entry.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details, including title, time, location, 
        and categories.

    Returns
    -------
    None
        This function does not return any value but logs success or failure messages.

    Examples
    --------
    >>> event_data = {
    >>>     "title": "Literature Speaker Event",
    >>>     "start_time": "2024-11-05T18:00:00",
    >>>     "end_time": "2024-11-05T20:00:00",
    >>>     "location": "Keefe Campus Center",
    >>>     "categories": ["Meeting"]
    >>> }
    >>> save_calendar_event_to_db(event_data)
    Successfully saved event: Literature Speaker Event with categories ['Meeting']
    """
    try:
        if not isinstance(event_data, dict):
            raise ValueError("Event data must be a dictionary")
            
        title = event_data.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Event must have a non-empty title string")

        event_id = str(700_000_000 + hash(str(title)) % 100_000_000)

        # Get coordinates
        location = event_data.get("location", "")
        map_location = categorize_location(location)
        lat, lng = get_lat_lng(location)
        if lat and lng:
            lat, lng = add_random_offset(lat, lng)

        pub_date = parse_calendar_datetime(event_data.get("pub_date")) or timezone.now()
        start_time = parse_calendar_datetime(event_data.get("start_time"), pub_date)
        end_time = parse_calendar_datetime(event_data.get("end_time"), pub_date)

        # Get categories using similarity
        try:
            auto_categories = assign_categories(event_data)
        except Exception as e:
            logger.error(f"Category assignment error: {e}")
            auto_categories = []

                # Ensure at least one category
        if not auto_categories:
            auto_categories = ["Other"]

        existing_categories = event_data.get("categories", [])
        all_categories = list(set(existing_categories + auto_categories))
        
        # Combine with any existing categories
        existing_categories = event_data.get("categories", [])
        all_categories = list(set(existing_categories + auto_categories))

        Event.objects.update_or_create(
            id=event_id,
            defaults={
                "title": event_data["title"],
                "author_name": event_data.get("author_name", ""),
                "pub_date": pub_date,
                "host": json.dumps(event_data.get("host", [])),
                "link": event_data.get("link", "https://www.amherst.edu"),
                "picture_link": event_data.get("picture_link", ""),
                "event_description": event_data.get("event_description", ""),
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "categories": json.dumps(all_categories),
                "latitude": lat,
                "longitude": lng,
                "map_location": map_location,
            },
        )
        logger.info(f"Successfully saved event: {event_data['title']} with categories {all_categories}")
        
    except Exception as e:
        logger.error(f"Error saving event '{event_data.get('title', 'Unknown')}': {e}")
        raise


def process_calendar_events():
    """
    Process and save calendar events extracted from JSON data.

    This function loads event data from a JSON file, checks for duplicate events, 
    and saves new events to the database.

    Returns
    -------
    None
        This function does not return any value but logs processing status messages.

    Examples
    --------
    >>> process_calendar_events()
    Skipping similar event: Literature Speaker Event
    Successfully saved/updated event: New Music Festival
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    json_folder = os.path.join(curr_dir, "calendar_json_outputs")

    events_data = load_calendar_json(json_folder)
    if not events_data:
        logger.warning("No events data to process")
        return

    for event in events_data:
        try:
            if not is_calendar_event_similar(event):
                save_calendar_event_to_db(event)
            else:
                logger.info(f"Skipping similar event: {event['title']}")
        except Exception as e:
            logger.error(
                f"Error processing event '{event.get('title', 'Unknown')}': {e}"
            )