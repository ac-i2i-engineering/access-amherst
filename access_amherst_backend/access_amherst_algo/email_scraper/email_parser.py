import imaplib
import email
from email.header import decode_header
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import requests
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for detailed logs in a dev environment
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the console
    ],
)

# Load environment variables
load_dotenv()

# LLaMA API endpoint
LLAMA_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# System instruction for extracting events and generating valid JSON format
instruction = """
    You will be provided an email containing many events.
    Extract detailed event information and provide the result as a list of event JSON objects. Make sure to not omit any available information.
    Ensure all fields are included, even if some data is missing (set a field to null (with no quotations) if the information is not present).
    Use this format for each event JSON object:

    {{
        "title": "Event Title",
        "pub_date": "YYYY-MM-DD",
        "starttime": "HH:MM:SS",
        "endtime": "HH:MM:SS",
        "location": "Event Location",
        "event_description": "Event Description",
        "host": ["Host Organization"],
        "link": "Event URL",
        "picture_link": "Image URL",
        "categories": ["Category 1", "Category 2"],
        "author_name": "Author Name",
        "author_email": "author@email.com"
    }}

    Ensure all fields follow the exact format above. Only return the list of event JSON objects. START WITH [{. END WITH }].
"""


def connect_and_fetch_latest_email(
    app_password, subject_filter, mail_server="imap.gmail.com"
):
    """
    Connect to the email server and fetch the latest email matching a subject filter.

    This function connects to the specified IMAP email server (default is Gmail),
    logs in using the provided app password, and searches for the most recent email
    with a subject matching the `subject_filter`. It returns the email message object 
    of the latest matching email.

    Parameters
    ----------
    app_password : str
        The app password used for logging into the email account.
    subject_filter : str
        The subject filter used to search for specific emails.
    mail_server : str, optional, default "imap.gmail.com"
        The IMAP email server address (default is 'imap.gmail.com').

    Returns
    -------
    email.message.Message or None
        The latest email message matching the filter, or None if no matching email is 
        found or login fails.

    Examples
    --------
    >>> email = connect_and_fetch_latest_email("amherst_college_password", "Amherst College Daily Mammoth for Sunday, November 3, 2024")
    >>> if email:
    >>>     print(email["From"])
    'noreply@amherst.edu'
    """
    logging.info("Connecting to email server...")
    try:
        mail = imaplib.IMAP4_SSL(mail_server)
        mail.login(os.getenv("EMAIL_ADDRESS"), app_password)
    except imaplib.IMAP4.error as e:
        logging.error(f"Login failed: {e}")
        return None

    try:
        mail.select("inbox")
        status, messages = mail.search(None, f'SUBJECT "{subject_filter}"')
        if status != "OK":
            logging.error(f"Failed to fetch emails: {status}")
            return None

        for msg_num in messages[0].split()[
            -1:
        ]:  # Only fetch the latest message
            res, msg = mail.fetch(msg_num, "(RFC822)")
            for response_part in msg:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    logging.info("Email fetched successfully.")
                    return msg
    except Exception as e:
        logging.error(f"Error while fetching emails: {e}")
    return None


def extract_email_body(msg):
    """
    Extract the body of an email message.

    This function extracts and returns the plain-text body of the given email message.
    It handles both multipart and non-multipart emails, retrieving the text content from 
    the message if available. If the email is multipart, it iterates over the parts to find 
    the "text/plain" part and decodes it. If the email is not multipart, it directly decodes 
    the payload.

    Parameters
    ----------
    msg : email.message.Message
        The email message object from which to extract the body.

    Returns
    -------
    str or None
        The decoded plain-text body of the email, or None if no text content is found.

    Examples
    --------
    >>> email_body = extract_email_body(email_msg)
    >>> print(email_body)
    'This is information about Amherst College events on Sunday, November 3, 2024.'
    """
    try:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    logging.info("Email body extracted successfully.")
                    return part.get_payload(decode=True).decode("utf-8")
        else:
            logging.info("Email body extracted successfully.")
            return msg.get_payload(decode=True).decode("utf-8")
    except Exception as e:
        logging.error(f"Failed to extract email body: {e}")
        return None


def extract_event_info_using_llama(email_content):
    """
    Extract event info from the email content using the LLaMA API.

    This function sends the provided email content to the LLaMA API for processing. 
    It sends the email content along with an instruction to extract event details.
    If the API response is valid, the function parses and returns the extracted 
    event information as a list of event JSON objects.

    Parameters
    ----------
    email_content : str
        The raw content of the email to be processed by the LLaMA API.

    Returns
    -------
    list
        A list of event data extracted from the email content in JSON format.
        If extraction fails, an empty list is returned.

    Examples
    --------
    >>> events = extract_event_info_using_llama("We're hosting a Literature Speaker Event this Tuesday, November 5, 2024 in Keefe Campus Center!")
    >>> print(events)
    [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefe Campus Center"}]
    """
    payload = {
        "model": "meta-llama/llama-3.1-405b-instruct:free",
        "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": email_content},
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(LLAMA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        if "error" in response_data:
            error_message = response_data["error"].get("message", "")
            logging.error(f"API Error: {error_message}")
            sys.exit(1)

        extracted_events_json = response_data["choices"][0]["message"][
            "content"
        ]
        events_data = json.loads(extracted_events_json)
        logging.info("Event data extracted successfully using LLaMA API.")
        return events_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from LLaMA API: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to parse LLaMA API response: {e}")
    return []


def save_to_json_file(data, filename, folder):
    """
    Save the extracted events to a JSON file.

    This function checks if the specified folder exists, creates it if it does not,
    and saves the provided event data to a JSON file with the specified filename.
    The data is saved with indentation for readability and structure.

    Parameters
    ----------
    data : dict or list
        The data to be saved in JSON format. Typically, this would be a list or dictionary
        containing event data.
    filename : str
        The name of the file where the data will be saved 
        (e.g., 'extracted_events_20241103_124530.json').
    folder : str
        The folder where the JSON file will be stored 
        (e.g., 'json_outputs').

    Returns
    -------
    None
        This function does not return any value but writes data to a JSON file.

    Examples
    --------
    >>> events = [{"title": "Literature Speaker Event", "date": "2024-11-05", "location": "Keefe Campus Center"}]
    >>> save_to_json_file(events, "extracted_events_20241105_150000.json", "json_outputs")
    Data successfully saved to json_outputs/extracted_events_20241105_150000.json
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
        logging.info(f"Created directory: {folder}")

    file_path = folder + "/" + filename
    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Data successfully saved to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")


def parse_email(subject_filter):
    """
    Parse the email and extract event data.

    This function connects to an email account, fetches the latest email based on the 
    provided subject filter, extracts event information from the email body using the 
    LLaMA API, and saves the extracted events to a JSON file. The file is saved with 
    a timestamped filename in the 'json_outputs' directory.

    Parameters
    ----------
    subject_filter : str
        The subject filter to identify the relevant email to fetch.

    Returns
    -------
    None
        This function does not return any value but logs status messages for each stage of the process.

    Examples
    --------
    >>> parse_email("Amherst College Daily Mammoth for Sunday, November 3, 2024")
    Email fetched successfully.
    Events saved successfully to extracted_events_20231103_150000.json.
    """
    app_password = os.getenv("EMAIL_PASSWORD")

    msg = connect_and_fetch_latest_email(app_password, subject_filter)
    if not msg:
        logging.error("No emails found or login failed.")
        return

    email_body = extract_email_body(msg)
    if not email_body:
        logging.error("Failed to extract email body.")
        return

    all_events = extract_event_info_using_llama(email_body)
    if not all_events:
        logging.warning("No event data extracted or extraction failed.")
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_events_{timestamp}.json"
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(curr_dir, "json_outputs")

        save_to_json_file(all_events, filename, output_dir)
    except Exception as e:
        logging.error(f"Error saving events: {e}")
