from agents.research_agent.rag_pipeline import (
    FinancialRAGPipeline
)


pipeline = FinancialRAGPipeline()


questions = [
    "What was the company's revenue in 2025?",
    "What was the company's net profit?",
    "What was the operating margin?",
]


for question in questions:

    print("\n" + "=" * 60)
    print("QUESTION")
    print("=" * 60)

    print(question)

    result = pipeline.run(
        question
    )

    print("\nANSWER")
    print("=" * 60)

    print(
        result["answer"]
    )

    print("\nCITATIONS")
    print("=" * 60)

    for citation in result.get(
        "citations",
        []
    ):
        print(citation)