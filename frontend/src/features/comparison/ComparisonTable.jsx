import { formatCurrency } from '../../utils/formatCurrency.js'

// Side-by-side table comparing financial metrics across companies.
// Expected shape: companies = [{ company, revenue, net_profit, assets, ... }, ...]
const METRICS = [
  { key: 'revenue', label: 'Revenue', format: true },
  { key: 'net_profit', label: 'Net Profit', format: true },
  { key: 'assets', label: 'Total Assets', format: true },
  { key: 'liabilities', label: 'Liabilities', format: true },
  { key: 'cash_flow', label: 'Cash Flow', format: true },
  { key: 'eps', label: 'EPS', format: false },
  { key: 'ratios.current_ratio', label: 'Current Ratio', format: false },
  { key: 'ratios.debt_to_equity', label: 'Debt to Equity', format: false },
  { key: 'ratios.net_profit_margin', label: 'Net Profit Margin (%)', format: false },
]

function getValue(obj, path) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj)
}

function ComparisonTable({ companies = [] }) {
  if (companies.length === 0) {
    return <p className="text-sm text-gray-400 text-center py-6">No comparison data yet.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="px-4 py-3 text-left text-gray-500 font-medium">Metric</th>
            {companies.map((c, i) => (
              <th key={i} className="px-4 py-3 text-left text-gray-900 font-semibold">
                {c.company || `Company ${i + 1}`}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRICS.map(({ key, label, format }) => (
            <tr key={key} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-600 font-medium">{label}</td>
              {companies.map((c, i) => {
                const val = getValue(c, key)
                return (
                  <td key={i} className="px-4 py-3 text-gray-700">
                    {val != null ? (format ? formatCurrency(val) : val) : 'N/A'}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ComparisonTable
