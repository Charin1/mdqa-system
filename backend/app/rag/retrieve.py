import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from functools import lru_cache
import numpy as np

from ..core.settings import settings
from ..db.chroma_db import get_or_create_collection

# --- Embedding Model ---
@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Loads and caches the state-of-the-art BAAI/bge-m3 embedding model.
    """
    return SentenceTransformer("BAAI/bge-m3")

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts (document chunks).
    The library automatically handles truncation for inputs longer than the model's limit.
    """
    model = get_embedding_model()
    # CORRECTED: Removed the invalid 'truncation=True' argument.
    return model.encode(texts, convert_to_numpy=True).tolist()

def embed_text(text: str) -> List[float]:
    """
    Generates an embedding for a single text (a user query).
    """
    instruction = "Represent this sentence for searching relevant passages: "
    return embed_texts([instruction + text])[0]

# --- Production-Grade Chunking Logic (No changes needed here) ---

def recursive_character_text_splitter(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    # ... (This function remains the same)
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
    # ... (This function remains the same)
    chunks_of_text = recursive_character_text_splitter(text, chunk_size, overlap)
    return [{"text": chunk, "metadata": metadata} for chunk in chunks_of_text]


# --- Hybrid Retrieval Logic (No changes needed here) ---

def reciprocal_rank_fusion(ranked_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
    # ... (This function remains the same)
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
    # ... (This function remains the same)
    collection = get_or_create_collection()
    all_docs = collection.get(include=["metadatas", "documents"])
    if not all_docs or not all_docs['ids']:
        return []
    tokenized_docs = [doc.split() for doc in all_docs['documents']]
    bm25 = BM25Okapi(tokenized_docs)
    bm25_scores = bm25.get_scores(query.split())
    top_n_bm25_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
    bm25_results = []
    for i in top_n_bm25_indices:
        bm25_results.append({
            "id": all_docs['ids'][i],
            "text": all_docs['documents'][i],
            "metadata": all_docs['metadatas'][i],
            "score": bm25_scores[i]
        })
    query_embedding = embed_text(query)
    semantic_results_raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 2,
        include=["metadatas", "documents", "distances"]
    )
    semantic_results = []
    if semantic_results_raw and semantic_results_raw['ids'][0]:
        for i, doc_id in enumerate(semantic_results_raw['ids'][0]):
            semantic_results.append({
                "id": doc_id,
                "text": semantic_results_raw['documents'][0][i],
                "metadata": semantic_results_raw['metadatas'][0][i],
                "score": 1.0 - semantic_results_raw['distances'][0][i]
            })
    final_results = reciprocal_rank_fusion([bm25_results, semantic_results])
    return final_results[:top_k]