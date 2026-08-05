import { FileText } from 'lucide-react'

// Renders an inline citation tag linking back to a source document.
// Usage: <CitationTag source="10-K Filing" page={42} />
function CitationTag({ source, page, onClick }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 text-blue-600 text-xs font-medium hover:bg-blue-100 transition-colors"
    >
      <FileText size={10} />
      {source}{page ? `, p.${page}` : ''}
    </button>
  )
}

export default CitationTag
