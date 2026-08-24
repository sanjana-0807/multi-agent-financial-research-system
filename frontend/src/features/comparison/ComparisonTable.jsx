import { Building2, Sparkles, Trophy } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency.js'

const METRICS = [
  { key: 'revenue', label: 'Total Revenue', format: true, isCurrency: true, lowerIsBetter: false },
  { key: 'net_profit', label: 'Net Profit', format: true, isCurrency: true, lowerIsBetter: false },
  { key: 'assets', label: 'Total Assets', format: true, isCurrency: true, lowerIsBetter: false },
  { key: 'liabilities', label: 'Total Liabilities', format: true, isCurrency: true, lowerIsBetter: true },
  { key: 'cash_flow', label: 'Operating Cash Flow', format: true, isCurrency: true, lowerIsBetter: false },
  { key: 'eps', label: 'Diluted EPS', format: false, prefix: '$', lowerIsBetter: false },
  { key: 'ratios.net_profit_margin', label: 'Net Profit Margin', format: false, suffix: '%', lowerIsBetter: false },
  { key: 'ratios.current_ratio', label: 'Current Ratio', format: false, suffix: '', lowerIsBetter: false },
  { key: 'ratios.debt_to_equity', label: 'Debt to Equity', format: false, suffix: '×', lowerIsBetter: true },
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
                      <div className="text-sm font-bold text-slate-900 tracking-tight truncate max-w-[180px]">
                        {c.company || `Company ${i + 1}`}
                      </div>
                      <span className="text-[10px] font-semibold text-blue-600">Verified Filing</span>
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {METRICS.map(({ key, label, format, prefix, suffix, lowerIsBetter }) => {
              // Extract values for this metric across companies
              const validEntries = companies
                .map((c, idx) => ({ idx, val: getValue(c, key) }))
                .filter((item) => item.val != null && !isNaN(Number(item.val)))
                .map((item) => ({ ...item, val: Number(item.val) }))

              // Find best performer index
              let bestIdx = null
              if (validEntries.length > 1) {
                const bestEntry = lowerIsBetter
                  ? validEntries.reduce((min, cur) => cur.val < min.val ? cur : min, validEntries[0])
                  : validEntries.reduce((max, cur) => cur.val > max.val ? cur : max, validEntries[0])
                bestIdx = bestEntry?.idx
              }

              return (
                <tr key={key} className="hover:bg-blue-50/30 transition-colors">
                  <td className="px-5 py-4 text-slate-700 font-bold text-xs uppercase tracking-wider">
                    {label}
                  </td>
                  {companies.map((c, i) => {
                    const rawVal = getValue(c, key)
                    const isBest = bestIdx === i
                    const formattedVal = rawVal != null 
                      ? (format ? formatCurrency(rawVal) : `${prefix || ''}${rawVal}${suffix || ''}`) 
                      : '—'

                    return (
                      <td key={i} className="px-5 py-4 text-slate-900 font-extrabold text-sm">
                        <div className="flex items-center gap-2">
                          <span>{formattedVal}</span>
                          {isBest && (
                            <span className="flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                              <Trophy size={10} className="text-amber-500" /> Leader
                            </span>
                          )}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ComparisonTable

