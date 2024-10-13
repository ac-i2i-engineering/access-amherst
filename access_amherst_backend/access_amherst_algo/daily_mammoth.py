import imaplib
import email
from email.header import decode_header
import getpass
import re
import pandas as pd

# Function to connect to Gmail and fetch emails
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

    # Select the inbox (or any other mailbox)
    mail.select("inbox")
    
    # Search for emails from a specific sender
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

# Function to extract and parse event details from the email body
def parse_event_details(email_body):
    events = []
    lines = email_body.splitlines()
    
    # Pattern to identify date lines (including day and month forms)
    date_pattern = r'(?i)\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?\b|\b(?:Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Sep(?:tember)?|Aug(?:ust)?|Jul(?:y)?|Jun(?:e)?|May|Apr(?:il)?|Mar(?:ch)?|Feb(?:ruary)?|Jan(?:uary)?)\s+\d{1,2}\b|\b\d{1,2}\s+(?:Oct|Nov|Dec|Sep|Aug|Jul|Jun|May|Apr|Mar|Feb|Jan)\b'
    
    # Pattern to identify time and location on the same line
    time_pattern = r'\b\d{1,2}:\d{2}\s?(?:AM|PM)\b|\b\d{1,2}\s?(?:AM|PM)\b'
    location_pattern = r'\b(Science Center|WGC|Frost Library|Drake|Valentine Hall|Porter House|CHI Think Tank|Webster Hall)\b'
    
    # Iterate over lines and search for dates, times, and locations
    for i in range(1, len(lines)):
        line = lines[i].strip()

        # Check if the current line has a date
        if re.search(date_pattern, line):
            # Extract time from the same line
            time_match = re.search(time_pattern, line)
            event_time = time_match.group(0) if time_match else "N/A"

            # Extract location from the same line
            location_match = re.search(location_pattern, line)
            event_location = location_match.group(0) if location_match else "N/A"

            # Get the event name from the line before the date line
            event_name = lines[i - 1].strip() if i - 1 >= 0 else "N/A"

            # Append event details
            events.append([event_name, line, event_time, event_location])

    return events

# Function to extract the email body
def extract_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode('utf-8')
    else:
        return msg.get_payload(decode=True).decode('utf-8')

# Function to save event details to a CSV file
def save_events_to_csv(events, filename='event_details.csv'):
    df = pd.DataFrame(events, columns=["Event Name", "Date", "Time", "Location"])
    df.to_csv(filename, index=False)
    print(f"Saved events to {filename}")

# Main function to run the process
def main():
    # Gmail account credentials
    app_password = getpass.getpass("Enter your Gmail App-Specific Password: ")
    sender_email = "shegde26@amherst.edu"  # The email you want to filter by

    # Fetch the email
    msg = connect_and_fetch_emails(app_password, sender_email)
    
    if msg:
        # Extract the email body
        email_body = extract_email_body(msg)
        print("Email fetched successfully.")
        
        # Parse event details from the email body
        events = parse_event_details(email_body)
        
        # Save the parsed events to a CSV file
        save_events_to_csv(events)
    else:
        print("No emails found or login failed.")

if __name__ == "__main__":
    main()
