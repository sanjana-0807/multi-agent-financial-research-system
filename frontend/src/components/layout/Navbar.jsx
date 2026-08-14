import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { LogOut, Bell, Search, User, Sparkles, X, ArrowRight, FileText, ShieldAlert, BarChart2, MessageSquare, CheckCircle2, AlertTriangle } from 'lucide-react'
import { useAuth } from '../../features/auth/useAuth.js'

function Navbar() {
  const { isAuthenticated, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Format current page title from route path
  const pathName = location.pathname.substring(1) || 'dashboard'
  const pageTitle = pathName.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

  // Global Keyboard Shortcut Listener for ⌘K / Ctrl+K
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsSearchOpen(prev => !prev)
      }
      if (e.key === 'Escape') {
        setIsSearchOpen(false)
        setShowNotifications(false)
        setShowLogoutConfirm(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const SEARCH_LINKS = [
    { label: 'Financial Dashboard', path: '/dashboard', icon: BarChart2, tag: 'Overview' },
    { label: 'Extracted Metrics', path: '/metrics', icon: FileText, tag: 'Data' },
    { label: 'Financial Ratios', path: '/ratios', icon: Sparkles, tag: 'Analytics' },
    { label: 'Red Flag Scanner', path: '/red-flags', icon: ShieldAlert, tag: 'Risk Alerts' },
    { label: 'Company Comparison', path: '/comparison', icon: BarChart2, tag: 'Matrix' },
    { label: 'AI Research Assistant', path: '/chat', icon: MessageSquare, tag: 'RAG Q&A' },
    { label: 'Executive Report', path: '/report', icon: FileText, tag: 'Synthesis' },
  ]

  const filteredLinks = SEARCH_LINKS.filter(item => 
    item.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.tag.toLowerCase().includes(searchQuery.toLowerCase())
  )

  function handleNavigate(path) {
    navigate(path)
    setIsSearchOpen(false)
    setSearchQuery('')
  }

  function handleConfirmLogout() {
    logout()
    setShowLogoutConfirm(false)
    navigate('/')
  }

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 flex items-center justify-between px-6 sticky top-0 z-30 shadow-2xs select-none">
      {/* Route Location & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span className="hover:text-slate-600 transition-colors">Platform</span>
          <span>/</span>
          <span className="text-slate-900 font-bold text-sm tracking-tight">{pageTitle}</span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/80 ml-2">
          <Sparkles size={12} className="text-blue-600 animate-pulse" />
          <span>Active Session: Tesla FY 2025</span>
        </div>
      </div>

      {/* Global Actions & User Profile */}
      <div className="flex items-center gap-4">
        {/* Command Palette Trigger Input */}
        <div 
          onClick={() => setIsSearchOpen(true)}
          className="hidden sm:flex items-center gap-2 bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 text-xs text-slate-400 w-56 hover:border-blue-300 hover:bg-white transition-all cursor-pointer shadow-2xs"
        >
          <Search size={14} className="text-slate-400" />
          <span>Search metrics, filings...</span>
          <kbd className="ml-auto text-[10px] font-mono bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-400">⌘K</kbd>
        </div>

        {/* Notifications Bell */}
        <div className="relative">
          <button 
            type="button"
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative text-slate-400 hover:text-slate-700 p-2 rounded-xl hover:bg-slate-100 transition-colors"
            title="Notifications"
          >
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          </button>

          {/* Notifications Popover Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl border border-slate-200 shadow-2xl p-4 z-40 space-y-3 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">System Notifications</span>
                <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">2 New</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-2.5">
                  <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold text-slate-800">10-K Parsing Complete</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Tesla FY 2025 document indexed in ChromaDB vector store.</div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-2.5">
                  <Sparkles size={16} className="text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold text-slate-800">RAG Vector Agent Ready</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Ready to answer financial questions for active session.</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="h-5 w-px bg-slate-200" />

        {/* User Auth Section */}
        {isAuthenticated ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-xs">
                AU
              </div>
              <div className="hidden lg:block text-left">
                <div className="text-xs font-bold text-slate-900 leading-tight">Admin User</div>
                <div className="text-[10px] font-medium text-slate-400">Financial Analyst</div>
              </div>
            </div>

            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-rose-600 p-2 rounded-xl hover:bg-rose-50 transition-colors"
              title="Logout"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center">
              <User size={16} />
            </div>
            <span className="text-xs font-semibold text-slate-600">Guest Analyst</span>
          </div>
        )}
      </div>

      {/* Logout Confirmation Dialogue Modal */}
      {showLogoutConfirm && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-sm animate-fadeIn"
          onClick={() => setShowLogoutConfirm(false)}
        >
          <div 
            className="relative w-full max-w-sm bg-white rounded-2xl border border-slate-200 shadow-2xl p-6 transition-all transform scale-100 animate-scaleUp select-none"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600 font-bold flex-shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900 tracking-tight">Do you want to logout?</h3>
                <p className="text-xs font-medium text-slate-500 mt-0.5">
                  Your session will be closed and you will return to the landing page.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-100 mt-4">
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(false)}
                className="px-4 py-2 text-xs font-bold text-slate-600 bg-slate-100 rounded-xl hover:bg-slate-200 transition-colors"
              >
                No, Stay
              </button>

              <button
                type="button"
                onClick={handleConfirmLogout}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 rounded-xl hover:bg-rose-700 transition-colors shadow-sm"
              >
                Yes, Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Command Palette Search Modal Overlay (⌘K) */}
      {isSearchOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-slate-950/40 backdrop-blur-sm animate-fadeIn"
          onClick={() => setIsSearchOpen(false)}
        >
          <div 
            className="relative w-full max-w-xl bg-white rounded-2xl border border-slate-200 shadow-2xl overflow-hidden animate-scaleUp"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search Input Bar */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100 bg-slate-50/50">
              <Search size={20} className="text-blue-600" />
              <input
                type="text"
                autoFocus
                placeholder="Type to search platform features, metrics, or filings (ESC to close)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full text-sm font-medium text-slate-900 placeholder-slate-400 bg-transparent outline-none"
              />
              <button 
                onClick={() => setIsSearchOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Results List */}
            <div className="p-3 max-h-80 overflow-y-auto space-y-1">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Quick Platform Navigation
              </div>

              {filteredLinks.map((item, idx) => {
                const Icon = item.icon
                return (
                  <div
                    key={idx}
                    onClick={() => handleNavigate(item.path)}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-blue-50/60 hover:border-blue-100 border border-transparent cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold group-hover:bg-blue-600 group-hover:text-white transition-colors">
                        <Icon size={16} />
                      </div>
                      <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                        {item.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-700">
                        {item.tag}
                      </span>
                      <ArrowRight size={14} className="text-slate-300 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                )
              })}

              {filteredLinks.length === 0 && (
                <div className="p-6 text-center text-xs text-slate-400 font-medium">
                  No matching platform features found for "{searchQuery}".
                </div>
              )}
            </div>

            <div className="bg-slate-50 px-4 py-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span>Use <kbd className="font-mono bg-white px-1 border rounded">↑</kbd> <kbd className="font-mono bg-white px-1 border rounded">↓</kbd> to navigate</span>
              <span>Press <kbd className="font-mono bg-white px-1 border rounded">ESC</kbd> to close</span>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}

export default Navbar



