from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Load service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build Calendar API
service = build('calendar', 'v3', credentials=credentials)
calendar_id = 'primary'

# Define a test time slot
start_time = datetime.utcnow() + timedelta(hours=1)
end_time = start_time + timedelta(hours=1)

# Check for existing events
events = service.events().list(
    calendarId=calendar_id,
    timeMin=start_time.isoformat() + 'Z',
    timeMax=end_time.isoformat() + 'Z',
    singleEvents=True,
    orderBy='startTime'
).execute()

# Create event if slot is free
if not events['items']:
    event = {
        'summary': 'Test Booking from TailorTalk',
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'}
    }
    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    print("✅ Booking successful:", created['htmlLink'])
else:
    print("❌ Time slot is already booked.")
