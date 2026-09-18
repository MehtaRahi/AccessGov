from fastapi import APIRouter
from pydantic import BaseModel
from app.services.rag import RAGPipeline

router = APIRouter()

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

class QueryRequest(BaseModel):
    query: str
    mode: str = "normal"

class QueryResponse(BaseModel):
    answer: str

@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(req: QueryRequest):
    answer = rag_pipeline.query(req.query, mode=req.mode)
    return QueryResponse(answer=answer)

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "AccessGov API is running"}
