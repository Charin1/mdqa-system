from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
# CORRECTED: Import 'func' from sqlmodel
from sqlmodel import Session, select, delete, func

from ..db.sqlite_db import get_session
from ..models.database import Conversation, ChatSession

class ChatHistoryService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_sessions(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all unique conversation sessions.
        Prioritizes the custom title from ChatSession, falling back to 
        the first query if no custom title exists.
        """
        # 1. Get the first interaction for each session (for the fallback title)
        subquery = select(func.min(Conversation.id).label("min_id")).group_by(Conversation.session_id).alias("subquery")
        query = select(Conversation).join(subquery, Conversation.id == subquery.c.min_id)
        first_conversations = self.session.exec(query).all()
        
        # 2. Get all custom titles from ChatSession
        sessions_metadata = self.session.exec(select(ChatSession)).all()
        metadata_map = {s.session_id: s.title for s in sessions_metadata}
        
        results = []
        for conv in first_conversations:
            # Priority: Custom Title > First Query (truncated)
            custom_title = metadata_map.get(conv.session_id)
            title = custom_title if custom_title else (conv.query[:50] + "..." if len(conv.query) > 50 else conv.query)
            
            results.append({
                "session_id": conv.session_id, 
                "title": title,
                "created_at": conv.created_at
            })

        # Sort by creation date descending
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    def update_session_title(self, session_id: str, new_title: str):
        """Updates or creates a custom title for a session."""
        existing = self.session.exec(
            select(ChatSession).where(ChatSession.session_id == session_id)
        ).first()

        if existing:
            existing.title = new_title
            existing.updated_at = func.utcnow()
        else:
            new_session = ChatSession(session_id=session_id, title=new_title)
            self.session.add(new_session)
        
        self.session.commit()
        return {"status": "ok", "title": new_title}

    def get_history(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves the full message history and metadata for a given session_id.
        """
        # Fetch messages
        conversations = self.session.exec(
            select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.id)
        ).all()

        if not conversations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # Fetch session metadata (title)
        session_meta = self.session.exec(
            select(ChatSession).where(ChatSession.session_id == session_id)
        ).first()
        
        # Default title if not set
        fallback_title = conversations[0].query[:50] + "..." if len(conversations[0].query) > 50 else conversations[0].query
        title = session_meta.title if session_meta else fallback_title

        # "Unroll" messages
        messages = []
        for conv in conversations:
            messages.append({"role": "user", "text": conv.query})
            messages.append({"role": "bot", "text": conv.answer, "sources": conv.sources})
        
        return {
            "session_id": session_id,
            "title": title,
            "messages": messages
        }

    def delete_session(self, session_id: str):
        """
        Deletes all conversation entries and session metadata for a given session_id.
        """
        # Delete conversations
        self.session.exec(delete(Conversation).where(Conversation.session_id == session_id))
        
        # Delete session metadata
        self.session.exec(delete(ChatSession).where(ChatSession.session_id == session_id))
        
        self.session.commit()
        return {"status": "ok"}