import { useState, useEffect } from 'react'
import MetricsPanel from '../features/extraction/MetricsPanel'
import RatiosTable from '../features/extraction/RatiosTable'
import { getExtraction } from '../api/extractionApi'
import { dashboardData as mockData } from '../data/mockDashboardData.js'

// placeholder document id until a real one exists from Document Agent
const PLACEHOLDER_DOCUMENT_ID = 'D100'

function WorkspaceDetailPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getExtraction(PLACEHOLDER_DOCUMENT_ID)
      .then((res) => {
        setData(res.data)
        setLoading(false)
      })
      .catch(() => {
        // backend/route not ready yet - fall back to mock data so the page still works
        setData(mockData)
        setError('Using mock data - backend not reachable yet')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <p className="p-6 text-gray-500">Loading...</p>
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Financial Dashboard</h1>
          <p className="text-gray-500">{data.company} - FY {data.fiscal_year}</p>
        </div>
        <p className="text-sm text-gray-400">Last updated: 2 mins ago</p>
      </div>

      {error && (
        <p className="text-xs text-orange-500 mb-4">{error}</p>
      )}

      <MetricsPanel data={data} />

      <div className="mt-6">
        <RatiosTable ratios={data.ratios} />
      </div>

      <div className="grid grid-cols-2 gap-4 mt-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-sm font-semibold text-gray-700 mb-2">Revenue Chart</p>
          <div className="h-40 flex items-center justify-center text-gray-300 text-sm border border-dashed border-gray-200 rounded-lg">
            Chart placeholder
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <p className="text-sm font-semibold text-gray-700 mb-2">Profit Chart</p>
          <div className="h-40 flex items-center justify-center text-gray-300 text-sm border border-dashed border-gray-200 rounded-lg">
            Chart placeholder
          </div>
        </div>
      </div>
    </div>
  )
}

export default WorkspaceDetailPage
