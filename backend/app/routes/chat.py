from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from ..services.rag_service import RAGService
# CORRECTED: Import the new history service
from ..services.chat_history_service import ChatHistoryService
from ..models.api import ChatQueryIn

router = APIRouter()

# --- Core Chat Endpoint ---
@router.post("/query")
async def query(payload: ChatQueryIn, service: RAGService = Depends(RAGService)):
    """Endpoint to ask a question and get a streamed answer."""
    return StreamingResponse(service.query_stream(payload), media_type="text/event-stream")

# --- NEW: Conversation History Endpoints ---

@router.get("/sessions")
def get_sessions(service: ChatHistoryService = Depends(ChatHistoryService)):
    """Retrieves a list of all past conversation sessions."""
    return service.get_sessions()

@router.get("/history/{session_id}")
def get_history(session_id: str, service: ChatHistoryService = Depends(ChatHistoryService)):
    """Retrieves all messages for a specific conversation session."""
    return service.get_history(session_id)

@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, service: ChatHistoryService = Depends(ChatHistoryService)):
    """Deletes a full conversation session."""
    service.delete_session(session_id)
    return None # Return None for 204 status