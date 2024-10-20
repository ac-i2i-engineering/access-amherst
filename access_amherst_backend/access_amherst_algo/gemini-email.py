import imaplib
import email
from email.header import decode_header
import getpass
import re
import pandas as pd
import os
import google.generativeai as genai  # Import for Gemini API

# Configure Gemini API with API key
genai.configure(api_key="AIzaSyCOpooOQrEw7rALcxmhlmKybagFKhGdL2E")  # Replace with your Gemini API key

# Function to connect to Gmail and get emails
def connect_and_fetch_emails(app_password, sender_email, mail_server="imap.gmail.com"):
    # Connect to Gmail's IMAP server
    mail = imaplib.IMAP4_SSL(mail_server)
    
    try:
        # Log in using the app-specific password
        mail.login("accessamherst@gmail.com", app_password)
        print("Logged in successfully")
    except imaplib.IMAP4.error as e:
        print(f"Login failed: {e}")
        return None

    # Select the inbox
    mail.select("inbox")
    
    # Search for emails from a sender
    status, messages = mail.search(None, f'(FROM "{sender_email}")')
    
    if status != "OK":
        print(f"Failed to fetch emails: {status}")
        return None

    # Fetch the most recent email from the sender
    for msg_num in messages[0].split()[-1:]:  # Fetch only the latest message
        res, msg = mail.fetch(msg_num, "(RFC822)")
        for response_part in msg:
            if isinstance(response_part, tuple):
                # Parse the email
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

# Function to extract event information using Gemini API
def extract_event_info_using_gemini(email_content):
    # Simplified prompt
    prompt = f"""
    Extract the event details from the following email content:

    {email_content}

    Please provide the following information:
    - Event Name
    - Event Date
    - Event Time
    - Event Location
    """

    # Use Gemini API to generate the response
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Debug: Print the full response for inspection
    print("Full Gemini API Response:\n", response)

    # Extracting the generated content from the response
    if 'candidates' in response and len(response.candidates) > 0:
        return response.candidates[0].content.parts[0].text
    else:
        return "No response generated."

# Function to save event details to a CSV file
def save_events_to_csv(events, filename='event_details.csv'):
    df = pd.DataFrame(events, columns=["Event Name", "Date", "Time", "Location"])
    df.to_csv(filename, index=False)
    print(f"Saved events to {filename}")

# Function to parse the extracted events from the API response
def parse_extracted_events(extracted_events):
    events = []
    lines = extracted_events.splitlines()
    event = {}
    
    for line in lines:
        if "Event Name:" in line:
            if event:  # If the event dictionary has already been filled, save it
                events.append(event)
                event = {}
            event["Event Name"] = line.split(":", 1)[1].strip()
        elif "Event Date:" in line:
            event["Date"] = line.split(":", 1)[1].strip()
        elif "Event Time:" in line:
            event["Time"] = line.split(":", 1)[1].strip()
        elif "Event Location:" in line:
            event["Location"] = line.split(":", 1)[1].strip()

    if event:  # Add the last event if there are any remaining details
        events.append(event)

    return events

# Main function to run the process
def main():
    # Gmail account credentials
    app_password = getpass.getpass("Enter your Gmail App-Specific Password: ")
    sender_email = "shegde26@amherst.edu"  # The email you want to filter by

    # Fetch the email from Gmail
    msg = connect_and_fetch_emails(app_password, sender_email)

    if msg:
        # Extract the email body
        email_body = extract_email_body(msg)
        print("Email fetched successfully.")
        print("Email content being sent to Gemini API:\n", email_body)  # Debug: Print the email content
        
        # Send the email content to Gemini API for event extraction
        extracted_events = extract_event_info_using_gemini(email_body)
        print("Extracted event details:\n", extracted_events)
        
        # Parse the extracted event details into a structured format
        event_data = parse_extracted_events(extracted_events)
        
        # Save the parsed events to a CSV file
        save_events_to_csv(event_data)
    else:
        print("No emails found or login failed.")

if __name__ == "__main__":
    main()
