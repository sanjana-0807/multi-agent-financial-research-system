import { DollarSign, TrendingUp, Landmark, FileText, ArrowLeftRight, User } from 'lucide-react'
import { formatCurrency } from '../../utils/formatCurrency.js'

const metricConfig = [
  { key: 'revenue', label: 'Revenue', icon: DollarSign, unit: 'USD in millions', color: 'bg-blue-50 text-blue-600' },
  { key: 'net_profit', label: 'Profit', icon: TrendingUp, unit: 'USD in millions', color: 'bg-green-50 text-green-600' },
  { key: 'assets', label: 'Assets', icon: Landmark, unit: 'USD in millions', color: 'bg-gray-100 text-gray-600' },
  { key: 'liabilities', label: 'Liabilities', icon: FileText, unit: 'USD in millions', color: 'bg-orange-50 text-orange-600' },
  { key: 'cash_flow', label: 'Cash Flow', icon: ArrowLeftRight, unit: 'USD in millions', color: 'bg-cyan-50 text-cyan-600' },
  { key: 'eps', label: 'EPS', icon: User, unit: 'USD', color: 'bg-purple-50 text-purple-600' }
]

function MetricsPanel({ data }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {metricConfig.map(({ key, label, icon: Icon, unit, color }) => {
        const value = data?.[key]
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
  )
}

export default MetricsPanel
