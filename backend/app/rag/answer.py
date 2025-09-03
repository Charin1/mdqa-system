from typing import List, Dict, Any, Tuple, Generator
from functools import lru_cache
from ctransformers import AutoModelForCausalLM
import os
from huggingface_hub import login

# --- Hugging Face Login ---
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    print("--- [INFO] Logging in to Hugging Face Hub ---")
    login(token=HF_TOKEN)
else:
    print("--- [WARNING] HF_TOKEN environment variable not set. ---")


# --- Llama Pro LLM Answer Generation Pipeline (GGUF for Universal Compatibility) ---

@lru_cache(maxsize=1)
def get_llama_llm():
    """
    Initializes and caches the Llama-Pro-8B-Instruct GGUF model using ctransformers.
    """

    llm = AutoModelForCausalLM.from_pretrained(
        "TheBloke/LLaMA-Pro-8B-Instruct-GGUF",
        model_file="llama-pro-8b-instruct.Q2_K.gguf",
        model_type="llama",
        gpu_layers=50 
    )
    return llm

def build_llama_pro_prompt(query: str, hits: List[Dict[str, Any]]) -> str:
    """
    Builds a prompt following the specific instruction format for Llama Pro Instruct.
    """
    context_texts = [hit['text'] for hit in hits[:5]]
    context = "\n\n".join(context_texts)

    prompt = f"""<|system|>
You are an expert document analyst. Your task is to answer the user's question based *only* on the provided context. Synthesize a coherent, helpful answer. If the context does not contain the information needed to answer the question, you must say "Based on the provided documents, I could not find an answer." Do not use any outside knowledge or make up information.
<|user|>
CONTEXT:
---
{context}
---

QUESTION: {query}
<|assistant|>
"""
    return prompt

def generate_llama_answer_stream(query: str, hits: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """
    Generates a precise, relevant answer using the local Llama Pro GGUF model
    and streams the output token by token.
    """
    if not hits:
        yield "I could not find any relevant information in the provided documents."
        return

    llm = get_llama_llm()
    prompt = build_llama_pro_prompt(query, hits)
    
    # --- THIS IS THE DEFINITIVE FIX ---
    # We go back to the simple llm() call, which correctly accepts `max_new_tokens`,
    # and we simply add the `stream=True` parameter to it.
    token_generator = llm(
        prompt, 
        max_new_tokens=512, 
        temperature=0.2, 
        top_p=0.95, 
        stop=["<|user|>", "<|system|>"],
        stream=True  # <-- THE FIX IS HERE
    )

    for token in token_generator:
        yield token

# Rename the main function for clarity
generate_simple_answer = generate_llama_answer_stream