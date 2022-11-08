import os.path
import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def fetch_calendar_events(number_of_events):
    """
    Fetches the events from the calendar.
    Used Google's CalendarAPI for this task.
    https://developers.google.com/calendar/api
    """
    creds = None
    # The file cal_token.json contains the user's access and refresh tokens
    if os.path.exists('cal_token.json'):
        creds = Credentials.from_authorized_user_file('cal_token.json', CALENDAR_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('cal_token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=number_of_events, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        return events

    except HttpError as error:
        print('An error occurred: %s' % error)
