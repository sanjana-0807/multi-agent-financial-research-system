import { useState } from 'react'
import { Send } from 'lucide-react'

const MOCK_MESSAGES = [
  { role: 'user', text: 'What was Tesla\'s revenue in FY 2025?' },
  { role: 'assistant', text: 'Based on the uploaded 10-K filing, Tesla\'s total revenue for FY 2025 was $879,891 thousand (approximately $879.9 million). This represents a 23% increase compared to the previous fiscal year.' },
  { role: 'user', text: 'How does their profit margin compare to industry average?' },
  { role: 'assistant', text: 'Tesla\'s net profit margin of 18.9% significantly exceeds the automotive industry average of 12.3%. This reflects strong operational efficiency and premium pricing power in both the automotive and energy segments.' },
]

function ResearchPromptForm() {
  const [messages, setMessages] = useState(MOCK_MESSAGES)
  const [prompt, setPrompt] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!prompt.trim()) return
    setMessages([...messages, { role: 'user', text: prompt }])
    setPrompt('')
  }

  return (
    <div className="p-6 flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Research Chat</h1>
        <p className="text-gray-500">Ask questions about uploaded financial documents.</p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-3 text-sm max-w-[80%] ${
              msg.role === 'user'
                ? 'bg-blue-50 text-blue-900 ml-auto'
                : 'bg-gray-50 text-gray-700'
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={2}
          placeholder="Ask about financial data..."
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!prompt.trim()}
          className="bg-blue-600 text-white rounded-lg px-4 hover:bg-blue-700 disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  )
}
export default ResearchPromptForm
