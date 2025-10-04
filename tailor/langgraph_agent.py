from datetime import datetime, timedelta
from calendar_utils import check_availability, create_event

def parse_input(user_input):
    # Simple keyword-based time parsing (for example purposes)
    now = datetime.now()
    if "tomorrow" in user_input:
        return now + timedelta(days=1), now + timedelta(days=1, hours=1)
    elif "next week" in user_input:
        return now + timedelta(days=7), now + timedelta(days=7, hours=1)
    elif "this Friday" in user_input:
        days_ahead = (4 - now.weekday()) % 7
        return now + timedelta(days=days_ahead), now + timedelta(days=days_ahead, hours=1)
    else:
        return now + timedelta(hours=1), now + timedelta(hours=2)  # default

def handle_booking(user_input):
    start, end = parse_input(user_input)
    if check_availability(start, end):
        create_event(start, end)
        return f"✅ Booked your appointment on {start.strftime('%A %I:%M %p')}."
    else:
        return "❌ Sorry, that time is not available. Try another slot?"
    
user_input = "Book me an appointment tomorrow"
start, end = parse_input(user_input)
print("User input:", user_input)
print("Start:", start, "End:", end)

