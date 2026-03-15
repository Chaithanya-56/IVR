"""
IRCTC IVR FastAPI Implementation
-----------------------------------------
1. FastAPI based IVR backend
2. Welcome prompt handling
3. Menu handling (single digit input)
4. Multi-digit input handling using buffer
5. JSON response structure
6. Session management
7. Basic workflow logging


"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import random
import logging

# ---------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------

app = FastAPI()

# Enable CORS (allows browser-based simulator to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable logging for workflow tracking
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
# Request Models (Incoming JSON Structure)
# ---------------------------------------------------------

class StartCallRequest(BaseModel):
    # Represents call initiation request
    caller_number: str = "Simulator"

class InputRequest(BaseModel):
    # Represents DTMF input from user
    session_id: str
    digit: str

# ---------------------------------------------------------
# Session Class – Maintains Call State
# ---------------------------------------------------------

class CallSession:
    """
    Each call creates a session object.
    It stores:
    - session_id
    - current menu
    - multi-digit input buffer
    - call history
    - call active status
    """

    def __init__(self, session_id, caller_number):
        self.session_id = session_id
        self.caller_number = caller_number
        self.current_menu = "main"
        self.input_buffer = ""
        self.call_history = []
        self.start_time = datetime.now()
        self.active = True

# Global session storage
sessions = {}

# ---------------------------------------------------------
# IVR Menu Configuration (State Machine Definition)
# ---------------------------------------------------------

MENUS = {

    # MAIN MENU (Single digit menu handling)
    "main": {
        "prompt": "Welcome to IRCTC. Press 1 to Book Ticket, 2 for PNR Status, 9 to Talk to Agent.",
        "type": "menu",  # menu = single digit routing
        "options": {
            "1": "booking_source",
            "2": "pnr_input",
            "9": "transfer_agent"
        }
    },

    # BOOKING SOURCE (Multi-digit input state)
    "booking_source": {
        "prompt": "Enter source station code followed by #.",
        "type": "input"  # input = multi-digit collection
    },

    # BOOKING DESTINATION (Multi-digit input state)
    "booking_destination": {
        "prompt": "Enter destination station code followed by #.",
        "type": "input"
    },

    # PNR INPUT (Multi-digit input state)
    "pnr_input": {
        "prompt": "Enter 10 digit PNR followed by #.",
        "type": "input"
    }
}

# ---------------------------------------------------------
# START CALL ENDPOINT
# ---------------------------------------------------------

@app.post("/ivr/start")
def start_call(request: StartCallRequest):
    """
    Workflow:
    1. Generate new session ID
    2. Create CallSession object
    3. Store session
    4. Return welcome prompt as JSON
    """

    session_id = f"SIM_{random.randint(100000,999999)}"
    session = CallSession(session_id, request.caller_number)
    sessions[session_id] = session

    logging.info(f"Call started: {session_id}")

    return {
        "session_id": session_id,
        "prompt": MENUS["main"]["prompt"]
    }

# ---------------------------------------------------------
# HANDLE USER INPUT ENDPOINT
# ---------------------------------------------------------

@app.post("/ivr/input")
def handle_input(request: InputRequest):

    """
    Workflow:
    1. Identify session using session_id
    2. Determine current menu state
    3. If menu type -> single digit routing
    4. If input type -> collect multi-digit until '#'
    5. Return JSON response
    """

    session = sessions.get(request.session_id)

    # If session does not exist
    if not session:
        return {"error": "Session not found"}

    digit = request.digit

    # Store input in call history
    session.call_history.append({
        "time": str(datetime.now()),
        "menu": session.current_menu,
        "input": digit
    })

    logging.info(f"Session {session.session_id} | Menu: {session.current_menu} | Input: {digit}")

    current_menu = MENUS.get(session.current_menu)

    # -----------------------------------------------------
    # CASE 1: MENU TYPE (Single Digit Handling)
    # -----------------------------------------------------

    if current_menu["type"] == "menu":

        if digit in current_menu["options"]:
            next_menu = current_menu["options"][digit]

            # Transfer handling
            if next_menu == "transfer_agent":
                session.active = False
                return {
                    "action": "hangup",
                    "message": "Transferring to customer support agent..."
                }

            # Move to next state
            session.current_menu = next_menu
            session.input_buffer = ""

            return {
                "prompt": MENUS[next_menu]["prompt"]
            }

        else:
            # Invalid option handling
            return {"prompt": "Invalid option. Please try again."}

    # -----------------------------------------------------
    # CASE 2: INPUT TYPE (Multi-Digit Handling)
    # -----------------------------------------------------

    elif current_menu["type"] == "input":

        # If user presses '#' -> end of multi-digit input
        if digit == "#":

            user_input = session.input_buffer

            # PNR FLOW
            if session.current_menu == "pnr_input":
                session.active = False
                return {
                    "action": "hangup",
                    "message": f"PNR {user_input} is Confirmed. Thank you for calling IRCTC."
                }

            # BOOKING SOURCE FLOW
            elif session.current_menu == "booking_source":
                session.current_menu = "booking_destination"
                session.input_buffer = ""
                return {
                    "prompt": "Enter destination station code followed by #."
                }

            # BOOKING DESTINATION FLOW
            elif session.current_menu == "booking_destination":
                session.active = False
                return {
                    "action": "hangup",
                    "message": f"Ticket booking request from source to {user_input} submitted successfully."
                }

        else:
            # Collect digits in buffer
            session.input_buffer += digit

            return {
                "prompt": f"Entered: {session.input_buffer}"
            }

# ---------------------------------------------------------
# OPTIONAL: VIEW CALL HISTORY
# ---------------------------------------------------------

@app.get("/ivr/history/{session_id}")
def get_history(session_id: str):
    """
    Returns stored call history for debugging/testing.
    """

    session = sessions.get(session_id)

    if session:
        return session.call_history

    return {"error": "Session not found"}



"""
Detailed Call Flow Architecture
    Start Call
        ↓
    State = main
        ↓
    User presses 1
        ↓
    State → booking_source
        ↓
    User enters 500#
        ↓
    Buffer collects digits
        ↓
    State → booking_destination
        ↓
    User enters 700#
        ↓
    Call ends
"""
"""
  
                 FRONTEND                       
 (index.html - Browser IVR UI)                 

 - Start Call Button                           
 - Keypad (0-9, #)                             
 - Display Screen                              
 - JavaScript State Handling                   
+--------------------------------------------------+
                     |
                     | HTTP (Fetch API)
                     v
+--------------------------------------------------+
                 BACKEND                        
             (FastAPI - main.py)               

 1. /ivr/start                                 
 2. /ivr/input                                 
 3. Session Management                         
 4. Menu Engine (State Machine)                
 5. Multi-Digit Input Buffer                   
 6. Call History Logging                       
+--------------------------------------------------+
                     |
                     v
+--------------------------------------------------+
              SESSION OBJECT                      

  - session_id                                   
  - current_menu                                 
  - input_buffer                                 
  - call_history                                 
  - active flag                                  

"""
