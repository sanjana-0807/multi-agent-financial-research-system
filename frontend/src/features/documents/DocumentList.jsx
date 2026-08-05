import Badge from '../../components/Badge.jsx'
import { FileText } from 'lucide-react'

const MOCK_DOCUMENTS = [
  { id: '1', filename: 'tesla_10k_2025.pdf', company: 'Tesla Inc.', uploaded_at: '2026-07-28', status: 'processed', size: '2.4 MB' },
  { id: '2', filename: 'apple_annual_2024.pdf', company: 'Apple Inc.', uploaded_at: '2026-07-25', status: 'processed', size: '3.1 MB' },
  { id: '3', filename: 'msft_10k_2025.pdf', company: 'Microsoft Corp.', uploaded_at: '2026-07-20', status: 'processing', size: '2.8 MB' },
  { id: '4', filename: 'googl_annual_2025.pdf', company: 'Alphabet Inc.', uploaded_at: '2026-07-18', status: 'pending', size: '4.2 MB' },
]

const statusVariant = { processed: 'success', processing: 'warning', pending: 'default' }

function DocumentList() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Upload History</h1>
      <p className="text-gray-500 mb-6">Previously uploaded documents.</p>
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
            {MOCK_DOCUMENTS.map((doc) => (
              <tr key={doc.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 flex items-center gap-2 text-gray-900">
                  <FileText size={14} className="text-gray-400" /> {doc.filename}
                </td>
                <td className="px-4 py-3 text-gray-700">{doc.company}</td>
                <td className="px-4 py-3 text-gray-500">{doc.uploaded_at}</td>
                <td className="px-4 py-3 text-gray-500">{doc.size}</td>
                <td className="px-4 py-3"><Badge variant={statusVariant[doc.status]}>{doc.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
export default DocumentList
