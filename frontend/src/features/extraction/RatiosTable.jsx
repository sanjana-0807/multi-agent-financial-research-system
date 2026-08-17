import { Scale, Percent, TrendingUp, Info } from 'lucide-react'
import Badge from '../../components/Badge.jsx'

const ratioConfig = [
  { 
    key: 'current_ratio', 
    label: 'Current Ratio', 
    icon: Scale, 
    unit: 'x', 
    benchmark: '1.5 - 2.0x',
    status: 'success',
    statusText: 'Optimal Liquidity',
    description: 'Measures short-term liquidity and ability to cover short-term liabilities with liquid assets.'
  },
  { 
    key: 'debt_to_equity', 
    label: 'Debt to Equity', 
    icon: Scale, 
    unit: 'x', 
    benchmark: '< 1.5x',
    status: 'success',
    statusText: 'Low Leverage Risk',
    description: 'Measures financial leverage and capital structure by comparing total debt to shareholder equity.'
  },
  { 
    key: 'net_profit_margin', 
    label: 'Net Profit Margin', 
    icon: Percent, 
    unit: '%', 
    benchmark: '> 15.0%',
    status: 'success',
    statusText: 'Strong Profitability',
    description: 'Percentage of net income generated from total revenue after all operating costs and taxes.'
  }
]

function RatiosTable({ ratios }) {
  return (
    <div className="space-y-4 select-none animate-fadeIn">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Extracted Financial Ratios</h3>
        <span className="text-xs font-semibold text-slate-400">Benchmarked vs Sector Averages</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {ratioConfig.map(({ key, label, icon: Icon, unit, benchmark, status, statusText, description }) => {
          const rawValue = ratios?.[key]
          const displayValue = rawValue !== undefined && rawValue !== null 
            ? (unit === '%' ? `${rawValue}%` : `${rawValue}${unit}`) 
            : 'N/A'

          return (
            <div 
              key={key} 
              className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-3d-subtle shadow-3d-hover hover:border-blue-300 transition-all duration-300 perspective-1000"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50/80 border border-blue-100 flex items-center justify-center text-blue-600 shadow-xs">
                  <Icon size={20} />
                </div>
                <Badge variant={status}>{statusText}</Badge>
              </div>

              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{label}</div>
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">
                {displayValue}
              </div>

              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 space-y-1 mt-3">
                <div className="flex items-center justify-between text-[11px] font-semibold">
                  <span className="text-slate-400">Sector Benchmark:</span>
                  <span className="text-slate-700">{benchmark}</span>
                </div>
                <p className="text-[11px] font-medium text-slate-500 leading-snug pt-1 border-t border-slate-200/60">
                  {description}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default RatiosTable

