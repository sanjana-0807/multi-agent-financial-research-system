from agents.research_agent.retriever import Retriever


retriever = Retriever()

results = retriever.retrieve(
    query="What is the company's revenue for fiscal year 2025?",
    top_k=5,
    document_id="D001",
)

print(f"Retrieved chunks: {len(results)}")

for i, result in enumerate(results, start=1):
    print("\n" + "=" * 60)
    print(f"RESULT {i}")
    print("=" * 60)
    print(f"Document ID: {result['document_id']}")
    print(f"Page: {result['page']}")
    print(f"Source: {result['source']}")
    print(f"Distance: {result['distance']}")
    print(f"\nText:\n{result['text']}")