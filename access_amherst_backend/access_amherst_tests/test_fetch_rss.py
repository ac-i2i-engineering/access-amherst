import pytest
from unittest.mock import patch, mock_open
from access_amherst_algo.rss_scraper.fetch_rss import fetch_rss
from datetime import datetime

# Mock function to replace `requests.get`


@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'<rss>Mock RSS content</rss>'
        yield mock_get

# Test function for `fetch_rss`


def test_fetch_rss(mock_requests_get):
    # Mock the file handling to prevent actual file creation
    with patch('builtins.open', mock_open()) as mock_file, \
            patch('os.path.join') as mock_join:

        # Define the expected file name
        expected_filename = 'access_amherst_algo/rss_scraper/rss_files/hub_' + \
            datetime.now().strftime('%Y_%m_%d_%H') + '.xml'
        mock_join.return_value = expected_filename

        # Call the function
        fetch_rss()

        # Check if the GET request was called with the correct URL
        mock_requests_get.assert_called_once_with(
            'https://thehub.amherst.edu/events.rss')

        # Check if the file was opened with the correct name and mode
        mock_file.assert_called_once_with(expected_filename, 'wb')

        # Check if the content was written to the file
        mock_file().write.assert_called_once_with(b'<rss>Mock RSS content</rss>')
