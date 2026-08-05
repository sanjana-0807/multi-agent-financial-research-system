import { GitCompare, Plus, X } from 'lucide-react'

// Lets users pick which companies/documents to compare.
// selectedIds is an array of document IDs, onCompare fires when ready.
function ComparisonSelector({ documents = [], selectedIds = [], onToggle, onCompare }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <GitCompare size={18} className="text-blue-600" />
        <h3 className="text-sm font-semibold text-gray-900">Select Companies to Compare</h3>
      </div>

      {documents.length === 0 ? (
        <p className="text-sm text-gray-400">No documents available. Upload financial reports first.</p>
      ) : (
        <div className="space-y-2 mb-4">
          {documents.map((doc) => {
            const isSelected = selectedIds.includes(doc.document_id)
            return (
              <button
                key={doc.document_id}
                onClick={() => onToggle(doc.document_id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm transition-colors ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <span className="truncate">{doc.company || doc.filename || doc.document_id}</span>
                {isSelected ? <X size={14} /> : <Plus size={14} className="text-gray-400" />}
              </button>
            )
          })}
        </div>
      )}

      <button
        onClick={onCompare}
        disabled={selectedIds.length < 2}
        className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Compare {selectedIds.length} {selectedIds.length === 1 ? 'Company' : 'Companies'}
      </button>
      {selectedIds.length < 2 && (
        <p className="text-xs text-gray-400 mt-2 text-center">Select at least 2 companies</p>
      )}
    </div>
  )
}

export default ComparisonSelector
