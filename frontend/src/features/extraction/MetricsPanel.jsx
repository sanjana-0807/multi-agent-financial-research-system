import { DollarSign, TrendingUp, Landmark, ShieldAlert, Coins, LineChart } from 'lucide-react'
import FinancialCard from '../../components/FinancialCard.jsx'
import { formatCurrency } from '../../utils/formatCurrency.js'

const metricConfig = [
  { 
    key: 'revenue', 
    label: 'Total Revenue', 
    icon: DollarSign, 
    unit: 'in thousands',
    description: 'Total top-line gross revenue generated during the fiscal period.' 
  },
  { 
    key: 'net_profit', 
    label: 'Net Profit', 
    icon: TrendingUp, 
    unit: 'in thousands',
    description: 'Net profit remaining after deducting all operating expenses, taxes, interest, and costs.' 
  },
  { 
    key: 'assets', 
    label: 'Total Assets', 
    icon: Landmark, 
    unit: 'in thousands',
    description: 'Combined balance sheet value of current assets, cash reserves, property, plant, and equipment.' 
  },
  { 
    key: 'liabilities', 
    label: 'Total Liabilities', 
    icon: ShieldAlert, 
    unit: 'in thousands',
    description: 'Total short-term and long-term financial obligations, accrued debt, and payables.' 
  },
  { 
    key: 'cash_flow', 
    label: 'Operating Cash Flow', 
    icon: Coins, 
    unit: 'in thousands',
    description: 'Net cash generated directly from core operating activities and customer operations.' 
  },
  { 
    key: 'eps', 
    label: 'Earnings Per Share (EPS)', 
    icon: LineChart, 
    unit: 'USD per share',
    description: 'Net earnings allocated to each outstanding share of common stock.' 
  }
]

function MetricsPanel({ data }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fadeIn">
      {metricConfig.map(({ key, label, icon: Icon, unit, description }) => {
        const rawValue = data?.[key]
        let formattedValue = '—'
        if (rawValue !== null && rawValue !== undefined && rawValue !== '') {
          formattedValue = key === 'eps' ? `$${rawValue}` : formatCurrency(rawValue)
        }

        return (
          <FinancialCard
            key={key}
            label={label}
            value={formattedValue}
            icon={Icon}
            unit={unit}
            description={description}
          />
        )
      })}
    </div>
  )
}

export default MetricsPanel
