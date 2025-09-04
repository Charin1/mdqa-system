import time
import json
from typing import Dict, Any, List, AsyncGenerator
from fastapi import Depends
from sqlmodel import Session, select
import traceback # Add this import for detailed error logging

from ..db.sqlite_db import get_session
from ..models.database import Conversation, Document
from ..models.api import ChatQueryIn
from ..rag.retrieve import retrieve_hybrid
from ..rag.answer import generate_simple_answer

class RAGService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    async def query_stream(self, payload: ChatQueryIn) -> AsyncGenerator[str, None]:
        start_time = time.time()

        hits = retrieve_hybrid(payload.query, top_k=payload.top_k)
        
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

        full_answer_parts = []
        token_generator = generate_simple_answer(payload.query, hits)
        
        for token in token_generator:
            full_answer_parts.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        full_answer = "".join(full_answer_parts)
        end_time = time.time()
        response_time = end_time - start_time
        
        if "could not find an answer" in full_answer.lower():
            confidence = "Medium"
        elif not hits:
            confidence = "Low"
        else:
            confidence = "High"

        # This is now the final step, happening after the stream is complete.
        self._save_conversation(payload, full_answer, confidence, sources, response_time)

    # --- THIS IS THE DEFINITIVE FIX ---
    def _save_conversation(self, payload: ChatQueryIn, answer: str, confidence: str, sources: list, response_time: float):
        """Saves a record of the conversation with robust error handling."""
        print("\n--- [DEBUG CHECKPOINT] Attempting to save conversation to database... ---")
        try:
            conversation = Conversation(
                session_id=payload.session_id,
                query=payload.query,
                answer=answer,
                confidence=confidence,
                sources=sources,
                response_time=response_time
            )
            
            print(f"--- [DEBUG] Conversation object created for session: {payload.session_id} ---")
            
            self.session.add(conversation)
            self.session.commit()
            
            print("--- [SUCCESS] Conversation saved successfully! ---")

        except Exception as e:
            # This will catch ANY error during the save process and print it.
            print("\n---!!! [CRITICAL ERROR] FAILED TO SAVE CONVERSATION !!!---")
            traceback.print_exc()
            print("---!!! [END OF ERROR TRACEBACK] !!!---\n")
            # We roll back the session to prevent a corrupted state.
            self.session.rollback()