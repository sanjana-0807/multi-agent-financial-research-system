from typing import List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()


class FinancialRetriever:
    """
    Retriever for financial documents stored in ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "vectorstore",
        collection_name: str = "financial_documents",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

    def add_documents(
        self,
        documents: List[Document],
    ):
        """
        Add documents to Chroma.
        """

        if not documents:
            return 0

        self.vectorstore.add_documents(documents)

        return len(documents)

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Document]:
        """
        Retrieve the most relevant document chunks.
        """

        if not query or not query.strip():
            return []

        return self.vectorstore.similarity_search(
            query,
            k=k,
        )

    def search_with_scores(
        self,
        query: str,
        k: int = 5,
    ):
        """
        Retrieve documents with similarity scores.
        """

        if not query or not query.strip():
            return []

        return self.vectorstore.similarity_search_with_score(
            query,
            k=k,
        )