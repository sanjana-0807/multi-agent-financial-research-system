import MetricsPanel from '../features/extraction/MetricsPanel.jsx'
import { dashboardData } from '../data/mockDashboardData.js'

function MetricsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Financial Metrics</h1>
      <p className="text-gray-500 mb-6">Key financial indicators extracted from uploaded documents.</p>
      <MetricsPanel data={dashboardData} />
    </div>
  )
}
export default MetricsPage
