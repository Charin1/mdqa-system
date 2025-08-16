from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
from ..services.document_service import DocumentService
from ..models.api import UploadResponse, DocumentOut, ChunkOut

router = APIRouter()

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    service: DocumentService = Depends(DocumentService)
):
    """Endpoint to upload and process multiple documents."""
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")
    results = await service.process_uploaded_files(files)
    return results

@router.get("", response_model=List[DocumentOut])
def list_documents(service: DocumentService = Depends(DocumentService)):
    """Endpoint to list all processed documents."""
    return service.get_all_documents()

@router.get("/{doc_id}", response_model=DocumentOut)
def get_document_details(doc_id: int, service: DocumentService = Depends(DocumentService)):
    """Endpoint to get details for a single document."""
    return service.get_document_by_id(doc_id)

@router.get("/{doc_id}/chunks", response_model=List[ChunkOut])
def get_document_chunks(doc_id: int, service: DocumentService = Depends(DocumentService)):
    """Endpoint to retrieve all chunks associated with a document."""
    return service.get_chunks_for_document(doc_id)

@router.get("/{doc_id}/download")
def download_document(doc_id: int, service: DocumentService = Depends(DocumentService)):
    """Endpoint to download the original document file."""
    return service.download_document_file(doc_id)

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: int, service: DocumentService = Depends(DocumentService)):
    """Endpoint to delete a document and its associated chunks."""
    service.delete_document(doc_id)
    return None