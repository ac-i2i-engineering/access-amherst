import requests
import json
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.amherst.edu/news/events/calendar"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.amherst.edu/",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraping_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_page(url):
    """
    Fetch the raw content of a webpage.

    This function sends an HTTP GET request to the specified URL and retrieves 
    the page content. It handles connection errors, timeouts, and unexpected 
    errors, logging relevant information.

    Parameters
    ----------
    url : str
        The URL of the webpage to fetch.

    Returns
    -------
    bytes or None
        The raw HTML content of the page if the request is successful, otherwise None.

    Examples
    --------
    >>> fetch_page("https://www.amherst.edu/news/events/calendar")
    >>> if html_content:
    >>>     print(html_content[:500])  # Print the first 500 bytes of the HTML content
    """
    logger.info(f"Fetching URL: {url}")
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            return None
        return response.content
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.error(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None

def scrape_page(url):
    """
    Scrape event details from a specified webpage.

    This function retrieves and parses the HTML content of the given URL to extract 
    event details, including title, author, publication date, description, start 
    and end times, location, and image links. If a CAPTCHA is detected, the function 
    will return an empty list.

    Parameters
    ----------
    url : str
        The URL of the event listing page to scrape.

    Returns
    -------
    list of dict
        A list of dictionaries, each containing extracted event details.

    Examples
    --------
    >>> events = scrape_page("https://www.amherst.edu/news/events/calendar?_page=1")
    >>> print(events[0]["title"])
    'Literature Speaker Event'
    """
    logger.info(f"Scraping page: {url}")

    try:
        html = fetch_page(url)
        if not html:
            logger.warning(f"Page {url} does not exist or failed to load.")
            return []

        soup = BeautifulSoup(html, "html.parser")

        if "captcha" in soup.text.lower():
            logger.warning("CAPTCHA detected. Unable to scrape this page.")
            return []

        events = []
        for article in soup.find_all("article", class_="mm-calendar-event"):
            event = {
                "title": None,
                "author_name": None,
                "author_email": None,
                "pub_date": None,
                "host": None,
                "link": None,
                "picture_link": None,
                "event_description": None,
                "start_time": None,
                "end_time": None,
                "location": None
            }

            # Extract basic event information
            title_tag = article.find("h2", class_="mm-event-listing-title").find("a")
            if title_tag:
                event["title"] = title_tag.text.strip()
                event["link"] = title_tag["href"]

            period_tag = article.find("h3", class_="mm-calendar-period")
            if period_tag:
                start_meta = period_tag.find("meta", itemprop="startDate")
                if start_meta:
                    event["start_time"] = start_meta["content"]

                end_meta = period_tag.find("meta", itemprop="endDate")
                if end_meta:
                    event["end_time"] = end_meta["content"]

            location_tag = article.find("p", class_="mm-event-listing-location")
            if location_tag:
                event["location"] = location_tag.get_text(strip=True)

            description_tag = article.find("div", class_="mm-event-listing-description")
            if description_tag:
                event["event_description"] = description_tag.get_text(strip=True)

            picture_tag = article.find("img", itemprop="image")
            if picture_tag and "data-src" in picture_tag.attrs:
                event["picture_link"] = "https://www.amherst.edu" + picture_tag.attrs["data-src"]

            events.append(event)

        logger.info(f"Scraped {len(events)} events from {url}")
    
    except Exception as e:
        logger.error(f"Error Scraping page {url}: {e}")
        return []

    return events

def scrape_all_pages():
    """
    Scrape all event pages iteratively until no more events are found.

    This function starts scraping from the first page and continues incrementing 
    the page number until no more events are detected. It aggregates all scraped 
    events into a single list.

    Returns
    -------
    list of dict
        A list of all scraped events across multiple pages.

    Examples
    --------
    >>> all_events = scrape_all_pages()
    >>> print(f"Total events scraped: {len(all_events)}")
    """
    logger.info("Starting scrape of all pages")
    page = 0
    all_events = []

    while True:
        url = f"{BASE_URL}?_page={page}"
        events = scrape_page(url)

        if not events:
            logger.info(f"No events found on page {page}. Stopping scrape.")
            break

        all_events.extend(events)
        logger.info(f"Total events scraped so far: {len(all_events)}")
        page += 1

    logger.info(f"Scraping completed. Total events scraped: {len(all_events)}")
    return all_events

def save_to_json(events):
    """
    Save scraped event data to a JSON file.

    This function saves event data to a timestamped JSON file inside the 
    `calendar_json_outputs` directory. If a file already exists for the 
    current date, the function will skip saving to avoid duplicates.

    Parameters
    ----------
    events : list of dict
        A list of dictionaries containing event data to be saved.

    Returns
    -------
    None
        This function does not return any value but logs success or failure messages.

    Examples
    --------
    >>> events = [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefe Campus Center"}]
    >>> save_to_json(events)
    Events saved to access_amherst_algo/calendar_scraper/calendar_json_outputs/events_2024-11-05.json
    """
    logger.info("Saving events to JSON file")
    
    try:
        output_dir = "access_amherst_algo/calendar_scraper/calendar_json_outputs"
        os.makedirs(output_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{output_dir}/events_{date_str}.json"

        if os.path.exists(file_name):
            logger.info(f"JSON file for today already exists: {file_name}. Skipping save.")
            return

        cleaned_events = [{k: v for k, v in event.items() if v is not None} for event in events]

        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(cleaned_events, file, indent=4, ensure_ascii=False)

        logger.info(f"Events saved to {file_name}")

    except PermissionError as e:
        logger.error(f"Permission denied while saving JSON: {e}")
        raise