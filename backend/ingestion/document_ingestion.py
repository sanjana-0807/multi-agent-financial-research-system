import os
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

from mongodb_helper import save_document, save_chunk
from backend.vectorstore.chroma_client import collection
from sentence_transformers import SentenceTransformer


# =========================================================
# TESSERACT OCR CONFIGURATION
# =========================================================

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if not os.path.exists(TESSERACT_PATH):
    raise FileNotFoundError(
        f"Tesseract not found at: {TESSERACT_PATH}"
    )

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# =========================================================
# EMBEDDING MODEL
# =========================================================

model = SentenceTransformer("all-MiniLM-L6-v2")


# =========================================================
# CHUNK CONFIGURATION
# =========================================================

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


# =========================================================
# SPLIT TEXT INTO CHUNKS
# =========================================================

def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
):
    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


# =========================================================
# EXTRACT TEXT FROM PDF PAGE
# =========================================================

def extract_page_text(page):
    """
    First try normal PDF text extraction.

    If the page contains no text, render the page as an
    image and use Tesseract OCR.
    """

    # -----------------------------------------------------
    # 1. Try normal PDF text extraction
    # -----------------------------------------------------

    page_text = page.get_text("text").strip()

    if page_text:
        return page_text

    # -----------------------------------------------------
    # 2. OCR fallback for scanned/image PDFs
    # -----------------------------------------------------

    print("No embedded text found. Running OCR...")

    # Render page at higher resolution for better OCR
    matrix = fitz.Matrix(2.0, 2.0)

    pix = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    # Convert PyMuPDF image to PIL image
    image = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    # Run Tesseract OCR
    ocr_text = pytesseract.image_to_string(
        image,
        lang="eng"
    )

    return ocr_text.strip()


# =========================================================
# INGEST PDF
# =========================================================

def ingest_pdf(
    pdf_path: str,
    document_id: str,
    company: str | None = None
):

    pdf_path = Path(pdf_path)

    # -----------------------------------------------------
    # Check PDF exists
    # -----------------------------------------------------

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print("=" * 60)
    print("STARTING PDF INGESTION")
    print("=" * 60)

    print(f"PDF       : {pdf_path}")
    print(f"Document ID: {document_id}")
    print(f"Company   : {company}")

    # -----------------------------------------------------
    # Open PDF
    # -----------------------------------------------------

    document = fitz.open(pdf_path)

    total_pages = len(document)

    print(f"Total pages: {total_pages}")

    # -----------------------------------------------------
    # Save document metadata to MongoDB
    # -----------------------------------------------------

    save_document({
        "document_id": document_id,
        "company": company,
        "filename": pdf_path.name,
        "pages": total_pages
    })

    total_chunks = 0

    # =====================================================
    # PROCESS EVERY PAGE
    # =====================================================

    for page_number, page in enumerate(
        document,
        start=1
    ):

        print(
            f"\nProcessing page "
            f"{page_number}/{total_pages}..."
        )

        # -------------------------------------------------
        # Extract text or OCR
        # -------------------------------------------------

        page_text = extract_page_text(page)

        if not page_text:

            print(
                f"Page {page_number}: "
                f"No text found."
            )

            continue

        print(
            f"Page {page_number}: "
            f"{len(page_text)} characters extracted."
        )

        # -------------------------------------------------
        # Split page into chunks
        # -------------------------------------------------

        page_chunks = split_text(page_text)

        print(
            f"Page {page_number}: "
            f"{len(page_chunks)} chunks created."
        )

        # =================================================
        # STORE EACH CHUNK
        # =================================================

        for chunk_index, chunk_text in enumerate(
            page_chunks,
            start=1
        ):

            chunk_id = (
                f"{document_id}"
                f"_P{page_number}"
                f"_C{chunk_index}"
            )

            # ---------------------------------------------
            # SAVE CHUNK TO MONGODB
            # ---------------------------------------------

            save_chunk({
                "document_id": document_id,
                "chunk_id": chunk_id,
                "page": page_number,
                "chunk_index": chunk_index,
                "text": chunk_text
            })

            # ---------------------------------------------
            # CREATE EMBEDDING
            # ---------------------------------------------

            embedding = model.encode(
                chunk_text,
                normalize_embeddings=True
            ).tolist()

            # ---------------------------------------------
            # STORE IN BACKEND CHROMADB
            # ---------------------------------------------

            collection.upsert(
                ids=[chunk_id],
                documents=[chunk_text],
                embeddings=[embedding],
                metadatas=[{
                    "document_id": document_id,
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "chunk_id": chunk_id
                }]
            )

            total_chunks += 1

        print(
            f"Page {page_number} completed."
        )

    # -----------------------------------------------------
    # Close PDF
    # -----------------------------------------------------

    document.close()

    # =====================================================
    # FINAL RESULT
    # =====================================================

    result = {
        "document_id": document_id,
        "filename": pdf_path.name,
        "pages": total_pages,
        "chunks": total_chunks
    }

    print("\n" + "=" * 60)
    print("PDF INGESTION COMPLETED")
    print("=" * 60)

    print(f"Document ID : {document_id}")
    print(f"Filename    : {pdf_path.name}")
    print(f"Pages       : {total_pages}")
    print(f"Total chunks: {total_chunks}")

    print("=" * 60)

    return result