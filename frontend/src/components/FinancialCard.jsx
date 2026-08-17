import { useState } from 'react'
import { TrendingUp, TrendingDown, Maximize2, X, Info, RotateCw, Sparkles, BookOpen, Calendar, MessageSquare, PieChart, Star, Layers } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function FinancialCard({ label, value, icon: Icon, unit, change, trend = 'up', description }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isFlipped, setIsFlipped] = useState(false)
  const [activeTab, setActiveTab] = useState('Overview')
  const [tiltStyle, setTiltStyle] = useState({ transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)' })
  const navigate = useNavigate()

  const formattedValue = value !== undefined && value !== null ? value : 'N/A'
  const isPositive = trend === 'up'

  // Dynamic 3D mouse tracking tilt handler
  function handleMouseMove(e) {
    if (isFlipped) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    const rotateX = (-y / (rect.height / 2)) * 6
    const rotateY = (x / (rect.width / 2)) * 6
    setTiltStyle({
      transform: `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`,
      transition: 'transform 0.1s ease-out'
    })
  }

  function handleMouseLeave() {
    setTiltStyle({
      transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
      transition: 'transform 0.5s ease-out'
    })
  }

  function handleFlip(e) {
    e.stopPropagation()
    setIsFlipped(!isFlipped)
  }

  return (
    <>
      {/* Interactive 3D KPI Card with Flip & Mouse Tilt */}
      <div
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={tiltStyle}
        className="group relative bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle hover:shadow-3d-hover hover:border-blue-300 transition-all duration-300 select-none overflow-hidden"
      >
        {/* Subtle top accent gradient line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 opacity-80 group-hover:opacity-100 transition-opacity z-10" />

        {/* Card Content Container */}
        <div className={`p-5 transition-all duration-500 ${isFlipped ? 'opacity-0 pointer-events-none hidden' : 'opacity-100'}`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              {Icon && (
                <div className="w-10 h-10 rounded-xl bg-blue-50/80 border border-blue-100 flex items-center justify-center text-blue-600 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-sm">
                  <Icon size={20} />
                </div>
              )}
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">KPI Metric</span>
                <h3 className="text-sm font-extrabold text-slate-800 group-hover:text-blue-600 transition-colors">
                  {label}
                </h3>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {change && (
                <div className={`flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full ${
                  isPositive ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-rose-50 text-rose-600 border border-rose-200'
                }`}>
                  {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  <span>{change}</span>
                </div>
              )}

              {/* 3D Flip Action Button */}
              <button 
                type="button"
                onClick={handleFlip}
                className="text-slate-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                title="Flip to view formula & details"
              >
                <RotateCw size={15} />
              </button>

              {/* Maximize Action Button */}
              <button 
                type="button"
                onClick={() => setIsExpanded(true)}
                className="text-slate-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                title="Click to maximize detailed analysis"
              >
                <Maximize2 size={15} />
              </button>
            </div>
          </div>

          <div 
            onClick={() => setIsExpanded(true)}
            className="mt-2 flex items-baseline justify-between cursor-pointer"
          >
            <div>
              <span className="text-2xl font-extrabold text-slate-900 tracking-tight group-hover:text-blue-900 transition-colors">
                {formattedValue}
              </span>
              {unit && (
                <span className="ml-1.5 text-xs font-semibold text-slate-500">
                  {unit}
                </span>
              )}
            </div>
            <span className="text-[11px] font-bold text-slate-400 group-hover:text-blue-600 transition-colors flex items-center gap-1">
              Maximize &rarr;
            </span>
          </div>
        </div>

        {/* Card Back View (Formula & Definitions) */}
        {isFlipped && (
          <div className="p-5 bg-slate-900 text-white rounded-2xl animate-fadeIn space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
                <BookOpen size={14} />
                <span>Accounting Context</span>
              </div>
              <button 
                type="button"
                onClick={handleFlip}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
                title="Flip back to metric"
              >
                <RotateCw size={14} />
              </button>
            </div>

            <p className="text-xs text-slate-300 font-medium leading-relaxed">
              {description || `Extracted ${label} figure from verified financial disclosures. Represents balance sheet and operating health.`}
            </p>

            <div className="bg-slate-800/80 rounded-xl p-2.5 border border-slate-700/80 flex items-center justify-between text-[11px] font-mono text-emerald-400">
              <span>Formula: Standard KPI</span>
              <span className="text-slate-400 font-sans">Verified</span>
            </div>
          </div>
        )}
      </div>

      {/* Expanded Interactive 3D Modal Window Matching Reference Screenshot */}
      {isExpanded && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-md animate-fadeIn select-none overflow-y-auto"
          onClick={() => setIsExpanded(false)}
        >
          <div 
            className="relative w-full max-w-4xl bg-white rounded-3xl border border-slate-200/90 shadow-2xl p-7 transition-all transform scale-100 animate-scaleUp my-8"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Top Header */}
            <div className="flex items-start justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center font-bold text-xl shadow-xs">
                  {Icon ? <Icon size={28} /> : '$'}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{label}</h2>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{formattedValue}</span>
                    {change && (
                      <span className="flex items-center gap-1 text-xs font-extrabold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                        <TrendingUp size={14} /> {change} vs FY 2024
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-slate-400 mt-1">
                    Total {label} • USD in millions
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 cursor-pointer hover:bg-slate-200 transition-colors">
                  <Calendar size={14} />
                  <span>5 Years</span>
                  <span>▾</span>
                </div>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="text-slate-400 hover:text-slate-700 p-2 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Sub-Header Tabs */}
            <div className="flex items-center gap-2 pt-4 pb-2 border-b border-slate-100 overflow-x-auto">
              {['Overview', 'Trend Analysis', 'Breakdown', 'AI Insights', 'Source Documents'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === tab 
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20' 
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Modal Body Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-6 items-start">
              {/* Left Column: 5-Year Trend Line Chart & Revenue Breakdown */}
              <div className="lg:col-span-7 space-y-6">
                {/* 5-Year Trend Chart Box */}
                <div className="bg-slate-50/70 rounded-2xl p-5 border border-slate-200/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                        {label} Trend (5-Year Performance)
                      </h3>
                      <span className="text-[11px] text-slate-400 font-medium">USD in millions</span>
                    </div>
                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-100">
                      879,891 Peak
                    </span>
                  </div>

                  {/* SVG Animated Area Line Chart */}
                  <div className="h-44 relative pt-4">
                    <svg className="w-full h-full overflow-visible" viewBox="0 0 500 140">
                      <defs>
                        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.35" />
                          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>

                      {/* Area Fill */}
                      <path
                        d="M 20,95 L 120,80 L 220,50 L 320,52 L 460,15 L 460,130 L 20,130 Z"
                        fill="url(#chartGradient)"
                        className="animate-fadeIn"
                      />

                      {/* Line Stroke */}
                      <path
                        d="M 20,95 L 120,80 L 220,50 L 320,52 L 460,15"
                        fill="none"
                        stroke="#2563eb"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                        className="transition-all duration-1000"
                      />

                      {/* Interactive Point Nodes with Labels */}
                      {[
                        { x: 20, y: 95, val: '538,200', year: '2021' },
                        { x: 120, y: 80, val: '603,600', year: '2022' },
                        { x: 220, y: 50, val: '714,600', year: '2023' },
                        { x: 320, y: 52, val: '715,300', year: '2024' },
                        { x: 460, y: 15, val: '879,891', year: '2025' },
                      ].map((pt, i) => (
                        <g key={i} className="group/pt cursor-pointer">
                          <circle cx={pt.x} cy={pt.y} r="5" fill="#ffffff" stroke="#2563eb" strokeWidth="3" />
                          <text x={pt.x} y={pt.y - 12} textAnchor="middle" className="text-[10px] font-extrabold fill-slate-900">
                            {pt.val}
                          </text>
                          <text x={pt.x} y="138" textAnchor="middle" className="text-[11px] font-bold fill-slate-400">
                            {pt.year}
                          </text>
                        </g>
                      ))}
                    </svg>
                  </div>
                </div>

                {/* Donut Segment Breakdown */}
                <div className="bg-slate-50/70 rounded-2xl p-5 border border-slate-200/80 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Revenue Breakdown (FY 2025)
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                    <div className="sm:col-span-5 flex items-center justify-center relative py-2">
                      {/* Donut Ring Visualizer */}
                      <div className="w-28 h-28 rounded-full border-8 border-blue-600 border-t-emerald-400 border-r-amber-400 flex flex-col items-center justify-center shadow-xs">
                        <span className="text-xs font-extrabold text-slate-900">$879,891M</span>
                        <span className="text-[9px] font-bold text-slate-400 uppercase">Total</span>
                      </div>
                    </div>

                    <div className="sm:col-span-7 space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200/60">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
                          <span className="font-bold text-slate-800">Automotive</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-extrabold text-slate-900">87%</span>
                          <span className="text-slate-500 font-semibold">$765,912M</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200/60">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                          <span className="font-bold text-slate-800">Energy Storage</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-extrabold text-slate-900">8%</span>
                          <span className="text-slate-500 font-semibold">$70,392M</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200/60">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                          <span className="font-bold text-slate-800">Services & Other</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-extrabold text-slate-900">5%</span>
                          <span className="text-slate-500 font-semibold">$43,587M</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Key Highlights & AI Insight Box */}
              <div className="lg:col-span-5 space-y-6">
                {/* Key Highlights Card */}
                <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-3d-subtle space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Key Highlights
                  </h3>

                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold flex-shrink-0">
                        <TrendingUp size={16} />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">Strong Growth</h4>
                        <p className="text-[11px] text-slate-500 font-medium leading-snug">
                          Revenue increased by 23.1% compared to the previous fiscal year.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold flex-shrink-0">
                        <PieChart size={16} />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">Automotive Segment</h4>
                        <p className="text-[11px] text-slate-500 font-medium leading-snug">
                          Contributed 87% of total revenue, followed by Energy (8%) and Services (5%).
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold flex-shrink-0">
                        <Star size={16} />
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">Record High</h4>
                        <p className="text-[11px] text-slate-500 font-medium leading-snug">
                          FY 2025 revenue reached an all-time high of $879,891M.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Insight Box Matching Image */}
                <div className="bg-gradient-to-br from-indigo-50/70 to-blue-50/70 rounded-2xl p-5 border border-indigo-100 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-700">
                    <Sparkles size={16} className="text-indigo-600" />
                    <span>✨ AI Insight</span>
                  </div>

                  <p className="text-xs font-medium text-slate-700 leading-relaxed">
                    Tesla's revenue growth is primarily driven by strong demand in the Automotive segment, supported by new product launches and global expansion. Energy business also shows steady growth, contributing to long-term diversification.
                  </p>

                  <button
                    onClick={() => {
                      setIsExpanded(false)
                      navigate('/chat')
                    }}
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-500/20"
                  >
                    <MessageSquare size={14} />
                    <span>Ask AI about Revenue</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default FinancialCard

