import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from models import EntityExtraction

class StateMachine:
    def __init__(self):
        # session_id -> {state, history, entities, last_intent, dtmf_buffer, source, destination}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # mock PNR database
        self.pnr_db: Dict[str, str] = {}
        
        self.STATES = {
            "MAIN_MENU": "MAIN_MENU",
            "ASK_SOURCE": "ASK_SOURCE",
            "ASK_DESTINATION": "ASK_DESTINATION",
            "DATE_SELECTION": "DATE_SELECTION",
            "TRAIN_SELECTION": "TRAIN_SELECTION",
            "CLASS_SELECTION": "CLASS_SELECTION",
            "CONFIRM_BOOKING": "CONFIRM_BOOKING",
            "PNR_STATUS": "PNR_STATUS",
            "CANCEL_TICKET": "CANCEL_TICKET",
            "SCHEDULE_TRAIN_NUMBER_INPUT": "SCHEDULE_TRAIN_NUMBER_INPUT"
        }

        # CONSOLIDATED TRAIN DATA (Source of Truth)
        self.TRAIN_DATA = {
            "12424": {"name": "Rajdhani Express", "source": "Delhi", "destination": "Mumbai", "time": "10:00 AM"},
            "12004": {"name": "Shatabdi Express", "source": "Hyderabad", "destination": "Chennai", "time": "6:00 AM"},
            "12260": {"name": "Duronto Express", "source": "Hyderabad", "destination": "Chennai", "time": "8:00 PM"},
            "12050": {"name": "Gatimaan Express", "source": "Delhi", "destination": "Agra", "time": "9:00 AM"}
        }

        # Legacy compatibility for booking flow
        self.MOCK_TRAINS = [
            {"no": k, "name": v["name"], "time": v["time"]} for k, v in self.TRAIN_DATA.items()
        ]

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "state": self.STATES["MAIN_MENU"],
                "history": [],
                "entities": EntityExtraction(),
                "last_intent": "unknown",
                "confidence": 0.0,
                "dtmf_buffer": "",
                "source": None,       # ROOT SESSION STORAGE
                "destination": None   # ROOT SESSION STORAGE
            }
        return self.sessions[session_id]

    def _calculate_next_monday(self) -> datetime.date:
        today = datetime.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0: days_ahead += 7
        return today + timedelta(days=days_ahead)

    def _parse_date(self, text: str) -> Optional[str]:
        today = datetime.now().date()
        target_date = None
        text = text.lower().strip()
        if text == "1" or "today" in text: target_date = today
        elif text == "2" or "tomorrow" in text: target_date = today + timedelta(days=1)
        elif text == "3" or "next monday" in text: target_date = self._calculate_next_monday()
        if not target_date:
            digits_only = re.sub(r'\D', '', text)
            if len(digits_only) == 8:
                try:
                    day, month, year = int(digits_only[0:2]), int(digits_only[2:4]), int(digits_only[4:8])
                    target_date = datetime(year, month, day).date()
                except ValueError: return "INVALID_FORMAT"
            match = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', text)
            if match:
                try:
                    day, month, year = map(int, match.groups())
                    target_date = datetime(year, month, day).date()
                except ValueError: return "INVALID_FORMAT"
        if target_date:
            end_of_year = datetime(today.year, 12, 31).date()
            if target_date < today: return "PAST_DATE"
            if target_date > end_of_year: return "OUT_OF_RANGE"
            return target_date.strftime("%d-%m-%Y")
        return None

    def detect_intent(self, text: str) -> tuple[str, float]:
        text = text.lower().strip()
        button_map = {
            "book ticket": "booking",
            "pnr status": "pnr_status",
            "train schedule": "train_schedule",
            "cancel ticket": "cancel_ticket"
        }
        if text in button_map: return button_map[text], 1.0
        if any(kw in text for kw in ["schedule", "time", "timetable"]): return "train_schedule", 0.95
        if any(kw in text for kw in ["pnr", "status"]): return "pnr_status", 0.98
        if any(kw in text for kw in ["cancel", "radd", "refund"]): return "cancel_ticket", 0.95
        if any(kw in text for kw in ["book", "ticket", "reserve"]): return "booking", 0.95
        if any(kw in text for kw in ["menu", "home", "start"]): return "main_menu", 0.85
        return "unknown", 0.3

    def extract_entities(self, text: str, session: Dict[str, Any]) -> EntityExtraction:
        cities = ["delhi", "mumbai", "chennai", "kolkata", "bangalore", "pune", "hyderabad", "lucknow", "patna", "secunderabad", "agra", "jaipur"]
        text_lower = text.lower().replace(",", " ").replace(".", " ")
        entities = session["entities"]
        curr_state = session["state"]

        # 1. Handle "X to Y" pattern (FORCE UPDATE ROOT)
        to_pattern = re.search(r'(\w+)\s+(?:to|till|for)\s+(\w+)', text_lower)
        if to_pattern:
            src, dest = to_pattern.groups()
            if src in cities: 
                session["source"] = src.capitalize()
                entities.source = src.capitalize()
                print(f"[SERVER] FORCE UPDATE Source (pattern): {session['source']}")
            if dest in cities: 
                session["destination"] = dest.capitalize()
                entities.destination = dest.capitalize()
                print(f"[SERVER] FORCE UPDATE Destination (pattern): {session['destination']}")

        # 2. General word-based extraction (FORCE OVERWRITE ROOT)
        words = text_lower.split()
        for word in words:
            if word in cities:
                city = word.capitalize()
                if curr_state == "ASK_SOURCE":
                    session["source"] = city
                    entities.source = city
                    print(f"[SERVER] FORCE UPDATE Source (state): {city}")
                elif curr_state == "ASK_DESTINATION":
                    session["destination"] = city
                    entities.destination = city
                    print(f"[SERVER] FORCE UPDATE Destination (state): {city}")
                else:
                    if not session["source"]:
                        session["source"] = city
                        entities.source = city
                    elif not session["destination"] and city != session["source"]:
                        session["destination"] = city
                        entities.destination = city
            
            classes = {"1a": "First Class (1A)", "2a": "AC 2 Tier (2A)", "sl": "Sleeper (SL)"}
            if word in classes: entities.train_class = classes[word]
        
        train_match = re.search(r'\b\d{5}\b', text)
        if train_match: entities.train_no = train_match.group(0)
            
        return entities

    def process_input(self, session_id: str, text: str, is_dtmf: bool = False) -> Dict[str, Any]:
        session = self.get_session(session_id)
        
        if text.strip():
            session["history"].append({"role": "user", "content": text})
        
        intent, confidence = self.detect_intent(text)
        
        # CLEAR OLD DATA ON NEW BOOKING (MANDATORY)
        if intent == "booking" and session["state"] == self.STATES["MAIN_MENU"]:
            print("[SERVER] Detected new booking intent. Clearing session data...")
            session["source"] = None
            session["destination"] = None
            session["entities"] = EntityExtraction()
        
        # EXTRACT ENTITIES (Update root session storage)
        if text.strip(): 
            session["entities"] = self.extract_entities(text, session)

        # DEBUG LOG (MANDATORY REQUIREMENT)
        print("\n" + "="*30)
        print(f"Session ID: {session_id}")
        print(f"Source: {session['source']}")
        print(f"Destination: {session['destination']}")
        print(f"Current State: {session['state']}")
        print("="*30 + "\n")
        
        if is_dtmf:
            return self._handle_dtmf(session, text)

        if intent == "main_menu" or text.lower() in ["0", "menu", "home"]:
            session["state"] = self.STATES["MAIN_MENU"]
            session["last_intent"] = "main_menu"
            response_text = "Main Menu. Press 1 for Booking, 2 for PNR Status, 3 for Schedule, 4 for Cancellation."
            session["history"].append({"role": "system", "content": response_text})
            return self._format_response(session, response_text)

        if confidence > 0.9:
            session["last_intent"] = intent
            session["confidence"] = confidence
        
        response_text = ""
        curr_state = session["state"]

        if curr_state == self.STATES["MAIN_MENU"]:
            if intent == "train_schedule":
                print("[SERVER] Starting Schedule Flow")
                session["state"] = self.STATES["SCHEDULE_TRAIN_NUMBER_INPUT"]
                if session["entities"].train_no:
                    return self.process_input(session_id, session["entities"].train_no)
                return self.process_input(session_id, "")
            elif intent == "booking":
                session["state"] = self.STATES["ASK_SOURCE"]
                return self.process_input(session_id, "")
            elif intent == "pnr_status":
                session["state"] = self.STATES["PNR_STATUS"]
                return self.process_input(session_id, "")
            elif intent == "cancel_ticket":
                session["state"] = self.STATES["CANCEL_TICKET"]
                return self.process_input(session_id, "")
            else:
                response_text = "Welcome to IRCTC. Press 1 to Book, 2 for PNR, 3 for Schedule, 4 to Cancel."

        elif curr_state == self.STATES["SCHEDULE_TRAIN_NUMBER_INPUT"]:
            train_no = str(re.sub(r'\D', '', text)).strip()
            if not train_no and session["entities"].train_no:
                train_no = session["entities"].train_no

            print(f"[SERVER] Schedule Lookup - Raw: '{text}', Cleaned: '{train_no}'")
            
            if train_no in self.TRAIN_DATA:
                data = self.TRAIN_DATA[train_no]
                print(f"[SERVER] Success! Found {data['name']}")
                
                # ACCESS ROOT SESSION DATA (MANDATORY)
                source = session.get("source")
                destination = session.get("destination")
                
                # PRIORITY LOGIC (MANDATORY)
                final_source = source if source else data['source']
                final_destination = destination if destination else data['destination']
                
                response_text = f"Train {train_no} ({data['name']}) runs from {final_source} to {final_destination} at {data['time']}. Press 0 for Main Menu."
                
                session["entities"].selected_train = f"{data['name']} ({train_no})"
                session["entities"].source = final_source
                session["entities"].destination = final_destination
                session["state"] = self.STATES["MAIN_MENU"]
            elif text or train_no:
                response_text = f"Sorry, no schedule found for train {train_no if train_no else text}. Please enter a valid 5-digit train number."
            else:
                response_text = "Please enter the 5-digit train number to check its schedule."

        elif curr_state == self.STATES["ASK_SOURCE"]:
            if session["source"]:
                session["state"] = self.STATES["ASK_DESTINATION"]
                return self.process_input(session_id, "")
            response_text = "Please enter source city (e.g., Bangalore)."
        
        elif curr_state == self.STATES["ASK_DESTINATION"]:
            if session["destination"]:
                if session["last_intent"] == "booking":
                    session["state"] = self.STATES["DATE_SELECTION"]
                return self.process_input(session_id, "")
            response_text = f"Going from {session['source']}. Enter destination city (e.g., Pune)."

        elif curr_state == self.STATES["DATE_SELECTION"]:
            date_val = self._parse_date(text)
            if date_val in ["PAST_DATE", "OUT_OF_RANGE", "INVALID_FORMAT"]:
                if date_val == "PAST_DATE": response_text = "The date you entered is in the past. Please select a future date."
                elif date_val == "OUT_OF_RANGE": response_text = "Booking is only allowed up to 31st December 2026."
                else: response_text = "Invalid date format. Please enter DDMMYYYY format."
            elif date_val:
                session["entities"].date = date_val
                session["state"] = self.STATES["TRAIN_SELECTION"]
                return self.process_input(session_id, "")
            else:
                response_text = "On which date would you like to travel? \n1. Today, 2. Tomorrow, 3. Next Monday, 4. Custom."

        elif curr_state == self.STATES["TRAIN_SELECTION"]:
            if text in ["1", "2", "3", "4"]:
                idx = int(text) - 1
                session["entities"].selected_train = self.MOCK_TRAINS[idx]["name"]
                session["state"] = self.STATES["CLASS_SELECTION"]
                return self.process_input(session_id, "")
            trains = "\n".join([f"{i+1}. {t['name']} ({t['no']})" for i, t in enumerate(self.MOCK_TRAINS)])
            response_text = f"Trains from {session['source']} to {session['destination']}:\n{trains}\nSelect 1-4."

        elif curr_state == self.STATES["CLASS_SELECTION"]:
            classes = {"1": "First Class (1A)", "2": "AC 2 Tier (2A)", "3": "Sleeper (SL)"}
            if text in classes:
                session["entities"].train_class = classes[text]
                session["state"] = self.STATES["CONFIRM_BOOKING"]
                return self.process_input(session_id, "")
            response_text = "Select Class:\n1. 1A, 2. 2A, 3. SL"

        elif curr_state == self.STATES["CONFIRM_BOOKING"]:
            pnr = "".join([str(random.randint(0,9)) for _ in range(10)])
            self.pnr_db[pnr] = "Confirmed"
            response_text = f"Booking Successful! {session['entities'].selected_train} on {session['entities'].date}. PNR: {pnr}. Press 0 for Main Menu."
            session["state"] = self.STATES["MAIN_MENU"]

        elif curr_state == self.STATES["PNR_STATUS"] or curr_state == self.STATES["CANCEL_TICKET"]:
            if re.match(r'^\d{10}$', text):
                status = self.pnr_db.get(text, "Confirmed (CNF)") if curr_state == self.STATES["PNR_STATUS"] else "Cancelled"
                if curr_state == self.STATES["CANCEL_TICKET"]: self.pnr_db[text] = "Cancelled"
                response_text = f"PNR {text} Status: {status}."
                session["state"] = self.STATES["MAIN_MENU"]
            else:
                response_text = "Please enter 10-digit PNR followed by #."

        if not response_text: response_text = "I'm sorry, I didn't understand that. Press 0 for Main Menu."
        session["history"].append({"role": "system", "content": response_text})
        
        self.sessions[session_id] = session
        return self._format_response(session, response_text)

    def _handle_dtmf(self, session: Dict[str, Any], digits: str) -> Dict[str, Any]:
        curr_state = session["state"]
        print(f"[SERVER] DTMF Input: '{digits}' | State: {curr_state}")
        if curr_state == self.STATES["MAIN_MENU"]:
            if digits == "1":
                session["state"] = self.STATES["ASK_SOURCE"]
                session["last_intent"] = "booking"
                session["source"] = None
                session["destination"] = None
                session["entities"] = EntityExtraction()
                return self.process_input(session["session_id"], "")
            elif digits == "2":
                session["state"] = self.STATES["PNR_STATUS"]
                session["last_intent"] = "pnr_status"
                return self.process_input(session["session_id"], "")
            elif digits == "3":
                session["state"] = self.STATES["SCHEDULE_TRAIN_NUMBER_INPUT"]
                session["last_intent"] = "train_schedule"
                return self.process_input(session["session_id"], "")
            elif digits == "4":
                session["state"] = self.STATES["CANCEL_TICKET"]
                session["last_intent"] = "cancel_ticket"
                return self.process_input(session_id=session["session_id"], text="")
            elif digits == "0": return self.process_input(session["session_id"], "0")
        if curr_state in [self.STATES["DATE_SELECTION"], self.STATES["TRAIN_SELECTION"], self.STATES["CLASS_SELECTION"]]:
            if len(digits) == 1 and digits in ["1", "2", "3", "4"]: return self.process_input(session["session_id"], digits)
        return self.process_input(session["session_id"], digits)

    def _format_response(self, session: Dict[str, Any], response_text: str) -> Dict[str, Any]:
        # Sync root session data back to entities for the UI
        entities_dict = session["entities"].dict()
        entities_dict["source"] = session["source"]
        entities_dict["destination"] = session["destination"]
        return {"response": response_text, "state": session["state"], "intent": session.get("last_intent", "unknown"), "confidence": session.get("confidence", 1.0), "entities": entities_dict, "history": session["history"], "dtmf_buffer": ""}
