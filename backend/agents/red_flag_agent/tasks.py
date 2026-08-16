from crewai import Task


def create_red_flag_task(agent):
    """
    Creates the CrewAI task for financial red flag detection.
    """

    return Task(
        description="""
Analyze the financial information provided from the company's
financial reports.

Identify important financial red flags in these categories:

1. Rising Debt
   - Increasing total debt
   - Increasing borrowings
   - Increasing leverage
   - Increasing interest burden

2. Falling Margins
   - Declining gross margin
   - Declining operating margin
   - Declining net profit margin
   - Increasing costs relative to revenue

3. Cash Flow Issues
   - Declining operating cash flow
   - Negative operating cash flow
   - Significant difference between profit and operating cash flow
   - Liquidity concerns

4. Auditor Remarks
   - Qualified audit opinions
   - Going-concern concerns
   - Material uncertainties
   - Significant audit observations
   - Internal control weaknesses

5. Financial Risks
   - Liquidity risk
   - Debt or credit risk
   - Foreign exchange risk
   - Customer concentration risk
   - Commodity/raw-material risk
   - Regulatory or legal financial risks
   - Other material financial risks

For every detected red flag:

- Identify the category.
- Give a short title.
- Explain the issue.
- Provide supporting evidence.
- Include the page number when available.
- Assign severity: LOW, MEDIUM, or HIGH.
- Never invent financial numbers or facts.

If there is insufficient evidence for a category, explicitly state
that no confirmed red flag was identified.

Distinguish clearly between confirmed findings and potential concerns.
""",

        expected_output="""
A structured financial red flag assessment containing:

- Overall risk assessment
- Rising Debt findings
- Falling Margins findings
- Cash Flow Issues findings
- Auditor Remarks findings
- Financial Risks findings

Each finding should contain:

- Category
- Title
- Severity
- Explanation
- Evidence
- Page number when available

The assessment must be based only on the provided financial information
and must not contain unsupported claims.
""",

        agent=agent,
    )