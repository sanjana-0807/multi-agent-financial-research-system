from pymongo import MongoClient
from getpass import getpass
from pdf_template import create_pdf
import json
from datetime import datetime


class ReportAgent:

    def __init__(self):

        print("Report Agent Initialized")

        # MongoDB connection
        username = input("MongoDB username: ")
        password = getpass("MongoDB password: ")

        self.client = MongoClient(
            "mongodb+srv://cluster0.nqpnmoc.mongodb.net/",
            username=username,
            password=password,
            authSource="admin"
        )

        self.db = self.client["financial_research"]
        self.reports_collection = self.db["reports"]

        self.client.admin.command("ping")

        print("MongoDB Connected")

    # Generate structured financial report
    def generate_report(
        self,
        extracted_data,
        red_flags=None,
        comparison_data=None,
        company_name="Unknown",
        report_period="Unknown"
    ):

        extracted_data = extracted_data or {}
        red_flags = red_flags or []
        comparison_data = comparison_data or {}

        report = {
            "Company Name": company_name,
            "Report Period": report_period
        }

        if extracted_data.get("summary"):
            report["Executive Summary"] = extracted_data["summary"]

        if extracted_data.get("financials"):
            report["Key Financials"] = extracted_data["financials"]

        if red_flags:
            report["Red Flags"] = red_flags

        if comparison_data:
            report["Comparison"] = comparison_data

        if extracted_data.get("outlook"):
            report["Outlook"] = extracted_data["outlook"]

        return report

    # Validate generated report
    def validate_report(self, report):

        errors = []

        if not report.get("Company Name"):
            errors.append("Company name is missing.")

        if not report.get("Report Period"):
            errors.append("Report period is missing.")

        if not report.get("Executive Summary"):
            errors.append("Executive summary is missing.")

        if not report.get("Key Financials"):
            errors.append("Financial data is missing.")

        if errors:

            print("\nReport Validation Failed:")

            for error in errors:
                print("-", error)

            return False

        print("\nReport Validation Successful.")

        return True

    # Save report to MongoDB
    def save_report(self, report):

        report_id = "R" + datetime.now().strftime("%Y%m%d%H%M%S")

        report_document = {
            "report_id": report_id,
            "company_name": report.get("Company Name"),
            "report_period": report.get("Report Period"),
            "executive_summary": report.get("Executive Summary"),
            "key_financials": report.get("Key Financials"),
            "red_flags": report.get("Red Flags", []),
            "comparison": report.get("Comparison", {}),
            "outlook": report.get("Outlook"),
            "created_at": datetime.now()
        }

        self.reports_collection.insert_one(report_document)

        # Show our application-level report ID
        print("Report saved to MongoDB")
        print("Report ID:", report_id)

        return report_id

    # Retrieve report from MongoDB
    def get_report(self, report_id):

        report = self.reports_collection.find_one(
            {"report_id": report_id}
        )

        if report:

            print("\nReport Retrieved Successfully")
            print("Report ID:", report_id)

            return report

        print("\nReport not found:", report_id)

        return None

    # Generate PDF
    def generate_pdf_report(
        self,
        report,
        filename="financial_research_report.pdf"
    ):

        create_pdf(filename, report)

        print("Financial research PDF generated successfully.")

    # Display report
    def display_report(self, report):

        print("\n========== Financial Research Report ==========\n")

        for section, content in report.items():

            if section == "_id":
                continue

            print(f"{section}:")

            if isinstance(content, dict):

                for key, value in content.items():
                    print(f"  {key}: {value}")

            elif isinstance(content, list):

                for item in content:
                    print(f"  - {item}")

            else:

                print(f"  {content}")

            print()


if __name__ == "__main__":

    # Read sample financial data
    with open("sample_data.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    extracted_data = data["extracted_data"]
    red_flags = data.get("red_flags", [])
    comparison_data = data.get("comparison_data", {})

    # Create Report Agent
    agent = ReportAgent()

    # Generate report
    report = agent.generate_report(
        extracted_data,
        red_flags,
        comparison_data,
        company_name=data.get("company_name", "Unknown"),
        report_period=data.get("report_period", "Unknown")
    )

    # Display report
    agent.display_report(report)

    # Validate report
    if agent.validate_report(report):

        # Save report
        saved_report_id = agent.save_report(report)

        # Generate PDF
        agent.generate_pdf_report(report)

        # Test MongoDB retrieval
        retrieved_report = agent.get_report(saved_report_id)

        if retrieved_report:
            print("MongoDB retrieval test completed successfully.")