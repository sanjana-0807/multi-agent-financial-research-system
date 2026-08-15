import { useState, useEffect } from 'react'
import MetricsPanel from '../features/extraction/MetricsPanel.jsx'
import { getExtraction } from '../api/extractionApi.js'
import { dashboardData as mockData } from '../data/mockDashboardData.js'

function MetricsPage() {
  const [data, setData] = useState(mockData)

  useEffect(() => {
    getExtraction('D100')
      .then((res) => setData(res.data))
      .catch(() => setData(mockData))
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Financial Metrics</h1>
      <p className="text-gray-500 mb-6">Key financial indicators extracted from uploaded documents.</p>
      <MetricsPanel data={data} />
    </div>
  )
}

export default MetricsPage