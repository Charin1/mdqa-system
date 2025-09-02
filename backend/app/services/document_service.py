import os
import uuid
import hashlib
import json
import traceback
from typing import List, Dict, Any
import pprint # Added for pretty-printing

from fastapi import Depends, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from ..db.sqlite_db import get_session
from ..db.chroma_db import get_or_create_collection
from ..core.settings import settings
from ..models.database import Document
from ..models.api import UploadResponse, DocumentOut, ChunkOut
from ..parsers.base import ParseResult
from ..parsers import pdf_parser, docx_parser, text_parser, md_parser, html_parser
from ..rag.retrieve import embed_texts, chunk_text

class DocumentService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session
        self.chroma_collection = get_or_create_collection()
        self.parsers = {
            ".pdf": pdf_parser.PDFParser(),
            ".docx": docx_parser.DOCXParser(),
            ".txt": text_parser.TextParser(),
            ".md": md_parser.MDParser(),
            ".html": html_parser.HTMLParser(),
            ".htm": html_parser.HTMLParser(),
        }
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    async def process_uploaded_files(self, files: List[UploadFile]) -> UploadResponse:
        success_docs = []
        error_docs = []

        for file in files:
            filepath = None
            try:
                content = await file.read()
                content_hash = hashlib.sha256(content).hexdigest()

                existing_doc = self.session.exec(select(Document).where(Document.content_hash == content_hash)).first()
                if existing_doc:
                    error_docs.append({"filename": file.filename, "error": "Duplicate document already exists."})
                    continue

                filepath = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
                with open(filepath, "wb") as buffer:
                    buffer.write(content)

                ext = os.path.splitext(file.filename)[1].lower()
                parser = self.parsers.get(ext)
                if not parser:
                    raise ValueError(f"Unsupported file type: '{ext}'")
                
                parsed_result = parser.parse(filepath)

                chunks = self._chunk_and_embed(parsed_result, file.filename, filepath)
                
                if chunks:
                    # --- THIS IS DEBUG STEP 2 ---
                    print("\n--- [DEBUG CHECKPOINT 2: METADATA BEFORE STORAGE] ---")
                    # Print the metadata of the first 3 chunks to be stored.
                    metadatas_to_add = [c['metadata'] for c in chunks]
                    pprint.pprint(metadatas_to_add[:3])
                    print("--- [DEBUG] END OF PRE-STORAGE METADATA ---\n")
                    # --- END OF DEBUG STEP 2 ---

                    sanitized_metadatas = []
                    for c in chunks:
                        clean_meta = {k: v for k, v in c['metadata'].items() if v is not None}
                        sanitized_metadatas.append(clean_meta)

                    self.chroma_collection.add(
                        ids=[c['id'] for c in chunks],
                        documents=[c['text'] for c in chunks],
                        embeddings=[c['embedding'] for c in chunks],
                        metadatas=sanitized_metadatas
                    )

                doc = Document(
                    filename=file.filename,
                    filepath=filepath,
                    content_hash=content_hash,
                    chunk_count=len(chunks),
                    document_metadata=parsed_result.metadata or {}
                )
                self.session.add(doc)
                self.session.commit()
                self.session.refresh(doc)
                
                success_docs.append(DocumentOut(
                    id=doc.id, filename=doc.filename, chunk_count=doc.chunk_count,
                    processed_at=doc.processed_at, document_metadata=doc.document_metadata
                ))

            except Exception as e:
                traceback.print_exc()
                error_docs.append({"filename": file.filename, "error": str(e)})
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
        
        return UploadResponse(success=success_docs, errors=error_docs)

    def _chunk_and_embed(self, parsed: ParseResult, filename: str, filepath: str) -> List[Dict[str, Any]]:
        text_units = []
        if "pages" in parsed.metadata and parsed.metadata["pages"]:
            for page_data in parsed.metadata["pages"]:
                text_units.append({
                    "text": page_data.get("text", ""),
                    "metadata": {"page": page_data.get("page_number")}
                })
        else:
            text_units.append({
                "text": parsed.text,
                "metadata": {"page": None}
            })

        all_chunks = []
        for unit in text_units:
            unit_text = unit.get("text", "")
            unit_metadata = unit.get("metadata", {})
            
            if not unit_text.strip():
                continue

            base_metadata = {
                "filename": filename,
                "source_path": filepath,
                **unit_metadata
            }
            
            unit_chunks = chunk_text(
                unit_text,
                chunk_size=settings.DEFAULT_CHUNK_SIZE,
                overlap=settings.DEFAULT_CHUNK_OVERLAP,
                metadata=base_metadata
            )
            all_chunks.extend(unit_chunks)

        if not all_chunks:
            return []

        texts_to_embed = [c['text'] for c in all_chunks]
        embeddings = embed_texts(texts_to_embed)

        results = []
        for i, chunk in enumerate(all_chunks):
            results.append({
                "id": str(uuid.uuid4()),
                "text": chunk['text'],
                "metadata": chunk['metadata'],
                "embedding": embeddings[i]
            })
        return results

    def get_all_documents(self) -> List[DocumentOut]:
        docs = self.session.exec(select(Document).order_by(Document.processed_at.desc())).all()
        return [DocumentOut(
            id=d.id, filename=d.filename, chunk_count=d.chunk_count,
            processed_at=d.processed_at, document_metadata=d.document_metadata
        ) for d in docs]

    def get_document_by_id(self, doc_id: int) -> DocumentOut:
        doc = self.session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return DocumentOut(
            id=doc.id, filename=doc.filename, chunk_count=doc.chunk_count,
            processed_at=doc.processed_at, document_metadata=doc.document_metadata
        )

    def get_chunks_for_document(self, doc_id: int) -> List[ChunkOut]:
        doc = self.session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        results = self.chroma_collection.get(where={"filename": doc.filename}, include=["metadatas", "documents"])
        if not results or not results['ids']:
            return []
        chunks = []
        for i, doc_text in enumerate(results['documents']):
            meta = results['metadatas'][i]
            chunks.append(ChunkOut(
                id=results['ids'][i],
                text_preview=doc_text[:250] + ("..." if len(doc_text) > 250 else ""),
                page=meta.get("page"),
                bboxes=meta.get("bboxes"),
                metadata=meta
            ))
        return chunks

    def download_document_file(self, doc_id: int) -> FileResponse:
        doc = self.session.get(Document, doc_id)
        if not doc or not os.path.exists(doc.filepath):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")
        return FileResponse(doc.filepath, filename=doc.filename)

    def delete_document(self, doc_id: int):
        doc = self.session.get(Document, doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        self.chroma_collection.delete(where={"filename": doc.filename})
        self.session.delete(doc)
        self.session.commit()
        if os.path.exists(doc.filepath):
            os.remove(doc.filepath)
        return None