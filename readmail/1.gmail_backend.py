import os
import time
import base64
import requests  # For making POST requests to our meeting APIs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError  # For handling Gmail API errors

# Use the Gmail read-only scope.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    # --- Authentication ---
    creds = None
    # token.json stores your access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials, run the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Request offline access and force the consent prompt.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        # Save the credentials for future runs.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # --- Build the Gmail API service ---
    service = build('gmail', 'v1', credentials=creds)

    # --- Get the current historyId from your profile ---
    profile = service.users().getProfile(userId='me').execute()
    last_history_id = profile.get('historyId')
    print("Monitoring new messages starting from historyId:", last_history_id)

    # --- Continuously poll for new messages ---
    while True:
        try:
            # Request history records for messages added since last_history_id.
            response = service.users().history().list(
                userId='me', 
                startHistoryId=last_history_id,
                historyTypes=['messageAdded']
            ).execute()
            
            history_records = response.get('history', [])
            if history_records:
                for record in history_records:
                    if 'messagesAdded' in record:
                        for added in record['messagesAdded']:
                            message = added.get('message')
                            # Wrap message retrieval in a try/except block.
                            try:
                                msg = service.users().messages().get(
                                    userId='me', id=message['id'], format='full'
                                ).execute()
                                print_message_details(msg)
                            except HttpError as error:
                                if error.resp.status == 404:
                                    print(f"Message with id {message['id']} not found, skipping.")
                                    continue  # Skip to the next message
                                else:
                                    print("Error retrieving message:", error)
            # Update last_history_id to the most recent value returned.
            last_history_id = response.get('historyId', last_history_id)
        except Exception as e:
            print("Error retrieving history:", e)
            # If error indicates the historyId is too old or invalid, reset it.
            if "historyId" in str(e):
                profile = service.users().getProfile(userId='me').execute()
                last_history_id = profile.get('historyId')
                print("Resetting historyId to:", last_history_id)
        # Poll every 5 seconds (adjust as needed).
        time.sleep(5)

def print_message_details(msg):
    """
    Extracts key details from a Gmail message, prints them,
    checks whether the email is a meeting request, and if so,
    gets the meeting time details and schedules the meeting.
    """
    headers = msg['payload'].get('headers', [])
    subject = sender = receiver = ''
    for header in headers:
        header_name = header.get('name', '').lower()
        if header_name == 'subject':
            subject = header.get('value', '')
        elif header_name == 'from':
            sender = header.get('value', '')
        elif header_name == 'to':
            receiver = header.get('value', '')
    
    body = get_message_body(msg.get('payload'))
    # Build a string that contains all the email details.
    email_content = (
        f"Message ID: {msg.get('id')}\n"
        f"Subject: {subject}\n"
        f"From: {sender}\n"
        f"To: {receiver}\n"
        f"Body:\n{body}"
    )
    
    # Print the email details.
    print("\n" + email_content)
    print("-" * 50)

    # --- Check if the email is a meeting request ---
    try:
        # Send the email content to the meeting-or-not API.
        meeting_check_payload = {"email": email_content}
        meeting_check_response = requests.post(
            "https://spitparserapi.onrender.com/response/meetingornot",
            json=meeting_check_payload,
            timeout=10
        )
        meeting_check_response.raise_for_status()  # Raise exception for bad HTTP codes

        # Debug prints (optional)
        print("Meeting check response:", meeting_check_response.text)
        print("Lowercase stripped response:", meeting_check_response.text.strip().lower())

        # Check if the response indicates "yes"
        if meeting_check_response.text.strip().lower() in ['"yes"', 'yes']:
            # Get meeting time details from the meetingTime API.
            meeting_time_payload = {"email_body": email_content}
            meeting_time_response = requests.post(
                "https://spitparserapi.onrender.com/response/meetingTime",
                json=meeting_time_payload,
                timeout=10
            )
            meeting_time_response.raise_for_status()
            # Parse the meeting time response to be used as the scheduling payload.
            schedule_payload = meeting_time_response.json()
            print("Meeting time response (used for scheduling):", schedule_payload)
            
            # Now, call the scheduling endpoint with the dynamic payload.
            schedule_response = requests.post(
                "http://localhost:3000/api/meetings",
                json=schedule_payload,
                timeout=10
            )
            schedule_response.raise_for_status()
            print("Meeting scheduled successfully:", schedule_response.text)
    except requests.exceptions.RequestException as req_err:
        print("HTTP error during meeting check/time/scheduling request:", req_err)
    except Exception as e:
        print("Error processing meeting check/time/scheduling:", e)

def get_message_body(payload):
    """
    Recursively extracts the plain text body from the message payload.
    Gmail messages can be multipart; this function decodes the base64url encoded data.
    """
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            # If the part is multipart, recursively extract its text parts.
            if part.get('mimeType', '').startswith('multipart'):
                body += get_message_body(part)
            elif part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    try:
                        text = base64.urlsafe_b64decode(data).decode('utf-8')
                        body += text
                    except Exception as decode_error:
                        print("Error decoding part:", decode_error)
    else:
        # For a single-part message.
        data = payload.get('body', {}).get('data')
        if data:
            try:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
            except Exception as decode_error:
                print("Error decoding message body:", decode_error)
    return body

if __name__ == '__main__':
    main()
