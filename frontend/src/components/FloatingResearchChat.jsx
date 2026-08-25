import { useState } from 'react'
import { MessageSquare, X, Sparkles } from 'lucide-react'

function FloatingResearchChat() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-blue-600 text-white shadow-lg shadow-blue-500/30 flex items-center justify-center hover:bg-blue-700 transition-colors z-40"
        title="Research Agent"
      >
        <MessageSquare size={22} />
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 w-80 bg-white rounded-2xl border border-slate-200 shadow-2xl z-50 animate-fadeIn overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-blue-600 text-white">
            <div className="flex items-center gap-2 text-sm font-bold">
              <Sparkles size={16} /> Research Agent
            </div>
            <button onClick={() => setOpen(false)} className="text-white/80 hover:text-white">
              <X size={16} />
            </button>
          </div>
          <div className="p-4 text-xs text-slate-600 leading-relaxed">
            The Research Agent is still in development. Once available, you'll be able to ask multi-part
            questions about your indexed documents here and get cited, source-grounded answers.
          </div>
        </div>
      )}
    </>
  )
}

export default FloatingResearchChat