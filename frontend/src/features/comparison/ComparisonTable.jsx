import { Building2, Sparkles, Trophy } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency.js'
import Badge from '../../components/Badge.jsx'

const METRICS = [
  { key: 'revenue', label: 'Revenue', format: true, isCurrency: true },
  { key: 'net_profit', label: 'Net Profit', format: true, isCurrency: true },
  { key: 'assets', label: 'Total Assets', format: true, isCurrency: true },
  { key: 'liabilities', label: 'Total Liabilities', format: true, isCurrency: true },
  { key: 'cash_flow', label: 'Operating Cash Flow', format: true, isCurrency: true },
  { key: 'eps', label: 'Earnings Per Share (EPS)', format: false, prefix: '$' },
  { key: 'ratios.current_ratio', label: 'Current Ratio', format: false, suffix: 'x' },
  { key: 'ratios.debt_to_equity', label: 'Debt to Equity', format: false, suffix: 'x' },
  { key: 'ratios.net_profit_margin', label: 'Net Profit Margin', format: false, suffix: '%' },
]

function getValue(obj, path) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj)
}

function ComparisonTable({ companies = [] }) {
  if (!companies || companies.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-8 text-center shadow-3d-subtle">
        <Building2 size={28} className="text-slate-300 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-400">No company comparison data loaded yet.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle overflow-hidden select-none animate-fadeIn">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200/80">
              <th className="px-5 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 w-1/3">
                Financial Metric
              </th>
              {companies.map((c, i) => (
                <th key={i} className="px-5 py-4 text-left">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                      {c.company ? c.company.charAt(0) : 'C'}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900 tracking-tight">{c.company || `Company ${i + 1}`}</div>
                      <span className="text-[10px] font-semibold text-blue-600">Verified Filing</span>
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {METRICS.map(({ key, label, format, prefix, suffix }) => (
              <tr key={key} className="hover:bg-blue-50/30 transition-colors">
                <td className="px-5 py-4 text-slate-700 font-bold text-xs uppercase tracking-wider">
                  {label}
                </td>
                {companies.map((c, i) => {
                  const val = getValue(c, key)
                  const formattedVal = val != null 
                    ? (format ? formatCurrency(val) : `${prefix || ''}${val}${suffix || ''}`) 
                    : 'N/A'

                  return (
                    <td key={i} className="px-5 py-4 text-slate-900 font-extrabold text-sm">
                      {formattedVal}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ComparisonTable

