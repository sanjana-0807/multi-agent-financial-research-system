import { useState } from 'react'
import Modal from '../../components/Modal.jsx'

function CreateWorkspaceModal({ open, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [ticker, setTicker] = useState('')
  const [industry, setIndustry] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim() || !companyName.trim() || !ticker.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await onCreate({
        name: name.trim(),
        description: description.trim(),
        objective: description.trim(),
        companyName: companyName.trim(),
        ticker: ticker.trim().toUpperCase(),
        industry: industry.trim() || undefined,
      })
      setName('')
      setDescription('')
      setCompanyName('')
      setTicker('')
      setIndustry('')
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create session')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New Research Session">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Session Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g. Tesla Q4 2025 Analysis"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Description (optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            placeholder="Brief description of this research session"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
              placeholder="Tesla Inc."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              required
              maxLength={10}
              placeholder="TSLA"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Industry (optional)</label>
          <input
            type="text"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="Automotive"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {error && (
          <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting || !name.trim() || !companyName.trim() || !ticker.trim()}
          className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? 'Creating...' : 'Create Session'}
        </button>
      </form>
    </Modal>
  )
}

export default CreateWorkspaceModal