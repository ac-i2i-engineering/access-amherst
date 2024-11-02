import imaplib
import email
from email.header import decode_header
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import requests  # Use requests for API calls

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

# Function to connect to Gmail and fetch the latest email from a specific
# sender


def connect_and_fetch_latest_email(
        app_password,
        subject_filter,
        mail_server="imap.gmail.com"):
    mail = imaplib.IMAP4_SSL(mail_server)
    try:
        mail.login(os.getenv("EMAIL_ADDRESS"), app_password)
        print("Logged in successfully")
    except imaplib.IMAP4.error as e:
        print(f"Login failed: {e}")
        return None

    mail.select("inbox")
    status, messages = mail.search(None, f'SUBJECT "{subject_filter}"')
    if status != "OK":
        print(f"Failed to fetch emails: {status}")
        return None

    for msg_num in messages[0].split()[-1:]:  # Only fetch the latest message
        res, msg = mail.fetch(msg_num, "(RFC822)")
        for response_part in msg:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                return msg
    return None

# Function to extract the email body


def extract_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode('utf-8')
    else:
        return msg.get_payload(decode=True).decode('utf-8')

# Function to extract event info using LLaMA API


def extract_event_info_using_llama(email_content):
    """
    Extract event info from the email content using the LLaMA API.
    """

    # API payload for LLaMA
    payload = {
        "model": "meta-llama/llama-3.1-405b-instruct:free",
        "messages": [
            {
                "role": "system",
                "content": instruction
            },
            {
                "role": "user",
                "content": email_content
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Send the API request
    response = requests.post(LLAMA_API_URL, headers=headers, json=payload)

    # Check for a valid response
    if response.status_code == 200:
        try:
            # Parse the JSON response
            response_data = response.json()
            print(response_data)

            # Extract the content of the message
            extracted_events_json = response_data['choices'][0]['message']['content']

            # Now parse the extracted content as JSON
            # Convert the content to a list of event JSON objects
            events_data = json.loads(extracted_events_json)
            return events_data
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse LLaMA API response: {e}")
            return []
    else:
        print(f"Failed to fetch data from LLaMA API: {response.status_code}")
        return []

# Function to save the extracted events to a JSON file


def save_to_json_file(data, filename, folder):
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Construct the full file path
    file_path = os.path.join(folder, filename)

    try:
        with open(file_path, 'w') as json_file:
            # Save data with indentation for readability
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Failed to save data to {file_path}: {e}")

# Main function to parse the email and extract events


def parse_email(subject_filter):
    app_password = os.getenv("EMAIL_PASSWORD")

    # Fetch the latest email
    msg = connect_and_fetch_latest_email(app_password, subject_filter)
    if msg:
        email_body = extract_email_body(msg)
        print("Email fetched successfully.")

        # Extract the event information from the email body using LLaMA API
        all_events = extract_event_info_using_llama(email_body)
        print(all_events)

        if all_events:  # Ensure data exists
            try:
                # Generate a timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"extracted_events_{timestamp}.json"

                # Get current directory
                curr_dir = os.path.dirname(os.path.abspath(__file__))

                # Define the relative path to the json_outputs directory
                output_dir = os.path.join(curr_dir, "json_outputs")

                # Ensure the directory exists
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # Save the modified events data to a JSON file
                save_to_json_file(all_events, filename, output_dir)

                print(f"Events saved successfully to {filename}.")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
        else:
            print("No event data extracted or extraction failed.")
    else:
        print("No emails found or login failed.")
