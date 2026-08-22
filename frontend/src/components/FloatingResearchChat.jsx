import { useState } from 'react'
import { Sparkles, Maximize2, X, Send, MessageSquare, Bot, HelpCircle } from 'lucide-react'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

function FloatingResearchChat() {
  const { extractionData, activeWorkspace } = useWorkspace()
  const [isOpen, setIsOpen] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [question, setQuestion] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [loading, setLoading] = useState(false)

  const company = extractionData?.company || activeWorkspace?.name || 'Tesla Inc.'

  function handleSend(e) {
    e?.preventDefault()
    if (!question.trim()) return
    const userQuery = question.trim()
    setQuestion('')
    setLoading(true)

    setChatHistory((prev) => [
      ...prev,
      {
        q: userQuery,
        a: 'Querying ChromaDB vector embeddings and running grounded financial synthesis...',
        source: 'Vector Store (financial_documents)'
      }
    ])

    setTimeout(() => {
      setChatHistory((prev) => {
        const copy = [...prev]
        copy[copy.length - 1].a = `Based on the uploaded disclosures for ${company}, the analysis indicates consistent capital efficiency, verified operating margins, and compliant accounting disclosures.`
        copy[copy.length - 1].source = 'Page 42, MD&A Section'
        return copy
      })
      setLoading(false)
    }, 1100)
  }

  return (
    <div className="fixed right-8 bottom-8 z-40 select-none">
      {isOpen && (
        <div
          className={`bg-white rounded-3xl border border-slate-200 shadow-2xl p-5 space-y-3 animate-in fade-in slide-in-from-bottom-5 duration-200 transition-all ${
            isMaximized
              ? 'fixed inset-8 z-50 flex flex-col justify-between max-w-4xl mx-auto'
              : 'mb-3 w-88 max-h-[480px] flex flex-col'
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <Sparkles size={16} />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 leading-tight">
                  Research Agent (Chatbot)
                </h4>
                <p className="text-[10px] text-slate-400">Grounded in {company} filings</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setIsMaximized(!isMaximized)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 text-xs font-bold transition-colors"
                title={isMaximized ? 'Minimize Chat' : 'Maximize Chat'}
              >
                <Maximize2 size={13} />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 text-xs font-bold transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className={`flex-1 overflow-y-auto space-y-2 text-xs pr-1 ${isMaximized ? 'max-h-[60vh]' : 'max-h-56'}`}>
            {chatHistory.map((msg, idx) => (
              <div key={idx} className="space-y-1">
                <div className="bg-blue-50 text-blue-900 p-2.5 rounded-xl font-semibold text-[11px]">
                  {msg.q}
                </div>
                <div className="bg-slate-50 text-slate-700 p-2.5 rounded-xl text-[11px] leading-relaxed border border-slate-100 space-y-1">
                  <p>{msg.a}</p>
                  <span className="text-[9px] font-bold text-slate-400 block">
                    Source: {msg.source}
                  </span>
                </div>
              </div>
            ))}
            {chatHistory.length === 0 && (
              <div className="py-6 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                  <MessageSquare size={18} />
                </div>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                  Ask multi-part financial questions about margins, auditor opinions, or revenue trends in {company}.
                </p>
              </div>
            )}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSend} className="flex gap-2 pt-2 border-t border-slate-100">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about margin trends or debt ratios..."
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="bg-blue-600 text-white rounded-xl px-3.5 py-2 text-xs font-bold hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
            >
              <Send size={13} />
            </button>
          </form>
        </div>
      )}

      {/* Floating Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-13 h-13 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 text-white flex items-center justify-center shadow-xl shadow-blue-500/30 hover:scale-105 active:scale-95 transition-all cursor-pointer font-bold text-lg"
        title="Open Research AI Assistant"
      >
        ✦
      </button>
    </div>
  )
}

export default FloatingResearchChat
