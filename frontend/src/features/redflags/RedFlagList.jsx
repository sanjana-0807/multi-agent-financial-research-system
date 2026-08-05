import { ShieldAlert } from 'lucide-react'
import RedFlagCard from './RedFlagCard.jsx'

// Renders a list of red flags. Shows an empty state if none exist.
// Expected shape: flags = [{ title, description, severity, category }, ...]
function RedFlagList({ flags }) {
  if (!flags || flags.length === 0) {
    return (
      <div className="text-center py-10">
        <ShieldAlert size={32} className="text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-400">No red flags detected.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {flags.map((flag, index) => (
        <RedFlagCard key={flag.id || index} flag={flag} />
      ))}
    </div>
  )
}

export default RedFlagList
