from report_agent import ReportAgent


agent = ReportAgent()

# Test report with missing required data
invalid_report = {
    "Company Name": "Microsoft",
    "Report Period": "FY2025"
}

print("\n========== INVALID REPORT TEST ==========")

if agent.validate_report(invalid_report):
    print("ERROR: Invalid report was accepted.")
else:
    print("Invalid report correctly rejected.")