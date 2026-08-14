import { useState } from 'react'
import { BarChart3, TrendingUp, DollarSign, Landmark, Coins, Trophy } from 'lucide-react'
import Card from '../../components/Card.jsx'
import { formatCurrency } from '../../utils/formatCurrency.js'

function ComparisonChart({ companies = [], metric: initialMetric = 'revenue' }) {
  const [selectedMetric, setSelectedMetric] = useState(initialMetric)
  const [hoveredCompany, setHoveredCompany] = useState(null)

  if (!companies || companies.length === 0) {
    return null
  }

  const METRIC_TABS = [
    { id: 'revenue', label: 'Revenue', icon: DollarSign },
    { id: 'net_profit', label: 'Net Profit', icon: TrendingUp },
    { id: 'assets', label: 'Assets', icon: Landmark },
    { id: 'cash_flow', label: 'Cash Flow', icon: Coins },
  ]

  const currentMetricObj = METRIC_TABS.find(m => m.id === selectedMetric) || METRIC_TABS[0]
  const maxValue = Math.max(...companies.map((c) => c[selectedMetric] || 0), 1)

  return (
    <Card 
      title={`${currentMetricObj.label} Comparison Visualizer`} 
      subtitle="Proportional financial performance bar chart with leader benchmarking"
    >
      <div className="space-y-6 select-none animate-fadeIn">
        {/* Metric Selector Tabs */}
        <div className="flex items-center gap-1.5 p-1.5 bg-slate-100/80 rounded-xl max-w-md">
          {METRIC_TABS.map((tab) => {
            const Icon = tab.icon
            const isActive = selectedMetric === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedMetric(tab.id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-white text-blue-600 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Proportional Comparison Bars */}
        <div className="space-y-5 pt-2">
          {companies.map((c, i) => {
            const rawValue = c[selectedMetric] || 0
            const percentage = Math.min(Math.round((rawValue / maxValue) * 100), 100)
            const formattedVal = formatCurrency(rawValue)
            const isLeader = percentage === 100
            const isHovered = hoveredCompany === i

            return (
              <div 
                key={i} 
                onMouseEnter={() => setHoveredCompany(i)}
                onMouseLeave={() => setHoveredCompany(null)}
                className={`space-y-2 p-3 rounded-xl transition-all cursor-pointer ${
                  isHovered ? 'bg-blue-50/50 border border-blue-100 shadow-2xs' : 'border border-transparent'
                }`}
              >
                <div className="flex justify-between items-center text-xs font-semibold">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                      {c.company ? c.company.charAt(0) : `C${i+1}`}
                    </div>
                    <span className="text-slate-900 font-extrabold">{c.company || `Company ${i + 1}`}</span>
                    
                    {isLeader && (
                      <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                        <Trophy size={10} className="text-amber-500" /> Sector Leader
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-500">{percentage}% of Leader</span>
                    <span className="text-slate-900 font-extrabold text-sm">{formattedVal}</span>
                  </div>
                </div>

                <div className="h-4 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200/60 relative">
                  <div
                    className={`h-full rounded-full transition-all duration-700 shadow-xs ${
                      isLeader 
                        ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-emerald-500' 
                        : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                    }`}
                    style={{ width: `${Math.max(percentage, 4)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

export default ComparisonChart


