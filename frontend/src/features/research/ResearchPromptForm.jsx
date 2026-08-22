import { useState } from 'react'
import { Send, Cpu, User, Sparkles, FileText, X, CheckCircle2, ExternalLink } from 'lucide-react'
import Button from '../../components/Button.jsx'

const MOCK_MESSAGES = [
  { role: 'user', text: 'What was Tesla\'s revenue in FY 2025?' },
  { 
    role: 'assistant', 
    text: 'Based on the uploaded 10-K filing, Tesla\'s total revenue for FY 2025 was $879,891 thousand (approximately $879.9 million). This represents a 23% increase compared to the previous fiscal year.', 
    citation: 'Tesla 10-K FY25 • Page 42',
    snippet: 'Item 7. Management\'s Discussion and Analysis: Total Automotive Revenues reached $879,891 thousand in FY 2025, driven by Model Y volume expansion and energy storage deployment.',
    score: '98.4%'
  },
  { role: 'user', text: 'How does their profit margin compare to industry average?' },
  { 
    role: 'assistant', 
    text: 'Tesla\'s net profit margin of 18.9% significantly exceeds the automotive industry average of 12.3%. This reflects strong operational efficiency and premium pricing power in both the automotive and energy segments.', 
    citation: 'Multi-Agent Ratio Tool • Benchmark V2',
    snippet: 'Ratio Tool Computation: Net Income ($74,982K) / Total Revenue ($879,891K) = 18.86% vs Industry Peer Median (12.30%).',
    score: '96.2%'
  },
]

const SUGGESTED_PROMPTS = [
  'What is Tesla\'s net profit margin for FY 2025?',
  'Summarize the primary red flag risks found in filings.',
  'How does debt-to-equity ratio compare across companies?',
  'What was operating cash flow growth in Q4?',
]

function ResearchPromptForm() {
  const [messages, setMessages] = useState(MOCK_MESSAGES)
  const [prompt, setPrompt] = useState('')
  const [activeCitation, setActiveCitation] = useState(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (!prompt.trim()) return
    setMessages([
      ...messages, 
      { role: 'user', text: prompt },
      { 
        role: 'assistant', 
        text: `Analysis complete for "${prompt}". Extracted disclosures confirm strong balance sheet liquidity and compliant reporting metrics.`,
        citation: 'ChromaDB RAG Index • Vector Doc #84f2',
        snippet: `Vector Chunk Similarity Index #84f2: Match confidence high for query "${prompt}". Relevant disclosures validated from 10-K Section 4.`,
        score: '99.1%'
      }
    ])
    setPrompt('')
  }

  function handleSelectSuggested(text) {
    setPrompt(text)
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6 flex flex-col h-[calc(100vh-6rem)] animate-fadeIn select-none">
      {/* Header */}
      <div className="flex items-center justify-between bg-white rounded-2xl p-5 border border-slate-200/80 shadow-3d-subtle flex-shrink-0">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-0.5">
            <Sparkles size={14} /> Multi-Agent AI Assistant
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Financial Document Research Chat</h1>
          <p className="text-xs font-medium text-slate-500 mt-0.5">
            Ask questions about uploaded 10-K filings, financial metrics, and balance sheet risks.
          </p>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/80">
          <Cpu size={14} className="text-blue-600 animate-pulse" />
          <span>RAG Vector Search Active</span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle overflow-y-auto space-y-5 custom-scrollbar">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 max-w-[85%] ${
              msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''
            }`}
          >
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shadow-xs flex-shrink-0 ${
              msg.role === 'user' ? 'bg-slate-900 text-white' : 'bg-blue-600 text-white shadow-blue-500/20'
            }`}>
              {msg.role === 'user' ? <User size={18} /> : <Cpu size={18} />}
            </div>

            <div className={`rounded-2xl p-4 text-xs font-medium leading-relaxed ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-50 text-slate-800 border border-slate-200/80 shadow-2xs'
            }`}>
              <div className="font-semibold mb-1 text-[11px] opacity-80 uppercase tracking-wider">
                {msg.role === 'user' ? 'Financial Analyst' : 'Multi-Agent Research Agent'}
              </div>
              <p className="text-sm">{msg.text}</p>

              {msg.citation && (
                <div 
                  onClick={() => setActiveCitation(msg)}
                  className="mt-3.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-bold text-blue-600 hover:text-blue-800 cursor-pointer group"
                >
                  <span className="flex items-center gap-1.5">
                    <FileText size={12} />
                    <span>Citation: {msg.citation}</span>
                  </span>
                  <span className="flex items-center gap-1 text-slate-400 group-hover:text-blue-600">
                    <span>Inspect Source</span>
                    <ExternalLink size={10} />
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Suggested Prompt Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 flex-shrink-0">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex-shrink-0">Suggested:</span>
        {SUGGESTED_PROMPTS.map((txt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectSuggested(txt)}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-white border border-slate-200/80 text-slate-600 hover:border-blue-300 hover:text-blue-600 transition-colors shadow-2xs flex-shrink-0"
          >
            {txt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex items-center gap-3 bg-white rounded-2xl p-3 border border-slate-200/80 shadow-3d-subtle flex-shrink-0">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={1}
          placeholder="Ask a question about Tesla, Apple, or uploaded financial reports..."
          className="flex-1 text-sm font-medium text-slate-800 placeholder-slate-400 bg-transparent resize-none outline-none py-1.5 px-2"
        />
        <Button
          type="submit"
          disabled={!prompt.trim()}
          icon={Send}
          variant="primary"
          size="md"
        >
          Send
        </Button>
      </form>

      {/* Interactive Citation Source Drawer Modal */}
      {activeCitation && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-sm animate-fadeIn"
          onClick={() => setActiveCitation(null)}
        >
          <div 
            className="relative w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 transition-all transform scale-100 animate-scaleUp select-none"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <FileText size={18} className="text-blue-600" />
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900">RAG Source Grounding Verification</h3>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{activeCitation.citation}</span>
                </div>
              </div>
              <button 
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>Extracted Document Text Chunk</span>
                  <span className="text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full text-[10px]">
                    {activeCitation.score || '98% Match'}
                  </span>
                </div>
                <p className="text-xs font-medium text-slate-600 leading-relaxed italic bg-white p-3 rounded-lg border border-slate-200/80">
                  "{activeCitation.snippet || activeCitation.text}"
                </p>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setActiveCitation(null)}
                  className="px-4 py-2 bg-slate-900 text-white text-xs font-bold rounded-xl hover:bg-slate-800 transition-colors"
                >
                  Done Inspecting
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ResearchPromptForm


