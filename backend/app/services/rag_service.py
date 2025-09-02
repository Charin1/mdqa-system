import time
import json
from typing import Dict, Any, List
import pprint # Added for pretty-printing

from fastapi import Depends
from sqlmodel import Session, select

from ..db.sqlite_db import get_session
from ..models.database import Conversation, Document
from ..models.api import ChatQueryIn, ChatQueryOut
from ..rag.retrieve import retrieve_hybrid
from ..rag.answer import generate_simple_answer

class RAGService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def query(self, payload: ChatQueryIn) -> ChatQueryOut:
        start_time = time.time()

        hits = retrieve_hybrid(payload.query, top_k=payload.top_k)
        
        # --- THIS IS DEBUG STEP 3 ---
        print("\n--- [DEBUG CHECKPOINT 3: DATA RETRIEVED FROM DB] ---")
        # Print the full 'hits' object to see what came back from Chroma.
        pprint.pprint(hits)
        print("--- [DEBUG] END OF RETRIEVED DATA ---\n")
        # --- END OF DEBUG STEP 3 ---

        answer, confidence = generate_simple_answer(payload.query, hits)
        
        end_time = time.time()
        response_time = end_time - start_time

        doc_id_cache = {}
        sources = []
        for h in hits:
            filename = h.get("metadata", {}).get("filename")
            if not filename:
                continue

            if filename not in doc_id_cache:
                doc = self.session.exec(select(Document).where(Document.filename == filename)).first()
                doc_id_cache[filename] = doc.id if doc else None
            
            doc_id = doc_id_cache[filename]
            
            if doc_id:
                score = round(float(h["rerank_score"]), 4)
                page_number = h.get("metadata", {}).get("page")
                sources.append({
                    "doc_id": doc_id,
                    "chunk_id": h["id"],
                    "filename": filename, 
                    "page": page_number, 
                    "score": score
                })
        
        # --- THIS IS DEBUG STEP 4 ---
        print("\n--- [DEBUG CHECKPOINT 4: FINAL API RESPONSE] ---")
        # Print the final 'sources' object being sent to the frontend.
        pprint.pprint(sources)
        print("--- [DEBUG] END OF API RESPONSE DATA ---\n")
        # --- END OF DEBUG STEP 4 ---

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