import time
import json
import asyncio
import traceback
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
        start_time = time.time()

        # 1. Retrieve chunks
        # This is also somewhat slow, but it's done once per query.
        hits = await asyncio.to_thread(retrieve_hybrid, payload.query, top_k=payload.top_k)

        doc_id_cache = {}
        sources = []
        for h in hits:
            filename = h.get("metadata", {}).get("filename")
            if not filename:
                continue
            if filename not in doc_id_cache:
                doc = self.session.exec(
                    select(Document).where(Document.filename == filename)
                ).first()
                doc_id_cache[filename] = doc.id if doc else None
            doc_id = doc_id_cache[filename]
            if doc_id:
                sources.append({
                    "doc_id": doc_id,
                    "chunk_id": h["id"],
                    "filename": filename,
                    "page": h.get("metadata", {}).get("page"),
                    "score": round(float(h["rerank_score"]), 4),
                })

        # 2. Send sources so the UI renders them immediately
        yield f"data: {json.dumps({'sources': sources})}\n\n"

        # 3. Stream LLM generation tokens
        # We use a Queue to bridge the sync generator (in a thread) and the async generator (here).
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _produce_tokens():
            try:
                for token in generate_simple_answer(payload.query, hits):
                    # Use call_soon_threadsafe to put into the queue from another thread
                    loop.call_soon_threadsafe(queue.put_nowait, token)
                # Signal the end of the stream
                loop.call_soon_threadsafe(queue.put_nowait, None)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"[Generation error: {e}]")
                loop.call_soon_threadsafe(queue.put_nowait, None)

        # Start the producer thread concurrently
        producer_task = asyncio.create_task(asyncio.to_thread(_produce_tokens))
        
        full_answer_parts = []
        
        # Consume from the queue
        while True:
            token = await queue.get()
            if token is None:
                break
            
            # Add to answer collection for database persistence
            full_answer_parts.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        await producer_task

        full_answer = "".join(full_answer_parts)
        print(f"\n--- [FULL ANSWER] ({len(full_answer_parts)} tokens, {len(full_answer)} chars) ---")
        print(full_answer if full_answer else "<<< EMPTY — no tokens yielded >>>")
        print("--- [END ANSWER] ---\n", flush=True)

        if not full_answer_parts:
            fallback = "I could not generate a response. Please try rephrasing your question."
            yield f"data: {json.dumps({'token': fallback})}\n\n"
            full_answer = fallback

        # 4. Persist conversation
        end_time = time.time()
        response_time = end_time - start_time

        if "could not find an answer" in full_answer.lower():
            confidence = "Medium"
        elif not hits:
            confidence = "Low"
        else:
            confidence = "High"

        self._save_conversation(payload, full_answer, confidence, sources, response_time)

    def _save_conversation(
        self,
        payload: ChatQueryIn,
        answer: str,
        confidence: str,
        sources: list,
        response_time: float,
    ):
        """Saves the conversation to SQLite with robust error handling."""
        try:
            conversation = Conversation(
                session_id=payload.session_id,
                query=payload.query,
                answer=answer,
                confidence=confidence,
                sources=sources,
                response_time=response_time,
            )
            self.session.add(conversation)
            self.session.commit()
            print(f"--- [SUCCESS] Conversation saved ({response_time:.1f}s). ---")
        except Exception as e:
            print("\n---!!! [CRITICAL ERROR] FAILED TO SAVE CONVERSATION !!!---")
            traceback.print_exc()
            self.session.rollback()