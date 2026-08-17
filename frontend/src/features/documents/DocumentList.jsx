import Badge from '../../components/Badge.jsx'
import { FileText, Inbox, Upload } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Button from '../../components/Button.jsx'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

const statusVariant = { processed: 'success', processing: 'warning', pending: 'default', failed: 'danger' }

function DocumentList() {
  const { uploadHistory } = useWorkspace()
  const navigate = useNavigate()

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Upload History</h1>
          <p className="text-gray-500">Previously uploaded documents.</p>
        </div>
        <Button onClick={() => navigate('/upload')} icon={Upload} variant="primary" size="sm">
          Upload New Document
        </Button>
      </div>

      {uploadHistory.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <Inbox size={24} />
          </div>
          <h3 className="text-base font-bold text-slate-800">No documents uploaded yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Upload your first financial disclosure (PDF) to view its ingestion and extraction status here.
          </p>
          <Button onClick={() => navigate('/upload')} icon={Upload} variant="outline" size="sm" className="mt-2">
            Go to Upload
          </Button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left text-gray-500 font-medium">Filename</th>
                <th className="px-4 py-3 text-left text-gray-500 font-medium">Company</th>
                <th className="px-4 py-3 text-left text-gray-500 font-medium">Uploaded</th>
                <th className="px-4 py-3 text-left text-gray-500 font-medium">Size</th>
                <th className="px-4 py-3 text-left text-gray-500 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {uploadHistory.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 flex items-center gap-2 text-gray-900">
                    <FileText size={14} className="text-gray-400" /> {doc.filename}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{doc.company || '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{doc.uploaded_at}</td>
                  <td className="px-4 py-3 text-gray-500">{doc.size}</td>
                  <td className="px-4 py-3">
                    <Badge variant={statusVariant[doc.status] || 'default'}>{doc.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default DocumentList
