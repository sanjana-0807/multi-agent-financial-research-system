import { Loader2 } from 'lucide-react'

function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  loading = false, 
  icon: Icon,
  className = '', 
  ...props 
}) {
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-200 rounded-xl select-none disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-blue-500/30'
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  }

  const variantStyles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0 active:bg-blue-800',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200/80 hover:-translate-y-0.5 active:translate-y-0',
    outline: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 hover:border-slate-400 hover:-translate-y-0.5 active:translate-y-0 shadow-2xs',
    danger: 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0',
    ghost: 'bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-900',
    success: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0',
  }

  const currentSize = sizeStyles[size] || sizeStyles.md
  const currentVariant = variantStyles[variant] || variantStyles.primary

  return (
    <button
      className={`${baseStyles} ${currentSize} ${currentVariant} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 size={16} className="animate-spin text-current" />
          <span>Processing...</span>
        </>
      ) : (
        <>
          {Icon && <Icon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} />}
          {children}
        </>
      )}
    </button>
  )
}

export default Button

