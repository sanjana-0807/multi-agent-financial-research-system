import { Download } from 'lucide-react'
import { downloadReport } from '../../api/reportApi.js'
import { useState } from 'react'

// Button that downloads the generated report as a file.
// Handles the blob response and triggers a browser download.
function ReportExportButton({ reportId, filename = 'financial-report.pdf' }) {
  const [downloading, setDownloading] = useState(false)

  async function handleDownload() {
    if (!reportId) return
    setDownloading(true)
    try {
      const res = await downloadReport(reportId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      console.error('Download failed')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={!reportId || downloading}
      className="flex items-center gap-2 bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <Download size={16} />
      {downloading ? 'Downloading...' : 'Export Report'}
    </button>
  )
}

export default ReportExportButton
