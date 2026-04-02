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
## LINK: https://irctc-ivr-simulator.onrender.com/
Build: pip install -r requirements.txt
Start: python main.py


## 🚀 How to Use the IRCTC IVR Simulator

### 🟢 1. Start the Application

After running the backend server:

```bash
python main.py
```

Open your browser and go to:

```
http://127.0.0.1:8000
```

OR use the deployed link (if available).

---

### 🟢 2. Choose Interaction Mode

The system provides two modes:

* 💬 **Chat Mode** → Type or speak naturally
* 🔢 **DTMF Mode** → Use keypad (like IVR system)

You can switch between modes using the toggle at the top.

---

### 🟢 3. Booking Flow (Ticket Reservation)

#### Chat Mode:

1. Type: *“Book ticket from Hyderabad to Delhi”*
2. Enter travel date
3. Select train-(type or speak 1 ,2,3,or 4 to select train in chat mode or in dtmf mode)
4. Choose class (1A / 2A / SL)-(type or speak 1 ,2,3,or 4 to select train in chat mode or in dtmf mode)
5. Confirm booking

👉 System returns:

* ✅ Booking confirmation
* 🎫 Generated PNR number

---

#### DTMF Mode:

1. Press **1** → Booking
2. Enter:

   * Source city
   * Destination city
3. Select date:

   * 1 → Today
   * 2 → Tomorrow
   * 3 → Next Monday
   * 4 → Custom date (DDMMYYYY#)
4. Select train (1–4)
5. Select class (1–3)

👉 Booking will be confirmed with PNR.

---

### 🟢 4. PNR Status

#### Chat Mode:

* Type: *“Check PNR status 1234567890”*

#### DTMF Mode:

* Press **2**
* Enter PNR number

👉 System shows:

* Booking status
* Journey details

---

### 🟢 5. Train Schedule

#### Chat Mode:

* Type: *“Train schedule for 12424”*

#### DTMF Mode:

* Press **3**
* Enter train number

👉 System shows:

* Source & destination
* Departure time

---

### 🟢 6. Ticket Cancellation

#### Chat Mode:

* Type: *“Cancel my ticket”*

#### DTMF Mode:

* Press **4**
* Enter PNR number

👉 Ticket will be cancelled.

---

### 🟢 7. Voice Features

* 🎤 Speech-to-Text: Speak instead of typing
* 🔊 Text-to-Speech: System responds with voice automatically

---

### 🟢 8. Debug Panel (Right Side)

Displays:

* Current state
* Detected intent
* Confidence score
* Extracted entities
* Full conversation history

---

## 🧪 Example Commands

* “Book ticket from Bangalore to Pune”
* “Check PNR status”
* “Train schedule for 12004”
* “Cancel my ticket”

---

## ⚠️ Notes

* Ensure server is running before accessing UI
* First load may take time (in deployment)
* Voice features depend on browser support

---


