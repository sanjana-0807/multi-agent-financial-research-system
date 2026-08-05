function Button({ children, variant = 'primary', disabled, ...props }) {
  const base = 'rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
    danger: 'bg-red-600 text-white hover:bg-red-700'
  }

  return (
    <button
      className={`${base} ${variants[variant]}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}

export default Button
