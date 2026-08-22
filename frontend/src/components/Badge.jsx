function Badge({ children, variant = 'default', dot = false }) {
  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    processed: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    warning: 'bg-amber-50 text-amber-700 border-amber-200/80',
    processing: 'bg-amber-50 text-amber-700 border-amber-200/80',
    danger: 'bg-rose-50 text-rose-700 border-rose-200/80',
    error: 'bg-rose-50 text-rose-700 border-rose-200/80',
    high: 'bg-rose-50 text-rose-700 border-rose-200/80',
    medium: 'bg-amber-50 text-amber-700 border-amber-200/80',
    low: 'bg-blue-50 text-blue-700 border-blue-200/80',
    info: 'bg-blue-50 text-blue-700 border-blue-200/80',
    pending: 'bg-slate-100 text-slate-600 border-slate-200',
  }

  const dotColors = {
    default: 'bg-slate-400',
    success: 'bg-emerald-500',
    processed: 'bg-emerald-500',
    warning: 'bg-amber-500 animate-pulse',
    processing: 'bg-amber-500 animate-pulse',
    danger: 'bg-rose-500',
    error: 'bg-rose-500',
    high: 'bg-rose-500 animate-pulse',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
    info: 'bg-blue-500',
    pending: 'bg-slate-400',
  }

  const currentStyle = variantStyles[variant] || variantStyles.default
  const currentDotColor = dotColors[variant] || dotColors.default

  const showDot = dot || ['processing', 'high', 'warning', 'processed', 'success'].includes(variant)

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStyle} transition-colors select-none`}>
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${currentDotColor}`} />
      )}
      {children}
    </span>
  )
}

export default Badge

