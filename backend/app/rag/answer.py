from typing import List, Dict, Any, Tuple
from functools import lru_cache
from ctransformers import AutoModelForCausalLM
# We no longer need the standard tokenizer for this model's prompt
# from transformers import AutoTokenizer 
import os
from huggingface_hub import login

# --- Hugging Face Login ---
# This is good practice, though not strictly required for this GGUF model.
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
    # CORRECTED: Using the exact model name you specified.
    llm = AutoModelForCausalLM.from_pretrained(
        "TheBloke/LLaMA-Pro-8B-Instruct-GGUF",
        model_file="llama-pro-8b-instruct.Q2_K.gguf",
        model_type="llama",
        # This will automatically use the best hardware available (CUDA, Metal, CPU).
        gpu_layers=50 
    )
    return llm

def build_llama_pro_prompt(query: str, hits: List[Dict[str, Any]]) -> str:
    """
    Builds a prompt following the specific instruction format for Llama Pro Instruct.
    """
    context_texts = [hit['text'] for hit in hits[:5]]
    context = "\n\n".join(context_texts)

    # CORRECTED: This is the official Llama Pro Instruct prompt template.
    # It is much simpler and is the key to fixing the garbage output.
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

def generate_llama_answer(query: str, hits: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Generates a precise, relevant answer using the local Llama Pro GGUF model.
    """
    if not hits:
        return "I could not find any relevant information in the provided documents.", "Low"

    # 1. Get the Llama Pro LLM
    llm = get_llama_llm()

    # 2. Build the correct prompt
    prompt = build_llama_pro_prompt(query, hits)
    
    # 3. Generate the answer
    # We need to add a stop token to tell the model when to finish.

    print(prompt)
    answer = llm(prompt, max_new_tokens=512, temperature=0.2, top_p=0.95, stop=["<|user|>", "<|system|>"])

    # Determine confidence
    if "could not find an answer" in answer.lower():
        confidence = "Medium"
    else:
        confidence = "High"
        
    return answer, confidence

# Rename the main function for clarity
generate_simple_answer = generate_llama_answer