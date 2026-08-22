import { useState, useEffect } from 'react'
import MetricsPanel from '../features/extraction/MetricsPanel.jsx'
import { getExtraction } from '../api/extractionApi.js'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { useNavigate } from 'react-router-dom'
import Button from '../components/Button.jsx'
import { Upload, Inbox, Sparkles } from 'lucide-react'

function MetricsPage() {
  const { extractionData, setExtractionData } = useWorkspace()
  const [data, setData] = useState(extractionData)
  const [loading, setLoading] = useState(!extractionData)
  const navigate = useNavigate()

  useEffect(() => {
    if (extractionData && extractionData.company) {
      setData(extractionData)
      setLoading(false)
      return
    }

    getExtraction('D100')
      .then((res) => {
        if (res.data && res.data.company) {
          setData(res.data)
          setExtractionData(res.data)
        } else {
          setData(null)
        }
        setLoading(false)
      })
      .catch(() => {
        setData(null)
        setLoading(false)
      })
  }, [extractionData])

  const hasData = data && (data.revenue !== null || data.net_profit !== null || data.assets !== null)

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> KPI Metrics Engine
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Financial Metrics {data?.company ? `— ${data.company}` : ''}
          </h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Key financial indicators extracted directly from active document disclosures.
          </p>
        </div>

        <Button onClick={() => navigate('/upload')} icon={Upload} variant="outline" size="sm">
          Upload New Document
        </Button>
      </div>

      {!hasData && !loading ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center space-y-3 shadow-3d-subtle">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <Inbox size={24} />
          </div>
          <h3 className="text-base font-bold text-slate-800">No extracted metrics available</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Upload a financial document (PDF) to run the AI Extraction Agent and view financial metrics.
          </p>
          <Button onClick={() => navigate('/upload')} icon={Upload} variant="primary" size="sm" className="mt-2">
            Upload Document
          </Button>
        </div>
      ) : (
        <MetricsPanel data={data} />
      )}
    </div>
  )
}

export default MetricsPage