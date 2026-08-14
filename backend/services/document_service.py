import os
import re
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from models.document import DocumentModel
from vectorstore.chroma_client import collection


UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "documents"
)

os.makedirs(UPLOAD_DIR, exist_ok=True)


class DocumentService:

    ALLOWED_EXTENSIONS = {".pdf"}

    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    @classmethod
    async def process_upload(cls, file: UploadFile):

        # 1. Validate file
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required."
            )

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        if extension not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are currently supported."
            )

        # 2. Generate document ID
        document_id = f"D{uuid4().hex[:8].upper()}"

        safe_filename = re.sub(
            r"[^a-zA-Z0-9_.-]",
            "_",
            file.filename
        )

        saved_filename = (
            f"{document_id}_{safe_filename}"
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            saved_filename
        )

        # 3. Save uploaded PDF
        content = await file.read()

        with open(file_path, "wb") as output_file:
            output_file.write(content)

        file_size = len(content)

        # 4. Parse PDF
        try:
            reader = PdfReader(file_path)

            page_count = len(reader.pages)

            pages = []

            for page_number, page in enumerate(
                reader.pages,
                start=1
            ):
                text = page.extract_text() or ""
                text = text.strip()

                if text:
                    pages.append({
                        "page": page_number,
                        "text": text
                    })

        except Exception as exc:

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail=f"Could not parse PDF: {str(exc)}"
            )

        # 5. Create text chunks
        chunks = []

        for page_data in pages:

            page_number = page_data["page"]
            text = page_data["text"]

            page_chunks = cls.chunk_text(text)

            for chunk_index, chunk in enumerate(
                page_chunks
            ):
                chunks.append({
                    "text": chunk,
                    "page": page_number,
                    "chunk_index": chunk_index
                })

        if not chunks:

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found in the PDF. "
                    "The document may be scanned and require OCR."
                )
            )

        # 6. Prepare ChromaDB data
        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):

            chunk_id = (
                f"{document_id}_CHUNK_{index}"
            )

            ids.append(chunk_id)

            documents.append(
                chunk["text"]
            )

            metadatas.append({
                "document_id": document_id,
                "filename": file.filename,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"]
            })

        # 7. Store chunks in ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        # 8. Store metadata in MongoDB
        now = datetime.now(timezone.utc)

        document = DocumentModel(
            document_id=document_id,
            filename=file.filename,
            file_path=file_path,
            content_type=(
                file.content_type or
                "application/pdf"
            ),
            file_size=file_size,
            page_count=page_count,
            chunk_count=len(chunks),
            status="indexed",
            created_at=now,
            updated_at=now
        )

        await document.insert()

        return {
    "message": "Document uploaded and indexed successfully.",
    "document_id": document_id,
    "filename": file.filename,
    "page_count": page_count,
    "chunk_count": len(chunks),
    "embedding_status": "generated",
    "vector_database": "ChromaDB",
    "metadata_database": "MongoDB",
    "status": "indexed"
}

    @classmethod
    def chunk_text(cls, text: str):

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        chunks = []

        start = 0

        while start < len(text):

            end = start + cls.CHUNK_SIZE

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = end - cls.CHUNK_OVERLAP

        return chunks

    @classmethod
    async def get_document(
        cls,
        document_id: str
    ):
        """
        Retrieve document metadata from MongoDB.
        """

        document = await DocumentModel.find_one(
            DocumentModel.document_id == document_id
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return document

    @classmethod
    def get_chunks(
        cls,
        document_id: str
    ):
        """
        Retrieve document chunks from ChromaDB.
        """

        result = collection.get(
            where={
                "document_id": document_id
            },
            include=[
                "documents",
                "metadatas"
            ]
        )

        return {
            "document_id": document_id,
            "chunk_count": len(result.get("ids", [])),
            "ids": result.get("ids", []),
            "documents": result.get("documents", []),
            "metadatas": result.get("metadatas", [])
        }