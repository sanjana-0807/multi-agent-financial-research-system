# multi-agent-financial-research-system
Multi-Agent Financial Research System developed as part of the Infosys Springboard Internship.
## Member 2 — Extraction Agent + Frontend

### Locked Extraction JSON Format
This is the exact shape the Extraction Agent will output, agreed and confirmed with the team on Day 4. All field names follow the team's Day 0 snake_case convention.

```json
{
  "metric_id": "M001",
  "document_id": "D001",
  "company": "Tesla",
  "fiscal_year": 2025,
  "revenue": 879891,
  "net_profit": 74982,
  "assets": 247489282,
  "liabilities": 628742,
  "cash_flow": 82782732,
  "eps": 847289,
  "ratios": {
    "current_ratio": 1.8,
    "debt_to_equity": 0.38,
    "net_profit_margin": 18.9
  }
}
```

**Naming decision:** `company` is used instead of `company_name` (which only appeared in an early example) to match Member 5's real MongoDB schema.

### Dashboard.jsx
Renders the Financial Dashboard page: a sidebar with navigation links, 6 metric cards (Revenue, Profit, Assets, Liabilities, Cash Flow, EPS), 3 ratio cards (Current Ratio, Debt to Equity, Net Profit Margin), and 2 chart placeholders. All values are read from `src/data/mockDashboardData.js`, not hardcoded.

### FinancialCard.jsx
Reusable card component. Accepts four props:
- `label` — the metric name
- `value` — the numeric value
- `icon` — a lucide-react icon component
- `unit` — the display unit (e.g. "USD in millions", "ratio", "%")

If `value` is missing or falsy, the card displays "N/A" instead of breaking or showing blank.

### Testing done
Tested with two different datasets (Tesla and Apple) to confirm the Dashboard correctly updates all fields. Also tested a dataset with a missing field (`eps` removed) to confirm the UI degrades gracefully rather than breaking.

### Still pending
- Response Models — to be finalized jointly with Member 3
- React Router integration with Member 1's existing `AppRoutes.jsx`
- Real charts (with axes) replacing the current placeholder boxes