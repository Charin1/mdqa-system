from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentOut(BaseModel):
    id: int
    filename: str
    chunk_count: int
    processed_at: datetime
    
    # CORRECTED: Renamed from 'metadata' to 'document_metadata' to match the database model.
    document_metadata: Dict[str, Any]

class UploadResponse(BaseModel):
    success: List[DocumentOut]
    errors: List[Dict[str, str]]

class ChunkOut(BaseModel):
    id: str
    text_preview: str
    page: Optional[int]
    bboxes: Optional[List[Dict[str, float]]]
    metadata: Dict[str, Any]

class ChatQueryIn(BaseModel):
    session_id: str
    query: str
    top_k: int = 5

class ChatQueryOut(BaseModel):
    answer: str
    confidence: str
    sources: List[Dict[str, Any]]

class AnalyticsOverview(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    avg_response_time: float