from agents.research_agent.retriever import retrieve_relevant_chunks


question = "What was NVIDIA's gross margin in fiscal 2025?"

results = retrieve_relevant_chunks(
    question=question,
    document_id="DC4FB216A",
    top_k=5,
)

print("\n===== GROSS MARGIN RETRIEVAL =====\n")

for i, result in enumerate(results, 1):

    print(f"===== RESULT {i} =====")
    print(f"Page: {result.get('page')}")
    print(f"Distance: {result.get('distance')}")
    print("CONTENT:")
    print(result.get("text"))
    print()