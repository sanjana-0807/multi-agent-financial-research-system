import RatiosTable from '../features/extraction/RatiosTable.jsx'
import { dashboardData } from '../data/mockDashboardData.js'

function RatiosPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Financial Ratios</h1>
      <p className="text-gray-500 mb-6">Key ratios calculated from extracted financial data.</p>
      <RatiosTable ratios={dashboardData.ratios} />
    </div>
  )
}
export default RatiosPage
