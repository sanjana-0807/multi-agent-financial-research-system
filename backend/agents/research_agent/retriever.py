from pathlib import Path
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions


class FinancialRetriever:
    """
    Simple persistent vector-store retriever for financial documents.
    """

    def __init__(
        self,
        persist_directory: str = "data/chroma",
        collection_name: str = "financial_documents",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        Path(persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=persist_directory
        )

        self.embedding_function = (
            embedding_functions.DefaultEmbeddingFunction()
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[str]:

        if not text:
            return []

        text = text.strip()

        if not text:
            return []

        chunks = []

        start = 0
        text_length = len(text)

        while start < text_length:

            end = min(
                start + chunk_size,
                text_length,
            )

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = end - chunk_overlap

        return chunks

    def add_document(
        self,
        document_id: str,
        document_text: str,
        metadata: Dict | None = None,
    ):
        """
        Split document into chunks and store them in ChromaDB.
        """

        chunks = self._chunk_text(
            document_text
        )

        if not chunks:
            return {
                "document_id": document_id,
                "chunks_added": 0,
            }

        metadata = metadata or {}

        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):

            chunk_id = (
                f"{document_id}_chunk_{index}"
            )

            ids.append(chunk_id)

            documents.append(chunk)

            chunk_metadata = {
                "document_id": document_id,
                "chunk_index": index,
                **metadata,
            }

            metadatas.append(
                chunk_metadata
            )

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "document_id": document_id,
            "chunks_added": len(chunks),
        }

    def retrieve(
        self,
        query: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Retrieve the most relevant document chunks.
        """

        where = None

        if document_id:
            where = {
                "document_id": document_id
            }

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        output = []

        for index, document in enumerate(documents):

            output.append(
                {
                    "text": document,
                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        else {}
                    ),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                }
            )

        return output