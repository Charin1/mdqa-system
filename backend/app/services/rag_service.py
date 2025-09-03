import time
import json
from typing import Dict, Any, List, AsyncGenerator
from fastapi import Depends
from sqlmodel import Session, select

from ..db.sqlite_db import get_session
from ..models.database import Conversation, Document
from ..models.api import ChatQueryIn
from ..rag.retrieve import retrieve_hybrid
from ..rag.answer import generate_simple_answer

class RAGService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    async def query_stream(self, payload: ChatQueryIn) -> AsyncGenerator[str, None]:
        """
        Processes a user's query and streams the response token by token.
        The response is formatted as Server-Sent Events (SSE).
        """
        start_time = time.time()

        # Stage 1: Retrieval (synchronous)
        hits = retrieve_hybrid(payload.query, top_k=payload.top_k)
        
        # First, send the sources so the UI can display them immediately.
        doc_id_cache = {}
        sources = []
        for h in hits:
            filename = h.get("metadata", {}).get("filename")
            if not filename: continue
            if filename not in doc_id_cache:
                doc = self.session.exec(select(Document).where(Document.filename == filename)).first()
                doc_id_cache[filename] = doc.id if doc else None
            doc_id = doc_id_cache[filename]
            if doc_id:
                sources.append({
                    "doc_id": doc_id, "chunk_id": h["id"], "filename": filename, 
                    "page": h.get("metadata", {}).get("page"), "score": round(float(h["rerank_score"]), 4)
                })
        
        yield f"data: {json.dumps({'sources': sources})}\n\n"

        # Stage 2: Generation (streaming)
        full_answer_parts = []
        token_generator = generate_simple_answer(payload.query, hits)
        
        for token in token_generator:
            full_answer_parts.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Stage 3: Post-generation (after the stream is finished)
        full_answer = "".join(full_answer_parts)
        end_time = time.time()
        response_time = end_time - start_time
        
        if "could not find an answer" in full_answer.lower():
            confidence = "Medium"
        elif not hits:
            confidence = "Low"
        else:
            confidence = "High"

        self._save_conversation(payload, full_answer, confidence, sources, response_time)

    def _save_conversation(self, payload: ChatQueryIn, answer: str, confidence: str, sources: list, response_time: float):
        conversation = Conversation(
            session_id=payload.session_id, query=payload.query, answer=answer,
            confidence=confidence, sources=sources, response_time=response_time
        )
        self.session.add(conversation)
        self.session.commit()