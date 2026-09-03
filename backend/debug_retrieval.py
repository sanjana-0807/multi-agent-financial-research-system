from agents.research_agent.retriever import retrieve_relevant_chunks

question = "What was NVIDIA's revenue in fiscal 2025?"
document_id = "DC4FB216A"

results = retrieve_relevant_chunks(
    question,
    document_id,
    top_k=5
)

print("\n===== RETRIEVED CHUNKS =====\n")

for i, chunk in enumerate(results, start=1):
    print(f"===== RESULT {i} =====")
    print(f"Page: {chunk.get('page')}")
    print(f"Document ID: {chunk.get('document_id')}")
    print(f"Filename: {chunk.get('filename')}")
    print(f"Source: {chunk.get('source')}")
    print(f"Distance: {chunk.get('distance')}")
    print("\nCONTENT:")
    print(chunk.get("text"))
    print("\n")