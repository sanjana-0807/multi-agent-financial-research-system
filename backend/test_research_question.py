from agents.research_agent.research_agent import answer_research_question


DOCUMENT_ID = "DC4FB216A"


questions = [
    "What was NVIDIA's revenue in fiscal 2025?",
    "What was NVIDIA's operating income in fiscal 2025?",
    "What was NVIDIA's gross margin in fiscal 2025?",
    "How much did NVIDIA's revenue grow year over year in fiscal 2025?",
    "What was NVIDIA's diluted earnings per share in fiscal 2025?",
    "What are NVIDIA's reportable segments?",
    "What was NVIDIA's revenue in fiscal 2024?",
]


for i, question in enumerate(questions, start=1):

    print("\n" + "=" * 80)
    print(f"QUESTION {i}")
    print("=" * 80)

    print(f"\n{question}")

    try:
        result = answer_research_question(
            question=question,
            document_id=DOCUMENT_ID,
            top_k=5,
        )

        print("\n===== ANSWER =====")
        print(result["answer"])

        print("\n===== CITATIONS =====")

        for citation in result.get("citations", []):
            print(
                f"Document: {citation.get('document_id')} | "
                f"Page: {citation.get('page')} | "
                f"Source: {citation.get('source')}"
            )

    except Exception as e:

        print("\n===== ERROR =====")
        print(f"{type(e).__name__}: {e}")