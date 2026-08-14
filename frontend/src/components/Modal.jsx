import { useEffect } from 'react'
import { X } from 'lucide-react'

function Modal({ open, onClose, title, subtitle, children, maxWidth = 'max-w-md' }) {
  // Close on ESC key press
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && open) {
        onClose?.()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm transition-opacity duration-300" 
        onClick={onClose} 
      />

      {/* Modal Dialog Card */}
      <div className={`relative w-full ${maxWidth} bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 z-10 transition-all transform scale-100 select-none`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
            {subtitle && <p className="text-xs font-medium text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Children Body */}
        <div>
          {children}
        </div>
      </div>
    </div>
  )
}

export default Modal

