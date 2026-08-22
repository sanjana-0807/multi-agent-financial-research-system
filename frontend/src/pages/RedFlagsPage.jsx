import RedFlagList from '../features/redflags/RedFlagList.jsx'

const MOCK_FLAGS = [
  { id: '1', title: 'Unusual Revenue Spike', description: 'Revenue increased by 340% in Q4 compared to Q3, significantly above the industry average growth rate.', severity: 'high', category: 'Revenue' },
  { id: '2', title: 'Debt-to-Equity Ratio Concern', description: 'Debt-to-equity ratio of 1.87 exceeds the industry benchmark of 1.5, indicating higher financial leverage risk.', severity: 'medium', category: 'Leverage' },
  { id: '3', title: 'Cash Flow Discrepancy', description: 'Operating cash flow does not align with reported net income. Difference exceeds 15% threshold.', severity: 'high', category: 'Cash Flow' },
  { id: '4', title: 'Inventory Buildup', description: 'Inventory levels increased by 28% while revenue grew only 12%, suggesting potential demand softening.', severity: 'low', category: 'Operations' },
]

function RedFlagsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Red Flags</h1>
      <p className="text-gray-500 mb-6">Financial risk indicators and anomaly detection results.</p>
      <RedFlagList flags={MOCK_FLAGS} />
    </div>
  )
}
export default RedFlagsPage
