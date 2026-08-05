import ComparisonTable from '../features/comparison/ComparisonTable.jsx'
import ComparisonChart from '../features/comparison/ComparisonChart.jsx'

const MOCK_COMPANIES = [
  { company: 'Tesla Inc.', revenue: 879891, net_profit: 74982, assets: 247489282, liabilities: 628742, cash_flow: 82782732, eps: 8.47, ratios: { current_ratio: 1.8, debt_to_equity: 0.38, net_profit_margin: 18.9 } },
  { company: 'Apple Inc.', revenue: 383285, net_profit: 96995, assets: 352755, liabilities: 290437, cash_flow: 122151, eps: 6.13, ratios: { current_ratio: 0.98, debt_to_equity: 1.87, net_profit_margin: 25.3 } },
]

function ComparisonPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Company Comparison</h1>
        <p className="text-gray-500">Side-by-side financial analysis.</p>
      </div>
      <ComparisonTable companies={MOCK_COMPANIES} />
      <ComparisonChart companies={MOCK_COMPANIES} metric="revenue" />
    </div>
  )
}
export default ComparisonPage
