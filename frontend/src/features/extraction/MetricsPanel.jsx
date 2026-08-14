import { DollarSign, TrendingUp, Landmark, ShieldAlert, Coins, LineChart } from 'lucide-react'
import FinancialCard from '../../components/FinancialCard.jsx'
import { formatCurrency } from '../../utils/formatCurrency.js'

const metricConfig = [
  { 
    key: 'revenue', 
    label: 'Total Revenue', 
    icon: DollarSign, 
    unit: 'in thousands',
    change: '+23.4%',
    trend: 'up',
    description: 'Total top-line gross revenue generated from automotive sales, energy generation, and services during the fiscal year.' 
  },
  { 
    key: 'net_profit', 
    label: 'Net Profit', 
    icon: TrendingUp, 
    unit: 'in thousands',
    change: '+14.2%',
    trend: 'up',
    description: 'Net profit remaining after deducting operating expenses, taxes, interest, and cost of goods sold.' 
  },
  { 
    key: 'assets', 
    label: 'Total Assets', 
    icon: Landmark, 
    unit: 'in thousands',
    change: '+8.7%',
    trend: 'up',
    description: 'Combined balance sheet value of current assets, cash reserves, property, plant, equipment, and inventory.' 
  },
  { 
    key: 'liabilities', 
    label: 'Total Liabilities', 
    icon: ShieldAlert, 
    unit: 'in thousands',
    change: '-3.1%',
    trend: 'down',
    description: 'Total short-term and long-term financial obligations, accrued debt, and supplier payables.' 
  },
  { 
    key: 'cash_flow', 
    label: 'Operating Cash Flow', 
    icon: Coins, 
    unit: 'in thousands',
    change: '+18.9%',
    trend: 'up',
    description: 'Net cash generated directly from core operating activities and customer payments.' 
  },
  { 
    key: 'eps', 
    label: 'Earnings Per Share (EPS)', 
    icon: LineChart, 
    unit: 'USD per share',
    change: '+$1.15',
    trend: 'up',
    description: 'Net earnings allocated to each outstanding share of common stock.' 
  }
]

function MetricsPanel({ data }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fadeIn">
      {metricConfig.map(({ key, label, icon: Icon, unit, change, trend, description }) => {
        const rawValue = data?.[key]
        const formattedValue = key === 'eps' 
          ? (rawValue ? `$${rawValue}` : 'N/A')
          : formatCurrency(rawValue)

        return (
          <FinancialCard
            key={key}
            label={label}
            value={formattedValue}
            icon={Icon}
            unit={unit}
            change={change}
            trend={trend}
            description={description}
          />
        )
      })}
    </div>
  )
}

export default MetricsPanel

