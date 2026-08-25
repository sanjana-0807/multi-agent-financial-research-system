from pathlib import Path
from typing import Any

import chromadb
import pdfplumber


class DocumentIngestion:
    """
    Extracts text from financial PDFs, creates chunks,
    and stores them in ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "vectorstore",
        collection_name: str = "financial_documents",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def extract_pdf(
        self,
        pdf_path: str,
    ) -> list[dict[str, Any]]:

        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(
                pdf.pages,
                start=1,
            ):
                text = page.extract_text() or ""

                if text.strip():
                    pages.append(
                        {
                            "page": page_number,
                            "text": text,
                        }
                    )

        return pages

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[str]:

        text = text.strip()

        if not text:
            return []

        chunks = []

        start = 0
        text_length = len(text)

        while start < text_length:

            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = end - overlap

        return chunks

    def ingest(
        self,
        pdf_path: str,
        document_id: str,
    ) -> int:

        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(
                f"PDF not found: {pdf_path}"
            )

        pages = self.extract_pdf(pdf_path)

        ids = []
        documents = []
        metadatas = []

        chunk_number = 0

        for page_data in pages:

            page_number = page_data["page"]
            text = page_data["text"]

            chunks = self.chunk_text(text)

            for chunk in chunks:

                chunk_id = (
                    f"{document_id}_"
                    f"page_{page_number}_"
                    f"chunk_{chunk_number}"
                )

                ids.append(chunk_id)
                documents.append(chunk)

                metadatas.append(
                    {
                        "document_id": document_id,
                        "page": page_number,
                        "source": pdf_file.name,
                    }
                )

                chunk_number += 1

        if not documents:
            return 0

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(documents)