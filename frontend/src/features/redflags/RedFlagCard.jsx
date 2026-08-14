import { AlertTriangle, ShieldAlert, AlertCircle, Info, Tag } from 'lucide-react'
import SeverityBadge from './SeverityBadge.jsx'

function RedFlagCard({ flag = {} }) {
  const severity = (flag.severity || 'low').toLowerCase()
  
  const iconColors = {
    high: 'bg-rose-50 text-rose-600 border-rose-200/80',
    medium: 'bg-amber-50 text-amber-600 border-amber-200/80',
    low: 'bg-blue-50 text-blue-600 border-blue-200/80',
  }

  const borderAccents = {
    high: 'border-l-4 border-l-rose-500',
    medium: 'border-l-4 border-l-amber-500',
    low: 'border-l-4 border-l-blue-500',
  }

  const currentIconColor = iconColors[severity] || iconColors.low
  const currentBorderAccent = borderAccents[severity] || borderAccents.low

  return (
    <div className={`bg-white rounded-2xl p-5 border border-slate-200/80 ${currentBorderAccent} shadow-3d-subtle shadow-3d-hover transition-all duration-300 select-none overflow-hidden`}>
      <div className="flex items-start gap-4">
        <div className={`w-11 h-11 rounded-xl border flex items-center justify-center flex-shrink-0 shadow-2xs ${currentIconColor}`}>
          {severity === 'high' ? (
            <ShieldAlert size={22} className="animate-pulse" />
          ) : severity === 'medium' ? (
            <AlertTriangle size={20} />
          ) : (
            <Info size={20} />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <h4 className="text-base font-bold text-slate-900 tracking-tight leading-snug">
              {flag.title || 'Anomaly Detection Risk'}
            </h4>
            <SeverityBadge severity={flag.severity} />
          </div>

          <p className="text-xs font-medium text-slate-600 leading-relaxed mb-3">
            {flag.description || 'No detailed analysis narrative provided for this risk item.'}
          </p>

          {flag.category && (
            <div className="flex items-center gap-1.5 pt-2 border-t border-slate-100">
              <Tag size={12} className="text-slate-400" />
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                {flag.category}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RedFlagCard

