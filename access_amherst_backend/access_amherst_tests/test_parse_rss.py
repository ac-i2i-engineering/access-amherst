import pytz
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
import xml.etree.ElementTree as ET
from dateutil import parser
import pytz
from access_amherst_algo.rss_scraper.parse_rss import (
    create_events_list,
    save_json,
    extract_event_details,
    save_to_db,
    save_event_to_db,
    categorize_location,
    get_lat_lng,
    add_random_offset,
    is_similar_event,
    format_category,
)
from access_amherst_algo.models import Event
from datetime import datetime
import os


@pytest.fixture
def xml_item_queer_talk():
    # Sample XML data for tests
    xml_data_queer_talk = """
    <item>
    <title>Queer Talk</title>
    <guid>https://thehub.amherst.edu/event/10538770</guid>
    <link>https://thehub.amherst.edu/event/10538770</link>
    <enclosure url="https://se-images.campuslabs.com/clink/images/bcbdb250-d63e-4d8d-9a6d-da44aa8785acbfe87d36-e7d5-486e-960d-cdb6b899e21d.pdf?preset=med-w" length="1" type="image/jpeg" />
    <description><![CDATA[<div class="h-event vevent">
    <div class="p-name summary">Queer Talk</div>
    <div class="p-description description"><p>Join us at the QRC for Queer Talk, a weekly conversation about queerness with a new theme every week! Don&rsquo;t miss it!!</p></div>
    <div>
        <p>
        From <time class="dt-start dtstart" datetime="2024-10-18T16:00:00.0000000-04:00" title="2024-10-18T16:00:00.0000000-04:00">Friday, October 18, 2024 4:00 PM</time>
        to <time class="dt-end dtend" datetime="2024-10-18T17:00:00.0000000-04:00" title="2024-10-18T17:00:00.0000000-04:00">5:00 PM EDT</time>
        at <span class="p-location location">Queer Resource Center (Keefe 213)</span>.
        </p>
    </div>
    </div>]]></description>
    <category>Social</category>
    <pubDate>Fri, 18 Oct 2024 02:21:19 GMT</pubDate>
    <start xmlns="events">Fri, 18 Oct 2024 20:00:00 GMT</start>
    <end xmlns="events">Fri, 18 Oct 2024 21:00:00 GMT</end>
    <location xmlns="events">Queer Resource Center (Keefe 213)</location>
    <status xmlns="events">confirmed</status>
    <host xmlns="events">Queer Resource Center</host>
    </item>
    """
    return ET.fromstring(xml_data_queer_talk)


@pytest.fixture
def xml_item_cricket_club():
    xml_data = """
    <item>
        <title>Amherst Cricket Club Practices</title>
        <link>https://thehub.amherst.edu/event/10428285</link>
        <enclosure url="https://se-images.campuslabs.com/clink/images/8cadf245-7639-4970-bf3c-0be3d0ef46b2f593f79a-2223-4cf8-86cb-54db96a57346.png?preset=med-w" length="1" type="image/jpeg" />
        <description><![CDATA[<div class="h-event vevent">
            <div class="p-description description"><div>Amherst Cricket Club Practice Details</div></div></div>]]></description>
        <category>Athletics</category>
        <category>Meeting</category>
        <pubDate>Fri, 18 Oct 2024 02:21:19 GMT</pubDate>
        <start xmlns="events">Sat, 19 Oct 2024 19:00:00 GMT</start>
        <end xmlns="events">Sat, 19 Oct 2024 20:00:00 GMT</end>
        <location xmlns="events">Amherst Alumni Gym (Coolidge Cage)</location>
        <author>dmavani25@amherst.edu (Amherst College Cricket Club)</author>
        <host xmlns="events">Amherst College Cricket Club</host>
    </item>
    """
    return ET.fromstring(xml_data)


def test_extract_event_details_cricket_club(xml_item_cricket_club):
    result = extract_event_details(xml_item_cricket_club)
    assert result["title"] == "Amherst Cricket Club Practices"
    assert result["link"] == "https://thehub.amherst.edu/event/10428285"
    assert (
        result["picture_link"]
        == "https://se-images.campuslabs.com/clink/images/8cadf245-7639-4970-bf3c-0be3d0ef46b2f593f79a-2223-4cf8-86cb-54db96a57346.png?preset=med-w"
    )
    assert (
        result["event_description"]
        == "<div>Amherst Cricket Club Practice Details</div>"
    )
    assert result["pub_date"] == "Fri, 18 Oct 2024 02:21:19 GMT"
    assert result["starttime"] == "Sat, 19 Oct 2024 19:00:00 GMT"
    assert result["endtime"] == "Sat, 19 Oct 2024 20:00:00 GMT"
    assert result["location"] == "Amherst Alumni Gym (Coolidge Cage)"
    assert result["categories"] == ["Athletics", "Meeting"]
    assert result["author_name"] == "Amherst College Cricket Club"
    assert result["author_email"] == "dmavani25@amherst.edu"
    assert result["map_location"] == "Alumni Gymnasium"


def test_extract_event_details_cricket_club(xml_item_cricket_club):
    result = extract_event_details(xml_item_cricket_club)
    assert result["title"] == "Amherst Cricket Club Practices"
    assert result["link"] == "https://thehub.amherst.edu/event/10428285"
    assert (
        result["picture_link"]
        == "https://se-images.campuslabs.com/clink/images/8cadf245-7639-4970-bf3c-0be3d0ef46b2f593f79a-2223-4cf8-86cb-54db96a57346.png?preset=med-w"
    )
    assert (
        result["event_description"]
        == "<div>Amherst Cricket Club Practice Details</div>"
    )
    assert result["pub_date"] == "Fri, 18 Oct 2024 02:21:19 GMT"
    assert result["starttime"] == "Sat, 19 Oct 2024 19:00:00 GMT"
    assert result["endtime"] == "Sat, 19 Oct 2024 20:00:00 GMT"
    assert result["location"] == "Amherst Alumni Gym (Coolidge Cage)"
    assert result["categories"] == ["Athletics", "Meeting"]
    assert (
        result["author"]
        == "dmavani25@amherst.edu (Amherst College Cricket Club)"
    )
    assert result["host"] == ["Amherst College Cricket Club"]
    assert result["map_location"] == "Alumni Gymnasium"


@pytest.fixture
def mock_rss_file():
    # Mock rss data
    rss_data = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
  <channel><title>Amherst College Public Events occurring between Thursday, October 17, 2024 10:21 PM EDT and Saturday, November 16, 2024 9:21 PM EST</title>
<description>A listing of public events for Amherst College occurring between Thursday, October 17, 2024 10:21 PM EDT and Saturday, November 16, 2024 9:21 PM EST.</description>
<language>en-us</language>
<lastBuildDate>Fri, 18 Oct 2024 02:21:19 GMT</lastBuildDate>
<category>Public Events</category>
<generator>Campus Labs Engage</generator>
<ttl>300</ttl>
<pubDate>Fri, 18 Oct 2024 02:21:19 GMT</pubDate>
<link>https://thehub.amherst.edu/events</link>
    <item>
    <title>Event 1</title>
    <description>Details for Event 1</description>
    </item>
    <item>
    <title>Event 2</title>
    <description>Details for Event 2</description>
    </item></channel>
    </rss>"""

    # Write the mock RSS data to a temporary file
    rss_file_path = f"access_amherst_algo/rss_scraper/rss_files/hub_{datetime.now().strftime('%Y_%m_%d_%H')}.xml"

    # Write the mock RSS data to this file
    with open(rss_file_path, "w") as file:
        file.write(rss_data)

    # Return the file path to be used in the test
    return rss_file_path


@patch("access_amherst_algo.rss_scraper.parse_rss.extract_event_details")
def test_create_event_list(mock_extract_event_details, mock_rss_file):
    # Mock extract_event_details to return specific data for each event
    mock_extract_event_details.side_effect = [
        {"title": "Event 1", "event_description": "Details for Event 1"},
        {"title": "Event 2", "event_description": "Details for Event 2"},
    ]

    # Patch the function's expected file path
    with patch(
        "access_amherst_algo.rss_scraper.parse_rss.create_events_list"
    ) as mock_rss_file_path:
        mock_rss_file_path.return_value = mock_rss_file
        # Call create_events_list and get the result
        events = create_events_list()

        # Check that events are correctly extracted
        assert len(events) == 2

        # Check the details of the first event
        assert events[0]["title"] == "Event 1"
        assert events[0]["event_description"] == "Details for Event 1"

        # Check the details of the second event
        assert events[1]["title"] == "Event 2"
        assert events[1]["event_description"] == "Details for Event 2"

        # Clean up the temporary file
        os.remove(mock_rss_file)


@pytest.fixture
def event_list():
    # Mock output of create_event_list
    event_list = [
        {
            "title": "Queer Talk",
            "author": None,
            "pub_date": "Fri, 18 Oct 2024 02:21:19 GMT",
            "host": ["Queer Resource Center"],
            "link": "https://thehub.amherst.edu/event/10538770",
            "picture_link": "https://se-images.campuslabs.com/clink/images/bcbdb250-d63e-4d8d-9a6d-da44aa8785acbfe87d36-e7d5-486e-960d-cdb6b899e21d.pdf?preset=med-w",
            "event_description": "<p>Join us at the QRC for Queer Talk, a weekly conversation about queerness with a new theme every week! Don\u2019t miss it!!</p>",
            "starttime": "Fri, 18 Oct 2024 20:00:00 GMT",
            "endtime": "Fri, 18 Oct 2024 21:00:00 GMT",
            "location": "Queer Resource Center (Keefe 213)",
            "categories": ["Social"],
        },
        {
            "title": "Amherst Cricket Club Practices",
            "author": "dmavani25@amherst.edu (Amherst College Cricket Club)",
            "pub_date": "Fri, 18 Oct 2024 02:21:19 GMT",
            "host": ["Amherst College Cricket Club"],
            "link": "https://thehub.amherst.edu/event/10428269",
            "picture_link": "https://se-images.campuslabs.com/clink/images/a70f783f-513b-4de7-9348-85134e311d76040d872b-6bbf-47a4-863e-0b24b295f5ab.png?preset=med-w",
            "event_description": '<div class="gmail_default">Dear Cricketers,</div>\n<div class="gmail_default">\u00a0</div>\n<div class="gmail_default">This semester\'s practices are scheduled on the following times at a\u00a0<strong>weekly</strong>\u00a0cadence in\u00a0<strong>Coolidge Cage (Alumni Gym aka Tennis Courts)</strong>:</div>\n<div class="gmail_default">\n<ul>\n<li><strong>Thursday 8-10 pm</strong></li>\n<li><strong>Saturday 3-5 pm</strong></li>\n</ul>\n<div><strong>So, the\u00a0INTRO-meeting is (12th Sept) THIS THURSDAY 8-10 pm!!! Equipment &amp; Snacks/Drinks Covered!</strong></div>\n<div><strong>\u00a0</strong></div>\n<div>\n<div class="gmail_default">Before that, as per the\u00a0Amherst College rules, please fill out the waiver below so that we can start the\u00a0ball rolling! And, I have also sent all of you invites on the Hub to join the club, so please accept the invite there to stay posted! (GroupMe:\u00a0<a data-saferedirecturl="https://www.google.com/url?q=https://groupme.com/join_group/97352198/c7Az2Nim&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw0iWr_SDUW44AuoUlaEUscv" href="https://groupme.com/join_group/97352198/c7Az2Nim" rel="noopener" target="_blank">https://groupme.com/join_<wbr/>group/97352198/c7Az2Nim</a>)</div>\n<div class="gmail_default">\n<h3>How do I sign the waiver?</h3>\n<p>Link:\u00a0<a data-saferedirecturl="https://www.google.com/url?q=https://risk-management.mtholyoke.edu/waivers/login.php&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw39nwDGnBb65E4VJnnujTZ-" href="https://risk-management.mtholyoke.edu/waivers/login.php" rel="noopener" target="_blank">https://risk-management.<wbr/>mtholyoke.edu/waivers/login.<wbr/>php</a></p>\n<p>Once logged in, you should click on\u00a0<strong>Waiver Form</strong>\u00a0in the top left-hand corner, and then select the following from the drop-down menus:</p>\n<p><strong>College:</strong>\u00a0Amherst College<br/><strong>Activity Type:</strong>\u00a0Student Group<br/><strong>Activity Name:</strong>\u00a0Amherst College Cricket Club</p>\n<p>After that you will be prompted to sign and fill in your background information!</p>\n<p>Thank you so much\u00a0for your\u00a0support and patience throughout this!</p>\n<p>Take care,</p>\n<p>Founder &amp; President of Cricket Club</p>\n</div>\n</div>\n</div>',
            "starttime": "Fri, 25 Oct 2024 00:00:00 GMT",
            "endtime": "Fri, 25 Oct 2024 02:00:00 GMT",
            "location": "Amherst Alumni Gym (Coolidge Cage)",
            "categories": ["Athletics", "Workshop"],
        },
    ]
    return event_list


@patch("access_amherst_algo.rss_scraper.parse_rss.create_events_list")
@patch(
    "access_amherst_algo.rss_scraper.parse_rss.open", new_callable=mock_open
)
@patch("access_amherst_algo.rss_scraper.parse_rss.json.dump")
def test_save_json(
    mock_json_dump, mock_open, mock_create_events_list, event_list
):
    # Mock the return value of `create_events_list`
    mock_create_events_list.return_value = event_list

    # Call the function
    save_json()

    # Check that `create_events_list` was called
    mock_create_events_list.assert_called_once()

    # Verify file path and opening mode
    expected_file_name = (
        "access_amherst_algo/rss_scraper/json_outputs/hub_"
        + datetime.now().strftime("%Y_%m_%d_%H")
        + ".json"
    )
    mock_open.assert_called_once_with(expected_file_name, "w")

    # Check the content written to the file
    mock_json_dump.assert_called_once_with(event_list, mock_open(), indent=4)


@pytest.fixture
def sample_pre_cleaned_data():
    return [
        {
            "title": "Amherst Cricket Club Practices",
            "author": "dmavani25@amherst.edu (Amherst College Cricket Club)",
            "pub_date": "Fri, 18 Oct 2024 02:21:19 GMT",
            "host": ["Amherst College Cricket Club"],
            "link": "https://thehub.amherst.edu/event/10428286",
            "picture_link": "https://se-images.campuslabs.com/clink/images/8cadf245-7639-4970-bf3c-0be3d0ef46b2f593f79a-2223-4cf8-86cb-54db96a57346.png?preset=med-w",
            "event_description": '<div class="gmail_default">Dear Cricketers,</div>\n<div class="gmail_default">\u00a0</div>\n<div class="gmail_default">This semester\'s practices are scheduled on the following times at a\u00a0<strong>weekly</strong>\u00a0cadence in\u00a0<strong>Coolidge Cage (Alumni Gym aka Tennis Courts)</strong>:</div>\n<div class="gmail_default">\n<ul>\n<li><strong>Thursday 8-10 pm</strong></li>\n<li><strong>Saturday 3-5 pm</strong></li>\n</ul>\n<div><strong>So, the\u00a0INTRO-meeting is (12th Sept) THIS THURSDAY 8-10 pm!!! Equipment &amp; Snacks/Drinks Covered!</strong></div>\n<div><strong>\u00a0</strong></div>\n<div>\n<div class="gmail_default">Before that, as per the\u00a0Amherst College rules, please fill out the waiver below so that we can start the\u00a0ball rolling! And, I have also sent all of you invites on the Hub to join the club, so please accept the invite there to stay posted! (GroupMe:\u00a0<a data-saferedirecturl="https://www.google.com/url?q=https://groupme.com/join_group/97352198/c7Az2Nim&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw0iWr_SDUW44AuoUlaEUscv" href="https://groupme.com/join_group/97352198/c7Az2Nim" rel="noopener" target="_blank">https://groupme.com/join_<wbr/>group/97352198/c7Az2Nim</a>)</div>\n<div class="gmail_default">\n<h3>How do I sign the waiver?</h3>\n<p>Link:\u00a0<a data-saferedirecturl="https://www.google.com/url?q=https://risk-management.mtholyoke.edu/waivers/login.php&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw39nwDGnBb65E4VJnnujTZ-" href="https://risk-management.mtholyoke.edu/waivers/login.php" rel="noopener" target="_blank">https://risk-management.<wbr/>mtholyoke.edu/waivers/login.<wbr/>php</a></p>\n<p>Once logged in, you should click on\u00a0<strong>Waiver Form</strong>\u00a0in the top left-hand corner, and then select the following from the drop-down menus:</p>\n<p><strong>College:</strong>\u00a0Amherst College<br/><strong>Activity Type:</strong>\u00a0Student Group<br/><strong>Activity Name:</strong>\u00a0Amherst College Cricket Club</p>\n<p>After that you will be prompted to sign and fill in your background information!</p>\n<p>Thank you so much\u00a0for your\u00a0support and patience throughout this!</p>\n<p>Take care,</p>\n<p>Founder &amp; President of Cricket Club</p>\n</div>\n</div>\n</div>',
            "starttime": "Sat, 26 Oct 2024 19:00:00 GMT",
            "endtime": "Sat, 26 Oct 2024 20:00:00 GMT",
            "location": "Amherst Alumni Gym (Coolidge Cage)",
            "categories": ["Athletics", "Meeting", "Workshop"],
        }
    ]


@pytest.fixture
def sample_cleaned_data():
    # Sample data fixture to be used across multiple tests
    return [
        {
            "title": "Regular HEMAC Meeting",
            "author": None,
            "id": "590_363_344",
            "pub_date": "Sun, 20 Oct 2024 18:50:18 GMT",
            "host": ["Historical European Martial Arts Club"],
            "link": "https://thehub.amherst.edu/event/90363344",
            "picture_link": "https://se-images.campuslabs.com/clink/images/a2ba57c3-df45-488c-89bd-be5f6618c6ed64337f06-79e3-4927-a1a9-5e8c89cc7bcc.png?preset=med-w",
            "event_description": "<p>Swords, quarterstaves, daggers, historical sources...</p>",
            "starttime": "Sun, 20 Oct 2024 20:30:00 GMT",
            "endtime": "Sun, 20 Oct 2024 22:00:00 GMT",
            "location": "In front of Alumni Gym (facing the road)",
            "categories": ["Social", "Meeting"],
        }
    ]


# Unit test with mocking
@pytest.mark.django_db
@patch("access_amherst_algo.rss_scraper.parse_rss.save_event_to_db")
@patch("access_amherst_algo.rss_scraper.clean_hub_data.clean_hub_data")
def test_save_to_db(mock_clean_hub_data, mock_save_event, sample_cleaned_data):
    # Mock clean_hub_data to return sample data
    mock_clean_hub_data.return_value = sample_cleaned_data

    # Run save_to_db, which should call save_event_to_db with the sample data
    save_to_db()

    # Verify that save_event_to_db was called with the correct data
    mock_save_event.assert_called_once_with(sample_cleaned_data[0])


# Database test with actual data saving
@pytest.mark.django_db
def test_save_event_creates_new_event(sample_cleaned_data):
    # Modify sample_cleaned_data to match the separated author fields
    sample_cleaned_data[0]["author_name"] = "Amherst College Cricket Club"
    sample_cleaned_data[0]["author_email"] = "dmavani25@amherst.edu"

    # Pass the first dictionary in the list to save_event_to_db
    save_event_to_db(sample_cleaned_data[0])

    # Check that exactly one event is created in the database
    assert Event.objects.count() == 1

    # Retrieve the created event using the expected ID
    event = Event.objects.get(id=90_363_344 + 500_000_000)

    # Verify event fields match the expected values
    assert event.author_name == "Amherst College Cricket Club"
    assert event.author_email == "dmavani25@amherst.edu"


@pytest.mark.django_db
def test_save_event_updates_existing_event(sample_cleaned_data):
    sample_cleaned_data[0]["author_name"] = "Amherst College Cricket Club"
    sample_cleaned_data[0]["author_email"] = "dmavani25@amherst.edu"

    # Save initial event
    save_event_to_db(sample_cleaned_data[0])

    # Prepare updated data by modifying a copy of the initial dictionary
    updated_data = sample_cleaned_data[0].copy()
    updated_data["title"] = "Updated Title"
    updated_data["author_name"] = "Updated Author"

    # Save the updated data to the database
    save_event_to_db(updated_data)

    # Verify the event was updated
    event = Event.objects.get(id=90_363_344 + 500_000_000)
    assert event.title == "Updated Title"
    assert event.author_name == "Updated Author"


# Test for categorize_location function, covering more keywords and "Other" case
def test_categorize_location():
    assert categorize_location("Keefe Campus Center") == "Keefe Campus Center"
    assert categorize_location("Ford Hall") == "Ford Hall"
    assert categorize_location("Unknown Location") == "Other"


# Test get_lat_lng function for known and unknown locations
def test_get_lat_lng():
    lat, lng = get_lat_lng("Science Center")
    assert lat == 42.37105378715133
    assert lng == -72.51334790776447

    lat, lng = get_lat_lng("Unknown Location")
    assert lat is None
    assert lng is None


# Test add_random_offset function with known lat/lng to verify range of offset
def test_add_random_offset():
    lat, lng = 42.372092, -72.514224
    new_lat, new_lng = add_random_offset(lat, lng)

    # Check the offset range
    assert abs(new_lat - lat) < 0.00015
    assert abs(new_lng - lng) < 0.00015


# Test is_similar_event for exact match and close title match
@pytest.mark.django_db
def test_is_similar_event():
    """Test similar event detection with same start time and similar title"""
    # Prepare test event data
    event_data = {
        "id": "90363344",
        "title": "Regular HEMAC Meeting",
        "starttime": "2024-10-20T20:30:00Z",  # Use ISO format
        "endtime": "2024-10-20T22:00:00Z",
        "author_name": "Historical European Martial Arts Club",
        "author_email": None,
        "categories": ["Social", "Meeting"],
        "location": "In front of Alumni Gym",
        "event_description": "<p>Test description</p>",
        "host": ["HEMAC"],
        "link": "https://test.com",
        "picture_link": None,
        "pub_date": "2024-10-20T18:50:18Z"
    }

    # Save initial event
    save_event_to_db(event_data)

    # Create similar event with slightly different title
    similar_data = event_data.copy()
    similar_data["title"] = "Regular HEMAC Meet"  # Similar title
    assert is_similar_event(similar_data) == True  # Expecting a match

    # Create a similar event with a different start time
    different_time_data = event_data.copy()
    different_time_data["starttime"] = (
        "Sun, 20 Oct 2024 22:30:00 GMT"  # Different time
    )
    assert is_similar_event(different_time_data) == False  # Expecting no match


# Test create_events_list for correct extraction and parsing
@patch("access_amherst_algo.rss_scraper.parse_rss.extract_event_details")
@patch("xml.etree.ElementTree.parse")
def test_create_events_list(
    mock_parse, mock_extract_event_details, xml_item_queer_talk
):
    mock_parse.return_value.getroot.return_value.findall.return_value = [
        xml_item_queer_talk
    ]
    mock_extract_event_details.return_value = {
        "title": "Test Event",
        "link": "https://testlink.com",
        "starttime": "2024-10-18T20:00:00",
        "endtime": "2024-10-18T21:00:00",
        "location": "Test Location",
        "categories": ["Social"],
    }

    events_list = create_events_list()
    assert len(events_list) == 1
    assert events_list[0]["title"] == "Test Event"


def test_format_category():
    """Test the format_category function for various category string formats"""
    
    # Test basic lowercase concatenated words
    assert format_category("academicCalendar") == "Academic Calendar"
    
    # Test camelCase
    assert format_category("artsAndCulture") == "Arts And Culture"
    
    # Test handling of 'and' conjunction in lowercase
    assert format_category("concertsandperformances") == "Concerts And Performances"
    
    # Test multiple word categories
    assert format_category("campusLifeStudent") == "Campus Life Student"
    
    # Test single word
    assert format_category("social") == "Social"
    
    # Test empty string
    assert format_category("") == ""
    
    # Test mixed case
    assert format_category("studentLifeActivities") == "Student Life Activities"
    
    # Test with spaces already present
    assert format_category("campus life") == "Campus Life"