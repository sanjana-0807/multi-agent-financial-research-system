import { useState, useEffect } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import Sidebar from './Sidebar.jsx'
import Navbar from './Navbar.jsx'
import FloatingResearchChat from '../FloatingResearchChat.jsx'
import { useAuth } from '../../features/auth/useAuth.js'

function AppLayout() {
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

  // Track root entry page and intercept back button at the main sessions page
  useEffect(() => {
    if (location.pathname === '/sessions') {
      window.history.pushState({ isRoot: true }, '', location.pathname)

      const handlePopState = () => {
        if (location.pathname === '/sessions') {
          window.history.pushState({ isRoot: true }, '', location.pathname)
          setShowLogoutConfirm(true)
        }
      }

      window.addEventListener('popstate', handlePopState)
      return () => window.removeEventListener('popstate', handlePopState)
    }
  }, [location.pathname])

  function handleConfirmLogout() {
    logout()
    setShowLogoutConfirm(false)
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar onOpenLogout={() => setShowLogoutConfirm(true)} />
        <main className="flex-1">
          <Outlet />
        </main>
        {/* Global Floating Research Chatbot Widget */}
        <FloatingResearchChat />
      </div>

      {/* Global Logout Confirmation Dialog */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn select-none">
          <div className="bg-white rounded-3xl border border-slate-200 p-6 max-w-sm w-full space-y-4 shadow-2xl text-center">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto font-bold">
              <LogOut size={24} />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-900">Log out of your session?</h3>
              <p className="text-xs text-slate-500">
                You've reached the beginning of your workspace history. Do you want to log out?
              </p>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmLogout}
                className="flex-1 px-4 py-2.5 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 transition-colors shadow-sm shadow-rose-500/20 cursor-pointer"
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AppLayout
