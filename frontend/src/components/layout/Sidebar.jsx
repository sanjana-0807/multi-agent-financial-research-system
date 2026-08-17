import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, Clock, History,
  BarChart3, Percent, MessageSquare, AlertTriangle, GitCompare, FileText, Settings,
  Cpu, Sparkles, ChevronRight
} from 'lucide-react'

const navItems = [
  { name: 'Upload', path: '/upload', icon: Upload },
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Upload History', path: '/upload-history', icon: History },
  { name: 'Metrics', path: '/metrics', icon: BarChart3 },
  { name: 'Ratios', path: '/ratios', icon: Percent },
  { name: 'Sessions', path: '/sessions', icon: Clock },
  { name: 'Chat', path: '/chat', icon: MessageSquare },
  { name: 'Red Flags', path: '/red-flags', icon: AlertTriangle },
  { name: 'Comparison', path: '/comparison', icon: GitCompare },
  { name: 'Report', path: '/report', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
]

function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col h-screen sticky top-0 z-30 select-none shadow-3d-subtle">
      {/* Header Branding */}
      <div className="px-5 py-5 border-b border-slate-100 bg-gradient-to-b from-slate-50/50 to-transparent">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Cpu size={22} className="animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1">
              <Sparkles size={11} /> AI Analysis Platform
            </span>
            <h1 className="font-extrabold text-slate-900 text-sm leading-snug tracking-tight">
              Multi-Agent AI
            </h1>
            <p className="text-[11px] font-medium text-slate-400">Financial Research</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Navigation Menu
        </div>
        {navItems.map(({ name, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `group relative flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                isActive
                  ? 'bg-blue-50 text-blue-600 border border-blue-200/80 shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div className="flex items-center gap-3">
                  <Icon 
                    size={18} 
                    className={`transition-colors ${
                      isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`} 
                  />
                  <span>{name}</span>
                </div>
                {isActive && (
                  <ChevronRight size={14} className="text-blue-600" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between p-2.5 rounded-xl bg-white border border-slate-200/80 shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold text-slate-700">Multi-Agent Engine</span>
          </div>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            Active
          </span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar

