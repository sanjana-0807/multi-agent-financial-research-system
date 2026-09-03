from agents.research_agent.retrieval import retrieve_relevant_chunks


document_id = "D09AE81D6"

question = "What was the revenue in 2025?"

results = retrieve_relevant_chunks(
    question=question,
    document_id=document_id,
    top_k=5,
)

print("\n===== RETRIEVED CHUNKS =====\n")

for index, result in enumerate(results, start=1):
    print(f"--- Result {index} ---")
    print("Page:", result["page"])
    print("Chunk:", result["chunk_index"])
    print("Distance:", result["distance"])
    print("Text:", result["text"][:500])
    print()