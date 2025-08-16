import json
from collections import defaultdict
from datetime import datetime, timedelta
# CORRECTED: Import Depends
from fastapi import Depends
from sqlmodel import Session, select, func
from ..db.sqlite_db import get_session
from ..models.database import Document, Conversation
from ..models.api import AnalyticsOverview

class AnalyticsService:
    # CORRECTED: Changed from next(get_session()) to Depends(get_session)
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_overview(self) -> AnalyticsOverview:
        total_docs = self.session.exec(select(func.count(Document.id))).one()
        total_chunks_result = self.session.exec(select(func.sum(Document.chunk_count))).one()
        total_chunks = total_chunks_result if total_chunks_result is not None else 0
        
        total_queries = self.session.exec(select(func.count(Conversation.id))).one()
        avg_time_result = self.session.exec(select(func.avg(Conversation.response_time))).one()
        avg_time = avg_time_result if avg_time_result is not None else 0.0

        return AnalyticsOverview(
            total_documents=total_docs,
            total_chunks=int(total_chunks),
            total_queries=total_queries,
            avg_response_time=round(float(avg_time), 3)
        )

    def get_latency_histogram(self) -> dict:
        buckets = [(0, 0.5), (0.5, 1), (1, 2), (2, 5), (5, float('inf'))]
        labels = ["0-0.5s", "0.5-1s", "1-2s", "2-5s", ">5s"]
        counts = {label: 0 for label in labels}
        
        response_times = self.session.exec(select(Conversation.response_time)).all()
        for rt in response_times:
            if rt is None: continue
            for i, (low, high) in enumerate(buckets):
                if low <= rt < high:
                    counts[labels[i]] += 1
                    break
        return counts

    def get_precision_at_k(self) -> dict:
        ks = [1, 3, 5]
        sums = {k: 0.0 for k in ks}
        total = 0
        
        # Use the .sources property which is already a list of dicts
        conversations = self.session.exec(select(Conversation)).all()
        for conv in conversations:
            if not conv.sources: continue
            total += 1
            n = len(conv.sources)
            for k in ks:
                sums[k] += min(1.0, n / float(k))
        
        if total == 0: return {f"p_at_{k}": 0.0 for k in ks}
        return {f"p_at_{k}": round(sums[k] / total, 4) for k in ks}
