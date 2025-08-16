from fastapi import APIRouter, Depends
from ..services.rag_service import RAGService
from ..models.api import ChatQueryIn, ChatQueryOut

router = APIRouter()

@router.post("/query", response_model=ChatQueryOut)
def query(payload: ChatQueryIn, service: RAGService = Depends(RAGService)):
    """Endpoint to ask a question and get an answer from the RAG system."""
    return service.query(payload)