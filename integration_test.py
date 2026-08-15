from mongodb_helper import save_document
from mongodb_helper import save_chunk

from chromadb_helper import store_embedding
from chromadb_helper import search_embedding


# --------------------------------------------------
# 1. Save document
# --------------------------------------------------

save_document({
    "document_id": "D001",
    "company": "Tesla",
    "pages": 120
})


# --------------------------------------------------
# 2. Financial document chunk
# --------------------------------------------------

financial_text = """
Tesla reported revenue of 879891 million in fiscal year 2025.
Tesla reported net profit of 74982 million.
Total assets were 247489282 million.
Total liabilities were 628742 million.
Cash flow was 82782732 million.
EPS was 847289.
"""


# --------------------------------------------------
# 3. Save chunk to MongoDB
# --------------------------------------------------

save_chunk({
    "chunk_id": "C002",
    "document_id": "D001",
    "page_number": 1,
    "text": financial_text
})


# --------------------------------------------------
# 4. Store embedding in ChromaDB
# --------------------------------------------------

store_embedding(
    financial_text,
    {
        "document_id": "D001",
        "page_number": 1,
        "chunk_id": "C002"
    },
    "C002"
)


# --------------------------------------------------
# 5. Test semantic search
# --------------------------------------------------

results = search_embedding(
    "What are Tesla's revenue, net profit, assets, liabilities, cash flow and EPS for 2025?"
)


print("\nSearch Results:")
print(results)