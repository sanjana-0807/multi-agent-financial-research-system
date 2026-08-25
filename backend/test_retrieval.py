from agents.research_agent.retrieval import FinancialRetriever


retriever = FinancialRetriever()

results = retriever.search(
    "What was the company's revenue in 2025?",
    k=5,
)

print()
print("=" * 60)
print("RETRIEVAL TEST")
print("=" * 60)

print("Number of results:", len(results))

for i, document in enumerate(results, start=1):

    print()
    print(f"RESULT {i}")
    print("-" * 60)

    print("CONTENT:")
    print(document.page_content)

    print()
    print("METADATA:")
    print(document.metadata)