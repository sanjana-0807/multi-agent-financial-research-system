import json
from report_agent import ReportAgent


with open("mock_reports.json", "r", encoding="utf-8") as file:
    mock_reports = json.load(file)


agent = ReportAgent()


for i, data in enumerate(mock_reports, start=1):

    print("\n" + "=" * 60)
    print(f"GENERATING PDF {i}: {data['company_name']}")
    print("=" * 60)

    report = agent.generate_report(
        data["extracted_data"],
        data.get("red_flags", []),
        data.get("comparison_data", {}),
        company_name=data.get("company_name", "Unknown"),
        report_period=data.get("report_period", "Unknown")
    )

    filename = f"{data['company_name'].lower()}_financial_report.pdf"

agent.generate_pdf_report(report, filename)

print(f"PDF generated for {data['company_name']}")