import os.path
import base64
from google.auth.transport.requests import Request
from email.message import EmailMessage
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def send_email(subject, content):
    """
    Send email to the predefined receiver.
    Used Google's GmailAPI for this task.
    https://developers.google.com/gmail/api
    """
    creds = None
    # The file gm_token.json contains the user's access and refresh tokens
    if os.path.exists('gm_token.json'):
        creds = Credentials.from_authorized_user_file('gm_token.json', GMAIL_SCOPES)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('gm_token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()
        message['To'] = 'nc2025@hw.ac.uk'
        message['From'] = 'nrj.fake10@gmail.com'
        message['Subject'] = subject
        message.set_content(content)
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'raw': encoded_message
        }
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())

        print('Email sent')
    except HttpError as error:#
        print('An error occurred: %s' % error)
