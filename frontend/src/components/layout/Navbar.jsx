import { LogOut, Bell } from 'lucide-react'
import { useAuth } from '../../features/auth/useAuth.js'

function Navbar() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="text-sm text-gray-500">
        Multi-Agent Financial Research
      </div>

      {isAuthenticated && (
        <div className="flex items-center gap-3">
          <button className="text-gray-400 hover:text-gray-600 transition-colors">
            <Bell size={18} />
          </button>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      )}
    </header>
  )
}

export default Navbar
