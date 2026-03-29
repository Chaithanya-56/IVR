import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import ChatRequest, DTMFRequest, ChatResponse
from state_machine import StateMachine
import uuid
from gtts import gTTS

app = FastAPI()

# Get the directory of the current file (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files and templates using absolute paths for Render compatibility
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialize state machine
sm = StateMachine()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    session_id = str(uuid.uuid4())
    # Use the explicit keyword arguments for TemplateResponse to avoid context mapping issues
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"session_id": session_id}
    )

@app.get("/health")
async def health():
    return {"status": "ok", "message": "IRCTC IVR Simulator is running"}

# Create temp directory for TTS if it doesn't exist
TEMP_TTS_DIR = os.path.join(BASE_DIR, "static/temp_tts")
os.makedirs(TEMP_TTS_DIR, exist_ok=True)

@app.get("/tts")
async def get_tts(text: str):
    try:
        tts = gTTS(text=text, lang="en")
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(TEMP_TTS_DIR, filename)
        tts.save(filepath)
        return FileResponse(filepath, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def post_chat(request: ChatRequest):
    try:
        result = sm.process_input(request.session_id, request.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dtmf", response_model=ChatResponse)
async def post_dtmf(request: DTMFRequest):
    try:
        result = sm.process_input(request.session_id, request.digit, is_dtmf=True)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state/{session_id}")
async def get_state(session_id: str):
    session = sm.get_session(session_id)
    return session

@app.post("/speech-to-text")
async def speech_to_text(request: Request):
    # This is a mock endpoint as browser Web Speech API handles this.
    # In a real system, you might send audio file to server for Whisper/Google Speech.
    return {"text": "This is mock speech text"}

@app.get("/text-to-speech")
async def text_to_speech(text: str):
    # This is a mock endpoint as browser speechSynthesis handles this.
    # In a real system, you might return audio/mp3 stream from gTTS or AWS Polly.
    return {"status": "success", "text": text}

if __name__ == "__main__":
    import uvicorn
    
    # FIXED PORT 8011 (As requested by user example)
    port = 8011
    
    print("\n" + "="*50)
    print("  IRCTC IVR SIMULATOR")
    print("="*50)
    print(f"Server running at http://127.0.0.1:{port}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="127.0.0.1", port=port)
