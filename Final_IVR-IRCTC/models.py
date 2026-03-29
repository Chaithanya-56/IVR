from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    message: str
    session_id: str

class DTMFRequest(BaseModel):
    digit: str
    session_id: str

class EntityExtraction(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    train_no: Optional[str] = None
    train_class: Optional[str] = None
    selected_train: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    state: str
    intent: str
    confidence: float
    entities: EntityExtraction
    history: List[Dict[str, str]]
    dtmf_buffer: Optional[str] = ""
