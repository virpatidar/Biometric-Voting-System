from fastapi import FastAPI
from pydantic import BaseModel
from langgraph_agent import handle_booking  # your actual booking logic

app = FastAPI()

class Message(BaseModel):
    message: str

@app.post("/chat/")
def chat(message: Message):
    response = handle_booking(message.message)
    return {"response": response}
