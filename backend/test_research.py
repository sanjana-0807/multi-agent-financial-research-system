from dotenv import load_dotenv

load_dotenv()

from agents.research_agent.research import FinancialResearcher


researcher = FinancialResearcher()

question = "What was the company's revenue in 2025?"

results = researcher.research(question, k=3)

print("\n===== RESEARCH RESULTS =====\n")

if not results:
    print("No relevant documents found.")

else:
    for i, result in enumerate(results, start=1):
        print(f"--- Result {i} ---")
        print("Content:")
        print(result["content"])
        print("Metadata:")
        print(result["metadata"])
        print()