"""
Retrieval Module.

Implements the full hybrid retrieval pipeline:
1. HyDE (Hypothetical Document Embeddings) – query transformation
2. BM25 keyword search + semantic vector search
3. Reciprocal Rank Fusion (RRF) to merge results
4. Cross-Encoder re-ranking for precision
"""

import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from functools import lru_cache
import numpy as np

from ..core.settings import settings
from ..db.chroma_db import get_or_create_collection
from ..rag.models import get_embedding_model, get_reranker_model, get_llm_and_tokenizer


# --- Embedding Logic ---

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for a list of texts."""
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True).tolist()

def embed_text(text: str) -> List[float]:
    """Generates an embedding for a single text."""
    instruction = "Represent this sentence for searching relevant passages: "
    return embed_texts([instruction + text])[0]


# --- Hypothetical Document Generation (HyDE) ---

def generate_hypothetical_answer(query: str) -> str:
    """
    Uses the main LLM to generate a hypothetical, ideal answer to the user's query.
    This hypothetical answer is then embedded for semantic search (HyDE technique).
    """
    llm, tokenizer = get_llm_and_tokenizer()

    prompt_data = [
        {"role": "system", "content": "You are a helpful assistant. Please generate a short, high-quality, hypothetical paragraph that directly answers the following user question. Do not say 'Here is a hypothetical answer.' Just generate the paragraph itself."},
        {"role": "user", "content": query}
    ]
    
    # 1. Try using tokenizer template
    prompt = None
    if tokenizer and tokenizer.chat_template:
        try:
             prompt = tokenizer.apply_chat_template(prompt_data, tokenize=False, add_generation_prompt=True)
        except Exception:
            pass
            
    # 2. Manual Fallback
    if not prompt:
        model_type = settings.LLM_MODEL_TYPE.lower()
        if "mistral" in model_type or "llama" in model_type:
            prompt = f"<s>[INST] {prompt_data[0]['content']}\n\nQuestion: {query} [/INST]"
        elif "qwen" in model_type:
            prompt = f"<|im_start|>system\n{prompt_data[0]['content']}<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
        else:
            prompt = f"System: {prompt_data[0]['content']}\nUser: {query}\nAssistant:"

    stop_tokens = []
    if "qwen" in settings.LLM_MODEL_TYPE.lower():
        stop_tokens = ["<|im_end|>", "<|im_start|>"]
    elif "mistral" in settings.LLM_MODEL_TYPE.lower():
        stop_tokens = ["</s>"]
    else:
        stop_tokens = ["User:", "System:"]

    result = llm(
        prompt,
        max_new_tokens=128,
        temperature=0.7,
        stop=stop_tokens
    )

    hypothetical_answer = result.strip()
    return hypothetical_answer


# --- Chunking Logic ---

def recursive_character_text_splitter(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Recursively splits text into chunks using a hierarchy of separators."""
    if len(text) <= chunk_size:
        return [text]
    separators = ["\n\n", "\n", ". ", " ", ""]
    best_separator = separators[-1]
    for sep in separators:
        if sep in text:
            best_separator = sep
            break
    chunks = []
    splits = text.split(best_separator)
    current_chunk = ""
    for part in splits:
        if len(part) > chunk_size:
            chunks.extend(recursive_character_text_splitter(part, chunk_size, chunk_overlap))
            continue
        if len(current_chunk) + len(part) + len(best_separator) <= chunk_size:
            current_chunk += part + best_separator
        else:
            chunks.append(current_chunk)
            overlap_start_index = max(0, len(current_chunk) - chunk_overlap)
            current_chunk = current_chunk[overlap_start_index:] + part + best_separator
    if current_chunk:
        chunks.append(current_chunk)
    return [c.strip() for c in chunks if c.strip()]

def chunk_text(text: str, chunk_size: int, overlap: int, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Chunks text and attaches metadata to each chunk."""
    chunks_of_text = recursive_character_text_splitter(text, chunk_size, overlap)
    return [{"text": chunk, "metadata": metadata} for chunk in chunks_of_text]


# --- Hybrid Retrieval Logic with Re-ranking ---

def reciprocal_rank_fusion(ranked_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
    """Merges multiple ranked lists using Reciprocal Rank Fusion (RRF)."""
    fused_scores = {}
    for doc_list in ranked_lists:
        for rank, doc in enumerate(doc_list):
            doc_id = doc['id']
            if doc_id not in fused_scores:
                fused_scores[doc_id] = {'doc': doc, 'score': 0}
            fused_scores[doc_id]['score'] += 1 / (k + rank + 1)
    reranked_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
    return [result['doc'] for result in reranked_results]

def retrieve_hybrid(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a three-stage retrieval process:
    1. HyDE – transform query into hypothetical answer
    2. Fast Retrieval – BM25 keyword + semantic vector search, merged via RRF
    3. Re-ranking – Cross-Encoder for precision scoring
    """
    collection = get_or_create_collection()
    all_docs = collection.get(include=["metadatas", "documents"])
    if not all_docs or not all_docs['ids']:
        return []

    # Stage 1: Query Transformation (HyDE)
    hypothetical_answer = generate_hypothetical_answer(query)

    # Stage 2: Fast Retrieval
    num_candidates = top_k * 5
    tokenized_docs = [doc.split() for doc in all_docs['documents']]
    bm25 = BM25Okapi(tokenized_docs)
    bm25_scores = bm25.get_scores(query.split())
    top_n_bm25_indices = np.argsort(bm25_scores)[::-1][:num_candidates]
    bm25_results = [{"id": all_docs['ids'][i], "text": all_docs['documents'][i], "metadata": all_docs['metadatas'][i]} for i in top_n_bm25_indices]
    query_embedding = embed_text(hypothetical_answer)
    semantic_results_raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=num_candidates,
        include=["metadatas", "documents"]
    )
    semantic_results = []
    if semantic_results_raw and semantic_results_raw['ids'][0]:
        for i, doc_id in enumerate(semantic_results_raw['ids'][0]):
            semantic_results.append({"id": doc_id, "text": semantic_results_raw['documents'][0][i], "metadata": semantic_results_raw['metadatas'][0][i]})
    candidate_chunks = reciprocal_rank_fusion([bm25_results, semantic_results])
    if not candidate_chunks:
        return []

    # Stage 3: Accurate Re-ranking
    reranker = get_reranker_model()
    reranker_input = [[query, chunk['text']] for chunk in candidate_chunks]
    reranker_scores = reranker.predict(reranker_input)
    for i in range(len(candidate_chunks)):
        candidate_chunks[i]['rerank_score'] = reranker_scores[i]
    reranked_results = sorted(candidate_chunks, key=lambda x: x['rerank_score'], reverse=True)
    
    return reranked_results[:top_k]