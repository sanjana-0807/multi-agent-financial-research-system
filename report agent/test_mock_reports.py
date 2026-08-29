import json
from report_agent import ReportAgent


with open("mock_reports.json", "r", encoding="utf-8") as file:
    mock_reports = json.load(file)


agent = ReportAgent()


for i, data in enumerate(mock_reports, start=1):

    print("\n" + "=" * 60)
    print(f"MOCK REPORT {i}: {data['company_name']}")
    print("=" * 60)

    report = agent.generate_report(
        data["extracted_data"],
        data.get("red_flags", []),
        data.get("comparison_data", {}),
        company_name=data.get("company_name", "Unknown"),
        report_period=data.get("report_period", "Unknown")
    )

    agent.display_report(report)

    if agent.validate_report(report):

        report_id = agent.save_report(report)

        print(f"Mock report {i} saved successfully.")
        print(f"MongoDB ID: {report_id}")