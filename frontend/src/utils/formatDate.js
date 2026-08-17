// Formats a date string or Date object into a readable format.
// Usage: formatDate('2026-08-05T10:30:00Z') → "Aug 5, 2026"
//        formatDate('2026-08-05T10:30:00Z', true) → "Aug 5, 2026, 4:00 PM"
export function formatDate(dateInput, includeTime = false) {
  if (!dateInput) return 'N/A'

  const date = new Date(dateInput)
  if (isNaN(date.getTime())) return 'N/A'

  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(includeTime && { hour: 'numeric', minute: '2-digit' })
  }

  return date.toLocaleDateString('en-US', options)
}

// Returns relative time like "2 mins ago", "3 hours ago"
export function timeAgo(dateInput) {
  if (!dateInput) return ''

  const now = new Date()
  const date = new Date(dateInput)
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} mins ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  return `${Math.floor(seconds / 86400)} days ago`
}
