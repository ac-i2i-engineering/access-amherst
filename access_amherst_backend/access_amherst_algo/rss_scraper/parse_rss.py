import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta
from access_amherst_algo.models import Event  # Import the Event model
from bs4 import BeautifulSoup
import random
import re
import os
from dotenv import load_dotenv
from django.db.models import Q
import difflib
from dateutil import parser
import pytz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

load_dotenv()


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

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for detailed logs in a dev environment
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the console
    ],
)
logger = logging.getLogger(__name__)

# Update categorize_location to use new dictionary structure
def categorize_location(location):
    """
    Categorize a location based on keywords in the `location_buckets` dictionary.

    This function searches the `location` string for any keyword defined in the
    `location_buckets` dictionary. If a keyword is found, it returns the associated 
    category name from the dictionary. If no keyword is matched, it returns "Other" 
    as the default category.

    Parameters
    ----------
    location : str
        The location description to categorize.

    Returns
    -------
    str
        The category name if a keyword is matched, otherwise "Other".

    Examples
    --------
    >>> categorize_location("Friedmann Room")
    'Keefe Campus Center'
    """
    logging.info("Categorizing location...")
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            logging.info("Location found.")
            return info["name"]
    logging.info("No location found.")
    return "Other"  # Default category if no match is found


# Function to extract the details of an event from an XML item
def extract_event_details(item):
    """
    Extract relevant event details from an XML item element.

    This function takes an XML item element and parses various fields such as
    title, link, description, categories, and other event metadata.
    It also handles optional fields like images and author.

    Parameters
    ----------
    item : xml.etree.ElementTree.Element
        The XML item element containing event details.

    Returns
    -------
    dict
        A dictionary containing event details with the following keys:
        - `title` (str): The event title.
        - `author` (str or None): The event author, if available.
        - `pub_date` (str): Publication date of the event.
        - `host` (list of str): A list of host names associated with the event.
        - `link` (str): URL link to the event.
        - `picture_link` (str or None): URL to the event image, if available.
        - `event_description` (str): Parsed HTML content of the event description.
        - `starttime` (str): Event start time.
        - `endtime` (str): Event end time.
        - `location` (str): The event location as specified in the XML.
        - `categories` (list of str): Categories or tags associated with the event.
        - `map_location` (str): Categorized location name for mapping purposes.

    Examples
    --------
    >>> event_data = extract_event_details(xml_item)
    >>> print(event_data['title'])
    'Literature Speaker Event'
    """

    logging.info("Extracting event info.")
    ns = "{events}"

    # Extract primary fields from XML
    title = item.find("title").text
    link = item.find("link").text

    # Get image link if available
    enclosure = item.find("enclosure")
    picture_link = enclosure.attrib["url"] if enclosure is not None else None

    # Parse event description HTML if available
    description = item.find("description").text
    event_description = ""
    if description:
        logging.info("Event description found. Parsing...")
        soup = BeautifulSoup(description, "html.parser")
        description_div = soup.find("div", class_="p-description description")
        event_description = "".join(
            str(content) for content in description_div.contents
        )
        logging.info("Event description parsing completed.")

    # Gather categories and other event metadata
    categories = [format_category(category.text) for category in item.findall("category")]
    pub_date = item.find("pubDate").text
    start_time = item.find(ns + "start").text
    end_time = item.find(ns + "end").text
    location = item.find(ns + "location").text
    author = (
        item.find("author").text if item.find("author") is not None else None
    )
    host = [host.text for host in item.findall(ns + "host")]

    # Categorize the location for mapping purposes
    map_location = categorize_location(location)

    return {
        "title": title,
        "author": author,
        "pub_date": pub_date,
        "host": host,
        "link": link,
        "picture_link": picture_link,
        "event_description": event_description,
        "starttime": start_time,
        "endtime": end_time,
        "location": location,
        "categories": categories,
        "map_location": map_location,
    }


def format_category(category_text):
    # Split on capital letters and lowercase sequences
    words = ''.join(' ' + c if c.isupper() else c for c in category_text).strip()
    # Handle cases where words are all lowercase without spaces
    if ' ' not in words:
        words = category_text.replace('and', ' and ')
    # Capitalize first letter of each word    
    return ' '.join(word.capitalize() for word in words.split())


# Use hardcoded lat/lng for each location bucket
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
    logging.info("Finding location lat/lng...")
    for keyword, info in location_buckets.items():
        if re.search(rf"\b{keyword}\b", location, re.IGNORECASE):
            logging.info("Location lat/lng found")
            return info["latitude"], info["longitude"]
    logging.info("Location lat/lng not found; None/None returned")
    return None, None


# Function to add a slight random offset to latitude and longitude
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
    # Define a small range for random offsets (in degrees)
    offset_range = 0.00015  # Adjust this value as needed for your map scale
    lat += random.uniform(-offset_range, offset_range)
    lng += random.uniform(-offset_range, offset_range)
    logging.info("Offset added to location.")
    return lat, lng


# Function to save the event to the Django model
def save_event_to_db(event_data):
    """
    Save event data to the Django model.

    This function processes event data for database storage by parsing publication,
    start, and end dates into timezone-aware datetime objects, extracting and
    adjusting location data, and generating a unique event ID. The function then
    updates or creates an entry in the database's `Event` table.

    Parameters
    ----------
    event_data : dict
        A dictionary containing event details

    Returns
    -------
    None

    Examples
    --------
    >>> event_data = {
    ...     "title": "Literature Speaker Event",
    ...     "link": "https://thehub.amherst.edu/event/10000000",
    ...     "event_description": "Join us to hear our speaker's talk on American Literature! Food from a local restaurant will be provided.",
    ...     "categories": ["Lecture", "Workshop"],
    ...     "pub_date": "Sun, 03 Nov 2024 05:30:25 GMT",
    ...     "starttime": "Tue, 05 Nov 2024 18:00:00 GMT",
    ...     "endtime": "Tue, 05 Nov 2024 19:00:00 GMT",
    ...     "location": "Friedmann Room",
    ...     "author": "literature@amherst.edu",
    ...     "host": "Literature Club",
    ... }
    >>> save_event_to_db(event_data)
    """

    # Parse dates and times
    pub_date = parser.parse(event_data["pub_date"])
    start_time = parser.parse(event_data["starttime"])
    end_time = parser.parse(event_data["endtime"])
    
    # Check if the dates are in UTC, if not, convert them to UTC
    # NOTE: It best practice to store all dates in UTC in the database
    
    if pub_date.tzinfo is None or pub_date.tzinfo.utcoffset(pub_date) != pytz.UTC.utcoffset(pub_date):
        pub_date = pub_date.astimezone(pytz.UTC)

    if start_time.tzinfo is None or start_time.tzinfo.utcoffset(start_time) != pytz.UTC.utcoffset(start_time):
        start_time = start_time.astimezone(pytz.UTC)

    if end_time.tzinfo is None or end_time.tzinfo.utcoffset(end_time) != pytz.UTC.utcoffset(end_time):
        end_time = end_time.astimezone(pytz.UTC)
    logging.info("Converted date/time to UTC.")

    # get map location
    event_data["map_location"] = categorize_location(event_data["location"])

    # Geocode to get latitude and longitude using hardcoded values
    lat, lng = get_lat_lng(event_data["map_location"])

    # Add random offset to coordinates if lat/lng are available
    if lat is not None and lng is not None:
        lat, lng = add_random_offset(lat, lng)

    # Save or update event in the database
    Event.objects.update_or_create(
        id=str(event_data["id"]),
        defaults={
            "id": event_data["id"],
            "title": event_data["title"],
            "author_name": event_data["author_name"],
            "author_email": event_data["author_email"],
            "pub_date": pub_date,
            "host": json.dumps(event_data["host"]),
            "link": event_data["link"],
            "picture_link": event_data["picture_link"],
            "event_description": event_data["event_description"],
            "start_time": start_time,
            "end_time": end_time,
            "location": event_data["location"],
            "categories": json.dumps(event_data["categories"]),
            "latitude": lat if lat is not None else None,
            "longitude": lng if lng is not None else None,
            "map_location": event_data["map_location"],
        },
    )


# Function to create a list of events from an RSS XML file
def create_events_list():
    """
    Create a list of event details from an RSS XML file.

    This function loads an RSS XML file with a timestamped filename format,
    parses its content, and extracts event details from each `<item>` element.
    The event details are returned as a list of dictionaries, with each dictionary
    containing relevant information for a single event.

    Returns
    -------
    list of dict
        A list where each dictionary represents an event and contains extracted
        details retrieved by `extract_event_details`.

    Examples
    --------
    >>> events = create_events_list()
    >>> print(events[0]["title"])
    'Literature Speaker Event'
    """
    logging.info("Creating events list from rss file...")
    rss_file_name = (
        "access_amherst_algo/rss_scraper/rss_files/hub_"
        + datetime.now().strftime("%Y_%m_%d_%H")
        + ".xml"
    )
    root = ET.parse(rss_file_name).getroot()
    logging.info("Rss file sucessfully parsed.")

    events_list = [
        extract_event_details(item) for item in root.findall(".//item")
    ]
    logging.info("Event list created.")
    return events_list


# Function to save extracted events to a JSON file
def save_json():
    """
    Save the list of extracted events to a JSON file.

    This function generates a timestamped JSON file containing event details.
    It first creates a list of events by calling `create_events_list()`, and
    then writes this list to a JSON file with a filename format based on the
    current date and time.

    The resulting JSON file is saved in the `json_outputs` directory under the
    `rss_scraper` folder.

    Returns
    -------
    None

    Examples
    --------
    >>> save_json()
    """
    # Generate the events list
    events_list = create_events_list()

    # Define the directory and output file name
    directory = "access_amherst_algo/rss_scraper/json_outputs"
    os.makedirs(
        directory, exist_ok=True
    )  # Create the directory if it doesn't exist
    output_file_name = directory + "/hub_" + datetime.now().strftime("%Y_%m_%d_%H") + ".json"

    # Save the events list to a JSON file
    with open(output_file_name, "w") as f:
        json.dump(events_list, f, indent=4)


def preprocess_title(title):
    """Preprocess title for comparison"""
    if not isinstance(title, str):
        logging.warning("Title provided is not a string.")
        return ""
    # Convert to lowercase and remove special characters
    title = re.sub(r'[^\w\s]', '', title.lower())
    # Remove extra whitespace
    return " ".join(title.split())


def is_similar_event(event_data):
    """
    Check if a similar event exists using start time and title similarity.
    """
    try:
        # Validate title
        new_title = event_data.get("title", "")
        if not new_title:
            logger.warning("Empty title provided")
            return False

        # Parse and validate start time only
        start_time = parser.parse(event_data["starttime"])
        
        # Convert to UTC if needed
        if start_time.tzinfo is None or start_time.tzinfo.utcoffset(start_time) != pytz.UTC.utcoffset(start_time):
            start_time = start_time.astimezone(pytz.UTC)

        # Query events with same start time only
        similar_events = list(Event.objects.filter(start_time=start_time))
        
        if not similar_events:
            return False

        # Preprocess titles
        existing_titles = [preprocess_title(event.title) for event in similar_events]
        new_title_processed = preprocess_title(new_title)

        # Remove empty titles
        existing_titles = [title for title in existing_titles if title]
        if not existing_titles:
            return False

        # Configure vectorizer
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
        SIMILARITY_THRESHOLD = 0.4
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


# Function to clean and save events to the database
def save_to_db():
    """
    Clean and save event data to the database.

    This function first retrieves a cleaned list of events by calling the 
    `clean_hub_data()` function. It then iterates through each event in the 
    list and saves the event data to the database using the `save_event_to_db()` 
    function.

    This process ensures that only cleaned event data is stored in the database.

    Returns
    -------
    None

    Examples
    --------
    >>> save_to_db()
    """
    from access_amherst_algo.rss_scraper.clean_hub_data import clean_hub_data

    events_list = (
        clean_hub_data()
    )  # Get the cleaned list of events to be saved

    for event in events_list:
        # Check if a similar event already exists. Cases:
        # (if hub event, collision detection handled by update_or_create so always call save_event_to_db)
        # (if not hub event, and not similar to something in DB, then only call save_event_to_db)
        if int(event["id"]) > 500_000_000 or not is_similar_event(event):
            # If no similar event is found, save the event
            save_event_to_db(event)
