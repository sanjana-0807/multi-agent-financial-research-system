from mongodb_helper import save_document
from mongodb_helper import save_chunk
from chromadb_helper import store_embedding
from chromadb_helper import search_embedding
save_document({
    "document_id":"D001",
    "company":"Tesla",
    "pages":120
})
save_chunk({
    "chunk_id":"C001",
    "document_id":"D001",
    "page_number":1,
    "text":"Tesla revenue increased by 15%."
})
store_embedding(
    "Tesla revenue increased by 15%.",
    {
        "document_id":"D001",
        "page_number":1,
        "chunk_id":"C001"
    },

    "DOC1"

)

results = search_embedding(

    "Which company revenue increased?"

)

print(results)