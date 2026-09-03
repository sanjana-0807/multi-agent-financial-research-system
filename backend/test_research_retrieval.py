from agents.research_agent.retriever import retrieve_relevant_chunks


DOCUMENT_ID = "DC4FB216A"

QUESTION = "What was NVIDIA's revenue in fiscal 2025?"


def main():

    results = retrieve_relevant_chunks(
        question=QUESTION,
        document_id=DOCUMENT_ID,
        top_k=5
    )

    print("\n===== RESEARCH QUESTION =====")
    print(QUESTION)

    print("\n===== RETRIEVED CHUNKS =====")

    if not results:
        print("No relevant chunks found.")
        return

    for index, result in enumerate(results, start=1):

        print(f"\n--- Result {index} ---")

        print(f"Page: {result['page']}")
        print(f"Document ID: {result['document_id']}")
        print(f"Source: {result['source']}")
        print(f"Distance: {result['distance']}")

        print("\nText:")
        print(result["text"])


if __name__ == "__main__":
    main()