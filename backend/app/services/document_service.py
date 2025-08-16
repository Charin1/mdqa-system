import os
import uuid
import hashlib
import json
import traceback
from typing import List, Dict, Any

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
    """
    A service layer responsible for all business logic related to documents.
    """
    # CORRECTED: Changed from next(get_session()) to Depends(get_session)
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
        """
        Processes a list of uploaded files with enhanced debugging.
        """
        success_docs = []
        error_docs = []

        for file in files:
            filepath = None
            try:
                print(f"\n--- [DEBUG] Starting processing for file: {file.filename} ---")

                content = await file.read()
                content_hash = hashlib.sha256(content).hexdigest()

                existing_doc = self.session.exec(select(Document).where(Document.content_hash == content_hash)).first()
                if existing_doc:
                    print(f"[DEBUG] File {file.filename} is a duplicate. Skipping.")
                    error_docs.append({"filename": file.filename, "error": "Duplicate document already exists."})
                    continue

                filepath = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
                with open(filepath, "wb") as buffer:
                    buffer.write(content)
                print(f"[DEBUG] File saved to: {filepath}")

                ext = os.path.splitext(file.filename)[1].lower()
                parser = self.parsers.get(ext)
                if not parser:
                    raise ValueError(f"Unsupported file type: '{ext}'")
                
                print(f"[DEBUG] Using parser: {parser.__class__.__name__}")
                parsed_result = parser.parse(filepath)
                print("[DEBUG] Parsing complete.")

                chunks = self._chunk_and_embed(parsed_result, file.filename, filepath)
                print(f"[DEBUG] Chunking and embedding complete. Found {len(chunks)} chunks.")
                
                if chunks:
                    print("[DEBUG] Preparing to add data to ChromaDB...")
                    self.chroma_collection.add(
                        ids=[c['id'] for c in chunks],
                        documents=[c['text'] for c in chunks],
                        embeddings=[c['embedding'] for c in chunks],
                        metadatas=[c['metadata'] for c in chunks]
                    )
                    print("[DEBUG] Successfully added data to ChromaDB.")
                else:
                    print("[DEBUG] No chunks were generated. Skipping ChromaDB add.")

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
                print("[DEBUG] Successfully saved document metadata to SQLite.")
                
                success_docs.append(DocumentOut(
                    id=doc.id, filename=doc.filename, chunk_count=doc.chunk_count,
                    processed_at=doc.processed_at, document_metadata=doc.document_metadata
                ))

            except Exception as e:
                # THIS IS THE MOST IMPORTANT PART
                print(f"\n---!!! [DEBUG] AN ERROR OCCURRED while processing {file.filename} !!!---")
                # Print the full, detailed traceback to the console
                traceback.print_exc()
                print("---!!! [DEBUG] END OF ERROR TRACEBACK !!!---\n")
                
                error_docs.append({"filename": file.filename, "error": str(e)})
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
        
        return UploadResponse(success=success_docs, errors=error_docs)


    def _chunk_and_embed(self, parsed: ParseResult, filename: str, filepath: str) -> List[Dict[str, Any]]:
        chunks_with_metadata = chunk_text(
            parsed.text,
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            overlap=settings.DEFAULT_CHUNK_OVERLAP,
            metadata={"filename": filename, "source_path": filepath}
        )
        
        if not chunks_with_metadata:
            return []

        texts_to_embed = [c['text'] for c in chunks_with_metadata]
        embeddings = embed_texts(texts_to_embed)

        results = []
        for i, chunk in enumerate(chunks_with_metadata):
            print(chunk)
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