# IVR
A FastAPI-based IVR simulation system that allows users to interact using chat, voice, and DTMF keypad, similar to real IRCTC services.
## Features
Ticket booking flow
PNR status check
Train schedule lookup
Ticket cancellation
Chat + DTMF interaction
Voice input & Text-to-Speech
Debug panel for state tracking
## Tech Stack
Backend: FastAPI, Uvicorn
Frontend: HTML, CSS, JavaScript
Voice: Web Speech API, gTTS
Logic: State Machine
## Project Structure
main.py
state_machine.py
models.py
test_full_flow.py
requirements.txt
runtime.txt
templates/index.html
static/script.js
static/style.css
## Setup
pip install -r requirements.txt
python main.py
Open: http://127.0.0.1:8011
## Deployment (Render)
Build: pip install -r requirements.txt
Start: python main.py
