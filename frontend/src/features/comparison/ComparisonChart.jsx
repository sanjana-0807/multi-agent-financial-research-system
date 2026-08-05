import { BarChart3 } from 'lucide-react'

// Placeholder chart component for comparison visualization.
// Will be replaced with real recharts BarChart once recharts is installed.
// Expected shape: companies = [{ company, revenue, net_profit, ... }, ...]
function ComparisonChart({ companies = [], metric = 'revenue' }) {
  if (companies.length === 0) {
    return null
  }

  const maxValue = Math.max(...companies.map((c) => c[metric] || 0))

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 size={18} className="text-blue-600" />
        <h3 className="text-sm font-semibold text-gray-900 capitalize">{metric.replace('_', ' ')} Comparison</h3>
      </div>

      {/* Simple bar visualization — replace with recharts once installed */}
      <div className="space-y-3">
        {companies.map((c, i) => {
          const value = c[metric] || 0
          const width = maxValue > 0 ? (value / maxValue) * 100 : 0
          return (
            <div key={i}>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>{c.company || `Company ${i + 1}`}</span>
                <span className="font-medium">{value.toLocaleString()}</span>
              </div>
              <div className="h-6 bg-gray-100 rounded-lg overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-lg transition-all"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ComparisonChart
