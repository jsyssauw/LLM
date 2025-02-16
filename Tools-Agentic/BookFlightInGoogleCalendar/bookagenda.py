from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import json
import os

def set_event_details(destination,ddate="2025-01-01"):
    l_destination = "Trip to " + str(destination)
    event_details = {
        'summary': l_destination,
        'description': f"Travelling to {destination}",
        'start_time': ddate + 'T10:00:00',
        'end_time': ddate + 'T11:00:00',
        'attendees': ['exqsdmj@gmail.com', 'exssdf2@gmail.com'],
    }
    return event_details

def make_booking(destination = "NA"):
    event_details = set_event_details(destination)
    event = book_meeting(event_details, destination)
    print ("Meeting scheduled successfully:", event['htmlLink']) 

#### this entry is when it's called from the agent MultiAgent.py to make a booking on a specific date.
def make_booking_int(city, ddate, tool_call_id):
    event_details = set_event_details(city,ddate)
    event = book_meeting(event_details, city)
    print ("Meeting scheduled successfully: Trip to " + city + " on " +ddate, event['htmlLink']) 
    response = {
        "role": "tool",
        "content": json.dumps({"destination_city": city,"travel_date": ddate}),
        "tool_call_id": tool_call_id
    }
    return response

# Define a function to book a meeting in Google Calendar
def book_meeting(event_details, destination):
    """
    Schedule a meeting in Google Calendar.

    Args:
        event_details (dict): A dictionary containing event details with keys:
            - 'summary': The title of the event.
            - 'description': A description of the event.
            - 'start_time': Start time in ISO format (e.g., '2025-01-01T10:00:00').
            - 'end_time': End time in ISO format (e.g., '2025-01-01T11:00:00').
            - 'attendees': List of attendees' email addresses.

    Returns:
        dict: Information about the created event.
    """

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def authenticate_google():
        creds = None
        # Check if token.json exists
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no valid credentials, prompt for login
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    # Initialize the Google Calendar API service
    creds = authenticate_google()
    service = build('calendar', 'v3', credentials=creds)
    
    # Create the event body
    event = {
        'summary': event_details['summary'],
        'description': event_details['description'],
        'start': {
            'dateTime': event_details['start_time'],
            'timeZone': 'UTC',  # Change the timezone if needed
        },
        'end': {
            'dateTime': event_details['end_time'],
            'timeZone': 'UTC',  # Change the timezone if needed
        },
        'attendees': [{'email': email} for email in event_details.get('attendees', [])],
    }

    # Add the event to the primary calendar
    created_event = service.events().insert(calendarId='primary', body=event).execute()

    return created_event

# Example usage
#try:
destination = "London"
## make_booking(destination)
#except Exception as e:
#    print("An error occurred:", e)
