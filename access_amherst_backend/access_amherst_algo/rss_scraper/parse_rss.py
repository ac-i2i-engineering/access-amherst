import xml.etree.ElementTree as ET
import json
from datetime import datetime
from access_amherst_algo.models import Event  # Import the Event model
from bs4 import BeautifulSoup
import random
import re
import os
from dotenv import load_dotenv
from django.utils import timezone
from opencage.geocoder import OpenCageGeocode

load_dotenv()

# Define location buckets with keywords as keys and dictionaries
# containing full names, latitude, and longitude as values
location_buckets = {
    "Keefe": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528},
    "Queer": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528},
    "Multicultural": {
        "name": "Keefe Campus Center",
                "latitude": 42.37141504481807,
                "longitude": -72.51479991450528},
    "Friedmann": {
        "name": "Keefe Campus Center",
        "latitude": 42.37141504481807,
        "longitude": -72.51479991450528},
    "Ford": {
        "name": "Ford Hall",
        "latitude": 42.36923506234738,
        "longitude": -72.51529130962976},
    "SCCE": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447},
    "Science Center": {
        "name": "Science Center",
        "latitude": 42.37105378715133,
        "longitude": -72.51334790776447},
    "Chapin": {
        "name": "Chapin Hall",
        "latitude": 42.371771820543486,
        "longitude": -72.51572746604714},
    "Gym": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099},
    "Cage": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099},
    "Lefrak": {
        "name": "Alumni Gymnasium",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099},
    "Middleton Gym": {
        "name": "Alumni Gym",
        "latitude": 42.368819594097864,
        "longitude": -72.5188658145099},
    "Frost": {
        "name": "Frost Library",
        "latitude": 42.37183195277655,
        "longitude": -72.51699336789369},
    "Paino": {
        "name": "Beneski Museum of Natural History",
        "latitude": 42.37209277500926,
        "longitude": -72.51422459549485},
    "Powerhouse": {
        "name": "Powerhouse",
        "latitude": 42.372109655195466,
        "longitude": -72.51309270030836},
    "Converse": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017},
    "Assembly Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017},
    "Red Room": {
        "name": "Converse Hall",
        "latitude": 42.37243680844771,
        "longitude": -72.518433147017},
}

# Update categorize_location to use new dictionary structure


def categorize_location(location):
    for keyword, info in location_buckets.items():
        if re.search(rf'\b{keyword}\b', location, re.IGNORECASE):
            return info["name"]
    return "Other"  # Default category if no match is found

# Function to extract the details of an event from an XML item


def extract_event_details(item):
    ns = '{events}'

    # Extract primary fields from XML
    title = item.find('title').text
    link = item.find('link').text

    # Get image link if available
    enclosure = item.find('enclosure')
    picture_link = enclosure.attrib['url'] if enclosure is not None else None

    # Parse event description HTML if available
    description = item.find('description').text
    event_description = ""
    if description:
        soup = BeautifulSoup(description, 'html.parser')
        description_div = soup.find('div', class_='p-description description')
        event_description = ''.join(str(content)
                                    for content in description_div.contents)

    # Gather categories and other event metadata
    categories = [category.text for category in item.findall('category')]
    pub_date = item.find('pubDate').text
    start_time = item.find(ns + 'start').text
    end_time = item.find(ns + 'end').text
    location = item.find(ns + 'location').text
    author = item.find('author').text if item.find('author') else None
    host = [host.text for host in item.findall(ns + 'host')]

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
        "map_location": map_location
    }

# Use hardcoded lat/lng for each location bucket


def get_lat_lng(location):
    for keyword, info in location_buckets.items():
        if re.search(rf'\b{keyword}\b', location, re.IGNORECASE):
            return info["latitude"], info["longitude"]
    return None, None

# Function to add a slight random offset to latitude and longitude


def add_random_offset(lat, lng):
    # Define a small range for random offsets (in degrees)
    offset_range = 0.00015  # Adjust this value as needed for your map scale
    lat += random.uniform(-offset_range, offset_range)
    lng += random.uniform(-offset_range, offset_range)
    return lat, lng

# Function to save the event to the Django model


def save_event_to_db(event_data):
    pub_date_format = '%a, %d %b %Y %H:%M:%S %Z'
    pub_date = timezone.make_aware(
        datetime.strptime(
            event_data['pub_date'],
            pub_date_format))

    # Parse start and end times with multiple format handling
    try:
        iso_format = '%Y-%m-%dT%H:%M:%S'
        start_time = datetime.strptime(event_data['starttime'], iso_format)
        end_time = datetime.strptime(event_data['endtime'], iso_format)
    except ValueError:
        rfc_format = '%a, %d %b %Y %H:%M:%S %Z'
        start_time = datetime.strptime(event_data['starttime'], rfc_format)
        end_time = datetime.strptime(event_data['endtime'], rfc_format)

    start_time, end_time = timezone.make_aware(
        start_time), timezone.make_aware(end_time)

    # get map location
    event_data['map_location'] = categorize_location(event_data['location'])

    # Generate unique event ID
    id = int(re.search(r'/(\d+)$', event_data['link']).group(1)) + 500_000_000

    # Geocode to get latitude and longitude using hardcoded values
    lat, lng = get_lat_lng(event_data['map_location'])

    # Add random offset to coordinates if lat/lng are available
    if lat is not None and lng is not None:
        lat, lng = add_random_offset(lat, lng)

    # Save or update event in the database
    Event.objects.update_or_create(
        id=str(id),
        defaults={
            "id": id,
            "title": event_data['title'],
            "author_name": event_data['author'],
            "pub_date": pub_date,
            "host": json.dumps(event_data['host']),
            "link": event_data['link'],
            "picture_link": event_data['picture_link'],
            "event_description": event_data['event_description'],
            "start_time": start_time,
            "end_time": end_time,
            "location": event_data['location'],
            "categories": json.dumps(event_data['categories']),
            "latitude": lat if lat is not None else None,
            "longitude": lng if lng is not None else None,
            "map_location": event_data['map_location']
        }
    )

# Function to create a list of events from an RSS XML file


def create_events_list():
    rss_file_name = 'access_amherst_algo/rss_scraper/rss_files/hub_' + \
        datetime.now().strftime('%Y_%m_%d_%H') + '.xml'
    root = ET.parse(rss_file_name).getroot()

    events_list = [extract_event_details(item)
                   for item in root.findall('.//item')]
    return events_list

# Function to save extracted events to a JSON file


def save_json():
    events_list = create_events_list()
    output_file_name = 'access_amherst_algo/rss_scraper/json_outputs/hub_' + \
        datetime.now().strftime('%Y_%m_%d_%H') + '.json'
    with open(output_file_name, 'w') as f:
        json.dump(events_list, f, indent=4)

# Function to clean and save events to the database


def save_to_db():
    from access_amherst_algo.rss_scraper.clean_hub_data import clean_hub_data
    events_list = clean_hub_data()
    for event in events_list:
        save_event_to_db(event)


if __name__ == '__main__':
    save_json()
    save_to_db()
