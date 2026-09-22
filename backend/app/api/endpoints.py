from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.rag import RAGPipeline
from app.db.session import get_db
from app.db.models import Chat
from app.services.evaluator import calculate_metrics
from app.services.data_pipeline import run_pipeline
from typing import List, Dict, Any, Optional
import datetime

router = APIRouter()

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

class QueryRequest(BaseModel):
    query: str
    mode: str = "normal"
    chat_history: List[Dict[str, Any]] = []
    detail: str = "auto"
    reset: bool = False
    user_id: Optional[int] = None
    session_id: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    session_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = {}

@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(req: QueryRequest, db: Session = Depends(get_db)):
    if req.reset:
        req.chat_history = []
        
    answer = rag_pipeline.query(req.query, mode=req.mode, chat_history=req.chat_history, detail=req.detail)
    
    session_id = req.session_id
    
    if req.user_id:
        if session_id:
            # Append to existing session
            chat = db.query(Chat).filter(Chat.id == session_id, Chat.user_id == req.user_id).first()
            if chat:
                # SQLAlchemy JSON columns need re-assignment to detect changes in lists
                messages = list(chat.messages)
                messages.extend([
                    {"role": "user", "content": req.query, "timestamp": str(datetime.datetime.utcnow())},
                    {"role": "assistant", "content": answer, "timestamp": str(datetime.datetime.utcnow())}
                ])
                chat.messages = messages
                db.commit()
            else:
                # session_id provided but not found, act as if new
                session_id = None
                
        if not session_id:
            # Create new session
            # Generate a title from the first 30 chars of the query
            title = req.query[:30] + "..." if len(req.query) > 30 else req.query
            chat = Chat(
                user_id=req.user_id,
                title=title,
                messages=[
                    {"role": "user", "content": req.query, "timestamp": str(datetime.datetime.utcnow())},
                    {"role": "assistant", "content": answer, "timestamp": str(datetime.datetime.utcnow())}
                ]
            )
            db.add(chat)
            db.commit()
            db.refresh(chat)
            session_id = chat.id
    
    return QueryResponse(answer=answer, session_id=session_id, metadata={"detail_requested": req.detail})

@router.get("/chats/{user_id}")
async def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in chats]

@router.get("/chats/{user_id}/session/{session_id}")
async def get_chat_session(user_id: int, session_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == session_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"id": chat.id, "title": chat.title, "messages": chat.messages, "created_at": chat.created_at}

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    reference: Optional[str] = None

@router.post("/evaluate")
async def evaluate_endpoint(req: EvaluateRequest):
    if not req.reference:
        raise HTTPException(status_code=400, detail="A reference (ground truth) is required to calculate BLEU/ROUGE scores.")
    
    scores = calculate_metrics(answer=req.answer, reference=req.reference)
    if "error" in scores:
        raise HTTPException(status_code=400, detail=scores["error"])
        
    return {
        "question": req.question,
        "metrics": scores
    }

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "AccessGov API is running"}

@router.post("/pipeline/run")
def trigger_pipeline():
    """Manually triggers the data extraction and ingestion pipeline."""
    result = run_pipeline()
    return result
