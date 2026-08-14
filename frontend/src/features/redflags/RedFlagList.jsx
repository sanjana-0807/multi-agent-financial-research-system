import { useState } from 'react'
import { ShieldAlert, AlertTriangle, Info, CheckCircle2, Filter, Tag } from 'lucide-react'
import RedFlagCard from './RedFlagCard.jsx'

function RedFlagList({ flags = [] }) {
  const [activeSeverity, setActiveSeverity] = useState('all')
  const [activeCategory, setActiveCategory] = useState('all')

  if (!flags || flags.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-3d-subtle select-none">
        <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center mx-auto mb-3">
          <CheckCircle2 size={32} />
        </div>
        <h3 className="text-lg font-bold text-slate-900">No Financial Red Flags Detected</h3>
        <p className="text-xs font-medium text-slate-500 max-w-sm mx-auto mt-1">
          Automated rule scanner completed verification with 0 high-risk anomalies flagged.
        </p>
      </div>
    )
  }

  const highCount = flags.filter(f => (f.severity || '').toLowerCase() === 'high').length
  const mediumCount = flags.filter(f => (f.severity || '').toLowerCase() === 'medium').length
  const lowCount = flags.filter(f => (f.severity || '').toLowerCase() === 'low').length

  const categories = Array.from(new Set(flags.map(f => f.category).filter(Boolean)))

  const filteredFlags = flags.filter(f => {
    const matchesSeverity = activeSeverity === 'all' || (f.severity || '').toLowerCase() === activeSeverity
    const matchesCategory = activeCategory === 'all' || f.category === activeCategory
    return matchesSeverity && matchesCategory
  })

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Summary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div 
          onClick={() => setActiveSeverity(activeSeverity === 'high' ? 'all' : 'high')}
          className={`cursor-pointer bg-white rounded-2xl p-4 border transition-all ${
            activeSeverity === 'high' ? 'border-rose-400 ring-2 ring-rose-500/20 bg-rose-50/20 shadow-md' : 'border-slate-200/80 shadow-3d-subtle hover:border-rose-300'
          } flex items-center justify-between`}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 border border-rose-100 flex items-center justify-center font-bold">
              <ShieldAlert size={20} className="animate-pulse" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">High Risk</div>
              <div className="text-xl font-extrabold text-slate-900">{highCount} Alerts</div>
            </div>
          </div>
        </div>

        <div 
          onClick={() => setActiveSeverity(activeSeverity === 'medium' ? 'all' : 'medium')}
          className={`cursor-pointer bg-white rounded-2xl p-4 border transition-all ${
            activeSeverity === 'medium' ? 'border-amber-400 ring-2 ring-amber-500/20 bg-amber-50/20 shadow-md' : 'border-slate-200/80 shadow-3d-subtle hover:border-amber-300'
          } flex items-center justify-between`}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 border border-amber-100 flex items-center justify-center font-bold">
              <AlertTriangle size={20} />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Medium Risk</div>
              <div className="text-xl font-extrabold text-slate-900">{mediumCount} Alerts</div>
            </div>
          </div>
        </div>

        <div 
          onClick={() => setActiveSeverity(activeSeverity === 'low' ? 'all' : 'low')}
          className={`cursor-pointer bg-white rounded-2xl p-4 border transition-all ${
            activeSeverity === 'low' ? 'border-blue-400 ring-2 ring-blue-500/20 bg-blue-50/20 shadow-md' : 'border-slate-200/80 shadow-3d-subtle hover:border-blue-300'
          } flex items-center justify-between`}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center font-bold">
              <Info size={20} />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Low Risk</div>
              <div className="text-xl font-extrabold text-slate-900">{lowCount} Alerts</div>
            </div>
          </div>
        </div>
      </div>

      {/* Severity & Category Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white rounded-2xl p-3 border border-slate-200/80 shadow-3d-subtle">
        <div className="flex items-center gap-2">
          <Filter size={15} className="text-slate-400 ml-2" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Severity:</span>
          <div className="flex items-center gap-1">
            {[
              { id: 'all', label: `All (${flags.length})` },
              { id: 'high', label: `High (${highCount})` },
              { id: 'medium', label: `Medium (${mediumCount})` },
              { id: 'low', label: `Low (${lowCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSeverity(tab.id)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  activeSeverity === tab.id
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {categories.length > 0 && (
          <div className="flex items-center gap-2 border-t sm:border-t-0 sm:border-l border-slate-100 pt-2 sm:pt-0 sm:pl-3">
            <Tag size={14} className="text-slate-400" />
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Category:</span>
            <select
              value={activeCategory}
              onChange={(e) => setActiveCategory(e.target.value)}
              className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 outline-none"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Red Flag Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredFlags.map((flag, index) => (
          <RedFlagCard key={flag.id || index} flag={flag} />
        ))}
      </div>
    </div>
  )
}

export default RedFlagList


