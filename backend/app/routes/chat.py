from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..services.rag_service import RAGService
from ..models.api import ChatQueryIn

router = APIRouter()

@router.post("/query")
async def query(payload: ChatQueryIn, service: RAGService = Depends(RAGService)):
    """
    Endpoint to ask a question and get a streamed answer from the RAG system.
    """
    return StreamingResponse(service.query_stream(payload), media_type="text/event-stream")