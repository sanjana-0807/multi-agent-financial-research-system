import { Percent, Scale } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency.js'

const ratioConfig = [
  { key: 'current_ratio', label: 'Current Ratio', icon: Scale, unit: 'ratio', color: 'bg-blue-50 text-blue-600' },
  { key: 'debt_to_equity', label: 'Debt to Equity', icon: Scale, unit: 'ratio', color: 'bg-green-50 text-green-600' },
  { key: 'net_profit_margin', label: 'Net Profit Margin', icon: Percent, unit: '%', color: 'bg-blue-50 text-blue-600' }
]

function RatiosTable({ ratios }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Ratios</h3>
      <div className="grid grid-cols-3 gap-4">
        {ratioConfig.map(({ key, label, icon: Icon, unit, color }) => {
          const value = ratios?.[key]
          return (
            <div key={key} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${color}`}>
                <Icon size={18} />
              </div>
              <p className="text-sm text-gray-500">{label}</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(value)}</p>
              <p className="text-xs text-gray-400">{unit}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default RatiosTable
