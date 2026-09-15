import os
import re
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from pypdf import PdfReader

from models.document import DocumentModel
from services.ocr_service import OCRService
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

    # ============================================================
    # UPLOAD + INDEX DOCUMENT
    # ============================================================

    @classmethod
    async def process_upload(
        cls,
        file: UploadFile,
        company_id: Optional[str] = None,
    ):
        # --------------------------------------------------------
        # 1. Validate file
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # 2. Generate ONE document ID
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # 3. Save uploaded PDF
        # --------------------------------------------------------

        content = await file.read()

        with open(file_path, "wb") as output_file:
            output_file.write(content)

        file_size = len(content)

        # --------------------------------------------------------
        # 4. Parse PDF
        # --------------------------------------------------------

        try:
            reader = PdfReader(file_path)

            page_count = len(reader.pages)

            pages = []
            ocr_page_numbers = []

            for page_number, page in enumerate(
                reader.pages,
                start=1
            ):
                text = page.extract_text() or ""
                text = text.strip()

                if OCRService.needs_ocr(text):
                    ocr_page_numbers.append(page_number)
                else:
                    pages.append({
                        "page": page_number,
                        "text": text,
                        "source": "text_layer"
                    })

        except Exception as exc:

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail=f"Could not parse PDF: {str(exc)}"
            )

        # --------------------------------------------------------
        # 4b. OCR fallback
        # --------------------------------------------------------

        ocr_used = False

        if ocr_page_numbers:

            try:
                ocr_results = OCRService.extract_pages(
                    file_path,
                    ocr_page_numbers
                )

            except RuntimeError as exc:

                if os.path.exists(file_path):
                    os.remove(file_path)

                raise HTTPException(
                    status_code=422,
                    detail=(
                        "This document appears to be scanned and OCR "
                        f"processing failed: {str(exc)}"
                    )
                )

            for page_number in ocr_page_numbers:

                ocr_text = (
                    ocr_results
                    .get(page_number, "")
                    .strip()
                )

                if ocr_text:

                    ocr_used = True

                    pages.append({
                        "page": page_number,
                        "text": ocr_text,
                        "source": "ocr"
                    })

            pages.sort(
                key=lambda p: p["page"]
            )

        ocr_page_count = sum(
            1
            for page_data in pages
            if page_data["source"] == "ocr"
        )

        # --------------------------------------------------------
        # 5. Create chunks
        # --------------------------------------------------------

        chunks = []

        for page_data in pages:

            page_number = page_data["page"]
            text = page_data["text"]
            source = page_data["source"]

            page_chunks = cls.chunk_text(text)

            for chunk_index, chunk in enumerate(
                page_chunks
            ):

                chunks.append({
                    "text": chunk,
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "source": source
                })

        if not chunks:

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found in the PDF, even after "
                    "OCR. The document may be empty, corrupted, or of "
                    "insufficient scan quality."
                )
            )

        # --------------------------------------------------------
        # 6. Prepare Chroma data
        # --------------------------------------------------------

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
                "chunk_index": chunk["chunk_index"],
                "source": chunk["source"]
            })

        # --------------------------------------------------------
        # 7. Store in ChromaDB
        # --------------------------------------------------------

        try:

            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

        except Exception as exc:

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to index document in ChromaDB: "
                    f"{str(exc)}"
                )
            )

        # --------------------------------------------------------
        # 8. Verify ChromaDB
        # --------------------------------------------------------

        try:

            verification = collection.get(
                where={
                    "document_id": document_id
                },
                include=[
                    "metadatas"
                ]
            )

            verified_chunk_count = len(
                verification.get("ids", [])
            )

        except Exception as exc:

            try:
                collection.delete(
                    where={
                        "document_id": document_id
                    }
                )
            except Exception:
                pass

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=500,
                detail=(
                    "Document was uploaded but ChromaDB verification "
                    f"failed: {str(exc)}"
                )
            )

        if verified_chunk_count != len(chunks):

            try:
                collection.delete(
                    where={
                        "document_id": document_id
                    }
                )
            except Exception:
                pass

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=500,
                detail=(
                    "ChromaDB verification failed. "
                    f"Expected {len(chunks)} chunks but found "
                    f"{verified_chunk_count} for document "
                    f"{document_id}."
                )
            )

        # --------------------------------------------------------
        # 9. Store metadata in MongoDB
        # --------------------------------------------------------

        now = datetime.now(timezone.utc)

        document = DocumentModel(
            document_id=document_id,
            filename=file.filename,
            file_path=file_path,
            content_type=(
                file.content_type
                or "application/pdf"
            ),
            file_size=file_size,
            page_count=page_count,
            chunk_count=len(chunks),
            ocr_used=ocr_used,
            ocr_page_count=ocr_page_count,
            company_id=company_id,
            status="indexed",
            created_at=now,
            updated_at=now
        )

        try:

            await document.insert()

        except Exception as exc:

            try:
                collection.delete(
                    where={
                        "document_id": document_id
                    }
                )
            except Exception:
                pass

            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=500,
                detail=(
                    "Document was indexed but MongoDB storage failed: "
                    f"{str(exc)}"
                )
            )

        # --------------------------------------------------------
        # 10. Return result
        # --------------------------------------------------------

        return {
            "message": (
                "Document uploaded and indexed successfully."
            ),
            "document_id": document_id,
            "filename": file.filename,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "embedding_status": "generated",
            "vector_database": "ChromaDB",
            "metadata_database": "MongoDB",
            "ocr_used": ocr_used,
            "ocr_page_count": ocr_page_count,
            "status": "indexed"
        }

    # ============================================================
    # CHUNK TEXT
    # ============================================================

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

            chunk = text[
                start:end
            ].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = (
                end -
                cls.CHUNK_OVERLAP
            )

        return chunks

    # ============================================================
    # GET DOCUMENT
    # ============================================================

    @classmethod
    async def get_document(
        cls,
        document_id: str
    ):

        document = await DocumentModel.find_one(
            DocumentModel.document_id == document_id
        )

        if not document:

            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        return document

    # ============================================================
    # GET CHUNKS
    # ============================================================

    @classmethod
    def get_chunks(
        cls,
        document_id: str
    ):

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
            "chunk_count": len(
                result.get("ids", [])
            ),
            "ids": result.get(
                "ids",
                []
            ),
            "documents": result.get(
                "documents",
                []
            ),
            "metadatas": result.get(
                "metadatas",
                []
            )
        }

    # ============================================================
    # FIND CHROMA DOCUMENT ID BY FILENAME
    # ============================================================

    @classmethod
    def _find_chroma_document_id(
        cls,
        filename: str,
        expected_chunk_count: int = 0,
    ) -> Optional[str]:
        """
        Find an existing Chroma document ID for a MongoDB document
        whose IDs are out of sync.

        This is only a compatibility/recovery mechanism for older
        documents. New uploads already use one consistent ID.

        Matching priority:
        1. filename
        2. expected chunk count, when available
        """

        if not filename:
            return None

        try:

            result = collection.get(
                where={
                    "filename": filename
                },
                include=[
                    "metadatas"
                ]
            )

        except Exception:
            return None

        metadatas = result.get(
            "metadatas",
            []
        )

        if not metadatas:
            return None

        counts = {}

        for metadata in metadatas:

            if not metadata:
                continue

            chroma_document_id = metadata.get(
                "document_id"
            )

            if not chroma_document_id:
                continue

            counts[chroma_document_id] = (
                counts.get(chroma_document_id, 0) + 1
            )

        if not counts:
            return None

        # Prefer an exact chunk-count match.
        if expected_chunk_count:

            exact_matches = [
                document_id
                for document_id, count in counts.items()
                if count == expected_chunk_count
            ]

            if exact_matches:
                return exact_matches[0]

        # Otherwise use the document ID with the highest number
        # of chunks for this filename.
        return max(
            counts,
            key=counts.get
        )

    # ============================================================
    # GET LATEST VALID DOCUMENT FOR COMPANY
    # ============================================================

    @classmethod
    async def get_latest_for_company(
        cls,
        company_id: str,
    ) -> Optional[DocumentModel]:
        """
        Return the newest usable indexed document for a company.

        Normal case:
            MongoDB document_id == Chroma document_id

        Legacy recovery case:
            If the MongoDB document_id has no Chroma chunks,
            locate the corresponding Chroma document using filename
            and chunk count, then repair the MongoDB document_id.

        This is company-agnostic and document-agnostic.
        """

        documents = await DocumentModel.find(
            DocumentModel.company_id == company_id,
            DocumentModel.status == "indexed",
        ).sort(
            "-created_at"
        ).to_list()

        for document in documents:

            # ----------------------------------------------------
            # Case 1: MongoDB and Chroma IDs already match
            # ----------------------------------------------------

            try:

                result = collection.get(
                    where={
                        "document_id": document.document_id
                    },
                    include=[
                        "metadatas"
                    ]
                )

                chunk_count = len(
                    result.get("ids", [])
                )

            except Exception:
                chunk_count = 0

            if chunk_count > 0:
                return document

            # ----------------------------------------------------
            # Case 2: Legacy MongoDB/Chroma ID mismatch
            # ----------------------------------------------------

            repaired_id = cls._find_chroma_document_id(
                filename=document.filename,
                expected_chunk_count=document.chunk_count,
            )

            if not repaired_id:
                continue

            # Already using that ID? Nothing to repair.
            if repaired_id == document.document_id:
                return document

            # ----------------------------------------------------
            # Prevent accidental collision with another Mongo
            # document already using the repaired Chroma ID.
            # ----------------------------------------------------

            existing_document = await DocumentModel.find_one(
                DocumentModel.document_id == repaired_id
            )

            if (
                existing_document is not None
                and existing_document.id != document.id
            ):
                # Don't overwrite another MongoDB document.
                continue

            # ----------------------------------------------------
            # Repair the MongoDB document ID.
            # ----------------------------------------------------

            old_document_id = document.document_id

            document.document_id = repaired_id
            document.updated_at = (
                datetime.now(timezone.utc)
            )

            try:

                await document.save()

            except Exception:
                # Restore in-memory value if MongoDB update fails.
                document.document_id = old_document_id
                continue

            return document

        return None

    # ============================================================
    # LINK DOCUMENT TO COMPANY
    # ============================================================

    @classmethod
    async def link_company(
        cls,
        document_id: str,
        company_id: str,
    ) -> DocumentModel:

        document = await cls.get_document(
            document_id
        )

        document.company_id = company_id

        document.updated_at = (
            datetime.now(timezone.utc)
        )

        await document.save()

        return document