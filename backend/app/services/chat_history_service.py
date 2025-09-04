from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
# CORRECTED: Import 'func' from sqlmodel
from sqlmodel import Session, select, delete, func

from ..db.sqlite_db import get_session
from ..models.database import Conversation

class ChatHistoryService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_sessions(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all unique conversation sessions, using the first
        query of each session as its title.
        """
        # This query finds the first entry (MIN(id)) for each session_id,
        # then we retrieve the full row for those first entries.
        # This line will now work correctly because 'func' is imported.
        subquery = select(func.min(Conversation.id).label("min_id")).group_by(Conversation.session_id).alias("subquery")
        query = select(Conversation).join(subquery, Conversation.id == subquery.c.min_id).order_by(Conversation.created_at.desc())
        
        first_conversations = self.session.exec(query).all()
        
        return [
            {"session_id": conv.session_id, "title": conv.query[:50] + "..." if len(conv.query) > 50 else conv.query}
            for conv in first_conversations
        ]

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the full message history for a given session_id and
        formats it for the frontend.
        """
        conversations = self.session.exec(
            select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.id)
        ).all()

        if not conversations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        # "Unroll" the conversation rows into a list of user/bot messages
        messages = []
        for conv in conversations:
            messages.append({"role": "user", "text": conv.query})
            messages.append({"role": "bot", "text": conv.answer, "sources": conv.sources})
        
        return messages

    def delete_session(self, session_id: str):
        """
        Deletes all conversation entries for a given session_id.
        """
        statement = delete(Conversation).where(Conversation.session_id == session_id)
        result = self.session.exec(statement)
        self.session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
        return {"status": "ok", "deleted_count": result.rowcount}