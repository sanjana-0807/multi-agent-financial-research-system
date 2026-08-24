import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { LogOut, User, Sparkles, Settings as SettingsIcon, ChevronDown, CheckCircle2, ShieldCheck, FileText } from 'lucide-react'
import { useAuth } from '../../features/auth/useAuth.js'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

function Navbar({ onOpenLogout }) {
  const { isAuthenticated, user, logout } = useAuth()
  const { extractionData, activeWorkspace } = useWorkspace()
  const location = useLocation()
  const navigate = useNavigate()

  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const dropdownRef = useRef(null)

  // Active session title
  const sessionName = activeWorkspace?.name || (extractionData?.company ? `${extractionData.company} FY ${extractionData.fiscal_year || 2025}` : null)

  // Format current page title from route path
  const pathName = location.pathname.substring(1) || 'dashboard'
  const pageTitle = pathName.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowProfileMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleConfirmLogout() {
    logout()
    setShowProfileMenu(false)
    setShowLogoutConfirm(false)
    navigate('/')
  }

  const userInitial = user?.initial || user?.name?.charAt(0)?.toUpperCase() || 'C'
  const userName = user?.name || 'Charitha'
  const userEmail = user?.email || 'charitha@ledgeriq.com'
  const userRole = user?.role || 'Senior Financial Analyst'

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 flex items-center justify-between px-6 sticky top-0 z-30 select-none">
      {/* Route Location & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <span className="hover:text-slate-600 transition-colors">Workspace</span>
          <span>/</span>
          <span className="text-slate-900 font-bold text-sm tracking-tight">{pageTitle}</span>
        </div>

        {sessionName && (
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/80 ml-2">
            <Sparkles size={12} className="text-blue-600 animate-pulse" />
            <span>Active Session: {sessionName}</span>
          </div>
        )}
      </div>

      {/* User Profile & Interactive Dropdown */}
      <div className="flex items-center gap-4">
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2.5 p-1.5 pr-3 rounded-full hover:bg-slate-100/80 border border-transparent hover:border-slate-200 transition-all cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 text-white font-bold text-sm flex items-center justify-center shadow-xs">
              {userInitial}
            </div>
            <div className="hidden md:block text-left">
              <div className="text-xs font-bold text-slate-800 leading-tight flex items-center gap-1">
                {userName}
                <ChevronDown size={12} className={`text-slate-400 transition-transform ${showProfileMenu ? 'rotate-180' : ''}`} />
              </div>
              <div className="text-[10px] text-slate-400 font-medium">Analyst</div>
            </div>
          </button>

          {/* Profile Dropdown Menu */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl border border-slate-200 shadow-xl p-3 z-50 animate-in fade-in zoom-in-95 duration-150">
              {/* Profile Card Header */}
              <div className="p-3 bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-xl border border-slate-100 flex items-center gap-3 mb-2">
                <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 text-white font-extrabold text-base flex items-center justify-center shadow-sm">
                  {userInitial}
                </div>
                <div className="overflow-hidden">
                  <h4 className="text-sm font-bold text-slate-900 truncate">{userName}</h4>
                  <p className="text-xs text-slate-500 truncate">{userEmail}</p>
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-700 bg-blue-100/70 px-1.5 py-0.2 rounded mt-1">
                    <ShieldCheck size={10} /> {userRole}
                  </span>
                </div>
              </div>

              {/* Menu Links */}
              <div className="space-y-1">
                <button
                  type="button"
                  onClick={() => {
                    setShowProfileMenu(false)
                    navigate('/settings')
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors text-left"
                >
                  <SettingsIcon size={15} className="text-slate-400" />
                  <span>Profile & Workspace Settings</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setShowProfileMenu(false)
                    navigate('/sessions')
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg transition-colors text-left"
                >
                  <FileText size={15} className="text-slate-400" />
                  <span>Manage Sessions</span>
                </button>

                <div className="my-1 border-t border-slate-100" />

                <button
                  type="button"
                  onClick={() => {
                    setShowProfileMenu(false)
                    if (onOpenLogout) {
                      onOpenLogout()
                    } else {
                      setShowLogoutConfirm(true)
                    }
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors text-left cursor-pointer"
                >
                  <LogOut size={15} className="text-rose-500" />
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Logout Confirmation Dialog Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-sm w-full space-y-4 shadow-xl">
            <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <LogOut size={24} />
            </div>
            <div className="text-center space-y-1">
              <h3 className="text-base font-bold text-slate-900">Log out of your account?</h3>
              <p className="text-xs text-slate-500">
                You will be redirected to the login page.
              </p>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmLogout}
                className="flex-1 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-colors shadow-sm shadow-rose-500/20"
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}

export default Navbar
