import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, TEXT
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel

class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Optional[Dict], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[Dict]:
        if value is None:
            return None
        return json.loads(value)

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    filepath: str
    content_hash: str = Field(unique=True)
    chunk_count: int
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # CORRECTED: Renamed the field from 'metadata' to 'document_metadata'
    # to avoid conflict with the reserved SQLAlchemy 'metadata' attribute.
    document_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSONEncodedDict))

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    query: str
    answer: str
    confidence: str
    response_time: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # This field is fine, 'sources' is not a reserved name.
    sources: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSONEncodedDict))