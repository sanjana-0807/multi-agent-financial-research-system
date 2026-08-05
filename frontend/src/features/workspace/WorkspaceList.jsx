import WorkspaceCard from './WorkspaceCard.jsx'
import { Plus } from 'lucide-react'

const MOCK_SESSIONS = [
  { id: '1', name: 'Tesla Q4 2025 Analysis', description: 'Annual report analysis for Tesla Inc.', document_count: 3, created_at: '2026-07-28T10:30:00Z' },
  { id: '2', name: 'Apple FY 2024 Review', description: 'Financial review of Apple Inc. annual filings.', document_count: 2, created_at: '2026-07-25T14:15:00Z' },
  { id: '3', name: 'Microsoft vs Google Comparison', description: 'Comparative analysis of MSFT and GOOGL financials.', document_count: 4, created_at: '2026-07-20T09:00:00Z' },
]

function WorkspaceList() {
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
          <p className="text-gray-500">Your research sessions</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700">
          <Plus size={16} /> New Session
        </button>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {MOCK_SESSIONS.map((ws) => (
          <WorkspaceCard key={ws.id} workspace={ws} onClick={() => {}} />
        ))}
      </div>
    </div>
  )
}
export default WorkspaceList
