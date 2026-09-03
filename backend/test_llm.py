from agents.research_agent.agent import llm


def main():
    print("Testing LLM connection...")

    response = llm.call(
        "Answer in one sentence: What is financial revenue?"
    )

    print("\n===== LLM RESPONSE =====")
    print(response)


if __name__ == "__main__":
    main()