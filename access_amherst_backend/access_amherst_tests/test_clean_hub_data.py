import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
from access_amherst_algo.rss_scraper.clean_hub_data import clean_hub_data


@pytest.fixture
def sample_pre_cleaned_data():
    return [
        {
            "title": "Amherst Women\u2019s Soccer vs Bowdoin College  (Cancelled)",
            "author": "sel@amherst.edu (Student Engagement and Leadership)",
            "pub_date": "Fri, 18 Oct 2024 02:21:19 GMT",
            "host": [
                "Student Engagement and Leadership"
            ],
            "link": "https://thehub.amherst.edu/event/10485655",
            "picture_link": "https://se-images.campuslabs.com/clink/images/cbf66210-67fa-4025-b13f-36be0ffb0e20bb4c6bb9-bb85-4782-9542-00f339e7a730.png?preset=med-w",
            "event_description": "<p>Come support the mammoths in a conference match up against Bowdoin\u00a0</p>",
            "starttime": "Sat, 26 Oct 2024 16:00:00 GMT",
            "endtime": "Sat, 26 Oct 2024 18:00:00 GMT",
            "location": "Hitchcock Field ",
            "categories": [
                "Athletics"
            ]
        },
        {
            "title": "Amherst Cricket Club Practices",
            "author": "dmavani25@amherst.edu (Amherst College Cricket Club)",
            "pub_date": "Fri, 18 Oct 2024 02:21:19 GMT",
            "host": [
                "Amherst College Cricket Club"
            ],
            "link": "https://thehub.amherst.edu/event/10428286",
            "picture_link": "https://se-images.campuslabs.com/clink/images/8cadf245-7639-4970-bf3c-0be3d0ef46b2f593f79a-2223-4cf8-86cb-54db96a57346.png?preset=med-w",
            "event_description": "<div class=\"gmail_default\">Dear Cricketers,</div>\n<div class=\"gmail_default\">\u00a0</div>\n<div class=\"gmail_default\">This semester's practices are scheduled on the following times at a\u00a0<strong>weekly</strong>\u00a0cadence in\u00a0<strong>Coolidge Cage (Alumni Gym aka Tennis Courts)</strong>:</div>\n<div class=\"gmail_default\">\n<ul>\n<li><strong>Thursday 8-10 pm</strong></li>\n<li><strong>Saturday 3-5 pm</strong></li>\n</ul>\n<div><strong>So, the\u00a0INTRO-meeting is (12th Sept) THIS THURSDAY 8-10 pm!!! Equipment &amp; Snacks/Drinks Covered!</strong></div>\n<div><strong>\u00a0</strong></div>\n<div>\n<div class=\"gmail_default\">Before that, as per the\u00a0Amherst College rules, please fill out the waiver below so that we can start the\u00a0ball rolling! And, I have also sent all of you invites on the Hub to join the club, so please accept the invite there to stay posted! (GroupMe:\u00a0<a data-saferedirecturl=\"https://www.google.com/url?q=https://groupme.com/join_group/97352198/c7Az2Nim&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw0iWr_SDUW44AuoUlaEUscv\" href=\"https://groupme.com/join_group/97352198/c7Az2Nim\" rel=\"noopener\" target=\"_blank\">https://groupme.com/join_<wbr/>group/97352198/c7Az2Nim</a>)</div>\n<div class=\"gmail_default\">\n<h3>How do I sign the waiver?</h3>\n<p>Link:\u00a0<a data-saferedirecturl=\"https://www.google.com/url?q=https://risk-management.mtholyoke.edu/waivers/login.php&amp;source=gmail&amp;ust=1725996770831000&amp;usg=AOvVaw39nwDGnBb65E4VJnnujTZ-\" href=\"https://risk-management.mtholyoke.edu/waivers/login.php\" rel=\"noopener\" target=\"_blank\">https://risk-management.<wbr/>mtholyoke.edu/waivers/login.<wbr/>php</a></p>\n<p>Once logged in, you should click on\u00a0<strong>Waiver Form</strong>\u00a0in the top left-hand corner, and then select the following from the drop-down menus:</p>\n<p><strong>College:</strong>\u00a0Amherst College<br/><strong>Activity Type:</strong>\u00a0Student Group<br/><strong>Activity Name:</strong>\u00a0Amherst College Cricket Club</p>\n<p>After that you will be prompted to sign and fill in your background information!</p>\n<p>Thank you so much\u00a0for your\u00a0support and patience throughout this!</p>\n<p>Take care,</p>\n<p>Founder &amp; President of Cricket Club</p>\n</div>\n</div>\n</div>",
            "starttime": "Sat, 26 Oct 2024 19:00:00 GMT",
            "endtime": "Sat, 26 Oct 2024 20:00:00 GMT",
            "location": "Amherst Alumni Gym (Coolidge Cage)",
            "categories": [
                "Athletics",
                "Meeting",
                "Workshop"
            ]
        }
    ]


@patch('builtins.open', new_callable=mock_open)
@patch('access_amherst_algo.rss_scraper.clean_hub_data.create_events_list')
def test_clean_hub_data(
        mock_create_events_list,
        mock_open,
        sample_pre_cleaned_data):
    mock_create_events_list.return_value = sample_pre_cleaned_data
    cleaned_events = clean_hub_data()

    assert len(cleaned_events) == 1
    assert cleaned_events[0]['title'] == 'Amherst Cricket Club Practices'
    assert cleaned_events[0]['author_name'] == 'Amherst College Cricket Club'
    assert cleaned_events[0]['author_email'] == 'dmavani25@amherst.edu'

    mock_open.assert_called_once_with(
        'access_amherst_algo/rss_scraper/cleaned_json_outputs/hub_' +
        datetime.now().strftime('%Y_%m_%d_%H') +
        '.json',
        'w')
