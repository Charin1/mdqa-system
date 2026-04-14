"""
Answer Generation Module.

Uses llama-cpp-python via the centralized get_llm_and_tokenizer().
Utilizes create_chat_completion for robust prompt template handling.

Retry strategy:
  Attempt 1: Top 3 chunks in context
  Attempt 2: Top 1 chunk (if attempt 1 produced nothing — context may have been too long)
  Fallback:  Yield informative error message
"""

import json
from typing import List, Dict, Any, Generator
from .models import get_llm_and_tokenizer
from ..core.settings import settings


def _build_messages(query: str, hits: List[Dict[str, Any]], n_chunks: int) -> List[Dict[str, str]]:
    """
    Builds a list of messages for the Chat Completion API.
    """
    context_texts = [h['text'] for h in hits[:n_chunks]]
    context = "\n\n".join(context_texts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful document analyst. "
                "Answer the user question using ONLY the provided context. "
                "Be concise. If the context lacks the answer, say so."
            ),
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        },
    ]
    return messages


def _stream_tokens(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """
    Calls llama-cpp-python create_chat_completion with streaming.
    """
    llm, _ = get_llm_and_tokenizer()
    
    print(f"--- [INFO] Generating answer via LLM streaming ---")

    try:
        for chunk in llm.create_chat_completion(
            messages=messages,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=0.7,
            top_p=0.95,
            stream=True,
        ):
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                token = delta["content"]
                if token:
                    yield token
    except Exception as e:
        print(f"--- [ERROR] llama-cpp-python chat streaming failed: {e} ---")
        import traceback
        traceback.print_exc()
        raise


def generate_answer_stream(query: str, hits: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Streams generated answer tokens, with a 2-attempt retry strategy.
    """
    if not hits:
        yield "I could not find any relevant information in the provided documents."
        return

    for attempt, n_chunks in enumerate([3, 1], start=1):
        if attempt > 1:
            print(f"--- [INFO] No tokens from attempt 1. Retrying with {n_chunks} chunk(s). ---")

        messages = _build_messages(query, hits, n_chunks)

        yielded_any = False
        try:
            for token in _stream_tokens(messages):
                yielded_any = True
                yield token
        except Exception as e:
            print(f"--- [ERROR] Attempt {attempt} raised: {e} ---")

        if yielded_any:
            print(f"--- [INFO] Attempt {attempt} succeeded with {n_chunks} chunk(s). ---")
            return

    # Both attempts failed
    print("--- [WARNING] All attempts exhausted. Yielding fallback. ---")
    yield (
        "I retrieved relevant document sections but could not generate a response. "
        "This may be a model compatibility issue. "
        "Try asking a more specific question, or check the backend logs."
    )


# Backward compat alias
generate_simple_answer = generate_answer_stream