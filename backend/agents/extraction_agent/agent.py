import os
from dotenv import load_dotenv
from crewai import Agent, LLM

load_dotenv()

llm = LLM(
    model="anthropic/claude-3-5-sonnet-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

extraction_agent = Agent(
    role="Financial Data Extraction Specialist",
    goal="Extract precise financial metrics and ratios from company documents",
    backstory="You are a financial analyst who reads annual reports and 10-K filings and pulls out exact numbers. Never guess a number - if it's not in the text, return null.",
    llm=llm,
    verbose=True
)
