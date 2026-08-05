import Badge from '../../components/Badge.jsx'

// Maps severity levels to Badge variants for consistent coloring.
const SEVERITY_MAP = {
  high: { variant: 'danger', label: 'High' },
  medium: { variant: 'warning', label: 'Medium' },
  low: { variant: 'info', label: 'Low' },
}

function SeverityBadge({ severity }) {
  const config = SEVERITY_MAP[severity?.toLowerCase()] || SEVERITY_MAP.low
  return <Badge variant={config.variant}>{config.label}</Badge>
}

export default SeverityBadge
