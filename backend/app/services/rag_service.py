import time
import json
from typing import Dict, Any
# CORRECTED: Import Depends
from fastapi import Depends
from sqlmodel import Session
from ..db.sqlite_db import get_session
from ..models.database import Conversation
from ..models.api import ChatQueryIn, ChatQueryOut
from ..rag.retrieve import retrieve_hybrid
from ..rag.answer import generate_simple_answer

class RAGService:
    # CORRECTED: Changed from next(get_session()) to Depends(get_session)
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def query(self, payload: ChatQueryIn) -> ChatQueryOut:
        start_time = time.time()

        hits = retrieve_hybrid(payload.query, top_k=payload.top_k)
        answer, confidence = generate_simple_answer(payload.query, hits)
        
        end_time = time.time()
        response_time = end_time - start_time

        sources = [
            {
                "filename": h["metadata"].get("filename"), 
                "page": h["metadata"].get("page"), 
                "score": round(h["score"], 4)
            }
            for h in hits
        ]
        
        self._save_conversation(payload, answer, confidence, sources, response_time)

        return ChatQueryOut(answer=answer, confidence=confidence, sources=sources)

    def _save_conversation(self, payload: ChatQueryIn, answer: str, confidence: str, sources: list, response_time: float):
        conversation = Conversation(
            session_id=payload.session_id,
            query=payload.query,
            answer=answer,
            confidence=confidence,
            sources=sources,
            response_time=response_time
        )
        self.session.add(conversation)
        self.session.commit()