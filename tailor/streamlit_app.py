import streamlit as st
import requests

st.title("📅 TailorTalk – Booking Assistant")

# Conversation state
if "messages" not in st.session_state:
    st.session_state.messages = []

# User input field
user_input = st.text_input("You:", "")

# Send button to trigger backend
if st.button("Send") and user_input:
    st.session_state.messages.append(f"You: {user_input}")
    
    # Send to FastAPI
    res = requests.post("http://localhost:8000/chat/", json={"message": user_input})
    reply = res.json().get("reply")  # match your backend return key

    
    st.session_state.messages.append(f"Agent: {reply}")

# Show message history
for msg in st.session_state.messages:
    st.write(msg)
