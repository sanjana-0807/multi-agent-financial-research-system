import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Briefcase, Upload, Clock, History,
  BarChart3, Percent, MessageSquare, AlertTriangle, GitCompare, FileText, Settings,
  PanelLeftClose
} from 'lucide-react'

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Workspace', path: '/workspace', icon: Briefcase },
  { name: 'Upload', path: '/upload', icon: Upload },
  { name: 'Sessions', path: '/sessions', icon: Clock },
  { name: 'Upload History', path: '/upload-history', icon: History },
  { name: 'Metrics', path: '/metrics', icon: BarChart3 },
  { name: 'Ratios', path: '/ratios', icon: Percent },
  { name: 'Chat', path: '/chat', icon: MessageSquare },
  { name: 'Red Flags', path: '/red-flags', icon: AlertTriangle },
  { name: 'Comparison', path: '/comparison', icon: GitCompare },
  { name: 'Report', path: '/report', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
]

function Sidebar() {
  return (
    <div className="w-60 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0">
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-100">
        <LayoutDashboard size={20} className="text-blue-600" />
        <span className="font-semibold text-gray-900 text-[15px]">Financial Dashboard</span>
      </div>

      <nav className="flex-1 px-3 py-3 overflow-y-auto">
        {navItems.map(({ name, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm mb-1 transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
              }`
            }
          >
            <Icon size={16} />
            {name}
          </NavLink>
        ))}
      </nav>

      <button className="flex items-center gap-2 px-5 py-4 border-t border-gray-100 text-gray-400 hover:text-gray-600 text-sm">
        <PanelLeftClose size={16} />
      </button>
    </div>
  )
}
export default Sidebar
