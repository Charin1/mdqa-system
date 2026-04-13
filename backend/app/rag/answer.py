"""
Answer Generation Module.

Uses the centralized LLM from models.py to generate answers.
Supports streaming token-by-token output for a responsive UX.
"""

from typing import List, Dict, Any, Generator
from .models import get_llm_and_tokenizer
from ..core.settings import settings


def build_answer_prompt(tokenizer, query: str, hits: List[Dict[str, Any]]) -> str:
    """
    Builds a prompt using the tokenizer's chat template if available,
    otherwise falls back to manual formatting based on model type.
    """
    context_texts = [hit['text'] for hit in hits[:5]]
    context = "\n\n".join(context_texts)

    # 1. Try using the tokenizer's chat template (Best for consistent behavior)
    if tokenizer and tokenizer.chat_template:
        messages = [
            {"role": "system", "content": "You are an expert document analyst. Your task is to answer the user's question based *only* on the provided context. Synthesize a coherent, helpful answer. If the context does not contain the information needed to answer the question, you must say \"Based on the provided documents, I could not find an answer.\" Do not use any outside knowledge or make up information."},
            {"role": "user", "content": f"CONTEXT:\n---\n{context}\n---\n\nQUESTION: {query}"}
        ]
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception as e:
            print(f"--- [WARNING] Chat template application failed: {e}. Falling back to manual. ---")

    # 2. Manual Fallback based on Model Type
    model_type = settings.LLM_MODEL_TYPE.lower()
    
    if "mistral" in model_type or "llama" in model_type:
        # Standard [INST] format for Mistral/Llama
        prompt = f"""<s>[INST] You are an expert document analyst. Answer the question based ONLY on the context provided.
        
CONTEXT:
{context}

QUESTION:
{query} [/INST]"""
        return prompt

    elif "qwen" in model_type:
        # ChatML format for Qwen
        prompt = f"""<|im_start|>system
You are an expert document analyst. Answer based ONLY on the context.<|im_end|>
<|im_start|>user
CONTEXT:
{context}

QUESTION:
{query}<|im_end|>
<|im_start|>assistant
"""
        return prompt

    else:
        # Generic fallback
        prompt = f"""System: You are a document analyst. Answer based on the context.

Context:
{context}

User: {query}

Assistant:"""
        return prompt


def generate_answer_stream(query: str, hits: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Generates a precise, relevant answer using the local GGUF model via ctransformers
    and streams the output token by token.
    """
    if not hits:
        yield "I could not find any relevant information in the provided documents."
        return

    llm, tokenizer = get_llm_and_tokenizer()
    prompt = build_answer_prompt(tokenizer, query, hits)
    
    # Determine stop tokens based on model type
    stop_tokens = []
    if "qwen" in settings.LLM_MODEL_TYPE.lower():
        stop_tokens = ["<|im_end|>", "<|im_start|>"]
    elif "mistral" in settings.LLM_MODEL_TYPE.lower():
        stop_tokens = ["</s>"]
    else:
        stop_tokens = ["User:", "System:"] # Generic

    # Use ctransformers streaming
    token_generator = llm(
        prompt,
        max_new_tokens=settings.LLM_MAX_TOKENS,
        temperature=0.2,
        top_p=0.95,
        stop=stop_tokens,
        stream=True
    )

    for token in token_generator:
        if token:
            yield token


# Alias for backward compatibility with rag_service.py
generate_simple_answer = generate_answer_stream