# Report Agent Integration Interface

## Purpose

The Report Agent receives outputs from other financial research agents
and combines them into a structured financial research report.

## Input 1: Extracted Data

The Report Agent expects:

{
    "summary": "Executive summary of the company.",
    "financials": {
        "Revenue": "₹100 Crores",
        "Profit": "₹20 Crores",
        "Assets": "₹250 Crores",
        "Liabilities": "₹120 Crores",
        "Cash Flow": "₹35 Crores",
        "EPS": "₹12.50"
    },
    "outlook": "Positive growth expected."
}

## Input 2: Red Flags

The Red Flag Agent provides a list:

[
    "No major financial risks detected."
]

## Input 3: Comparison Data

The Comparison Agent provides:

{
    "Compared Company": "Microsoft",
    "Revenue Comparison": "Apple revenue is higher.",
    "Profit Comparison": "Both companies are profitable."
}

## Company Information

The Report Agent also receives:

- Company Name
- Report Period

## Report Generation

The inputs are passed to:

generate_report(
    extracted_data,
    red_flags,
    comparison_data,
    company_name,
    report_period
)

## Output

The Report Agent generates:

1. Executive Summary
2. Key Financials
3. Red Flags
4. Company Comparison
5. Outlook

## Storage

The generated report is stored in MongoDB.

## PDF Generation

The structured report is converted into a PDF using the PDF template.

## Retrieval

Reports can be retrieved from MongoDB using the application-level
Report ID.

## Integration Flow

Extraction Agent
        ↓
Red Flag Agent
        ↓
Comparison Agent
        ↓
Report Agent
        ↓
 ┌───────────────┐
 │ MongoDB       │
 │ PDF Report    │
 └───────────────┘