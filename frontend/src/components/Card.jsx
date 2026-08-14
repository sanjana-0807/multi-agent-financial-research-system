function Card({ 
  children, 
  title, 
  subtitle, 
  action, 
  hover3D = false, 
  glass = false,
  className = '', 
  padding = 'p-6',
  ...props 
}) {
  const baseStyles = 'rounded-2xl transition-all duration-300 overflow-hidden'
  const borderStyles = 'border border-slate-200/80'
  const bgStyles = glass ? 'glass-card-light' : 'bg-white'
  const shadowStyles = hover3D ? 'shadow-3d-subtle shadow-3d-hover hover:border-blue-300/80' : 'shadow-3d-subtle'

  return (
    <div className={`${baseStyles} ${bgStyles} ${borderStyles} ${shadowStyles} ${padding} ${className}`} {...props}>
      {(title || subtitle || action) && (
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
          <div>
            {title && <h3 className="text-base font-bold text-slate-900 tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs font-medium text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

export default Card

