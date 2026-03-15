from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from session import get_session
from flow import handle_flow

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    session_id: str
    text: str


@app.post("/chat")
def chat(msg: Message):

    session = get_session(msg.session_id)

    reply = handle_flow(session, msg.text)

    return {
        "reply": reply,
        "debug": session
    }