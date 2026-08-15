import { useState, useEffect } from 'react'
import RatiosTable from '../features/extraction/RatiosTable.jsx'
import { getExtraction } from '../api/extractionApi.js'
import { dashboardData as mockData } from '../data/mockDashboardData.js'

function RatiosPage() {
  const [data, setData] = useState(mockData)

  useEffect(() => {
    getExtraction('D100')
      .then((res) => setData(res.data))
      .catch(() => setData(mockData))
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Financial Ratios</h1>
      <p className="text-gray-500 mb-6">Key ratios calculated from extracted financial data.</p>
      <RatiosTable ratios={data.ratios} />
    </div>
  )
}

export default RatiosPage