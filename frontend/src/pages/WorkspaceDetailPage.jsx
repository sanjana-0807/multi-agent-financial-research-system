import { useState, useEffect, useRef } from 'react'
import { Building2, Sparkles, Cpu, Clock, Upload, FileText, ArrowRight, ShieldCheck, TrendingUp, BarChart2, Database, GitCompare, MessageSquare, CheckCircle2 } from 'lucide-react'
import MetricsPanel from '../features/extraction/MetricsPanel.jsx'
import RatiosTable from '../features/extraction/RatiosTable.jsx'
import Card from '../components/Card.jsx'
import Button from '../components/Button.jsx'
import Badge from '../components/Badge.jsx'
import { getExtraction } from '../api/extractionApi.js'
import { dashboardData as mockData } from '../data/mockDashboardData.js'
import { useNavigate } from 'react-router-dom'

const PLACEHOLDER_DOCUMENT_ID = 'D100'

function WorkspaceDetailPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(0)
  const [animateBars, setAnimateBars] = useState(false)
  const chartRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    getExtraction(PLACEHOLDER_DOCUMENT_ID)
      .then((res) => {
        setData(res.data)
        setLoading(false)
      })
      .catch(() => {
        setData(mockData)
        setError('Connected via offline fallback mode')
        setLoading(false)
      })
  }, [])

  // Trigger scroll-activated line animation when chart enters viewport
  useEffect(() => {
    if (loading) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setAnimateBars(true)
        }
      },
      { threshold: 0.2 }
    )

    if (chartRef.current) {
      observer.observe(chartRef.current)
    }

    return () => observer.disconnect()
  }, [loading])

  if (loading) {
    return (
      <div className="p-8 text-center space-y-4 animate-fadeIn">
        <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center mx-auto animate-bounce">
          <Cpu size={24} />
        </div>
        <p className="text-sm font-semibold text-slate-500">Processing multi-agent financial extraction...</p>
      </div>
    )
  }

  const AGENT_PIPELINE = [
    { name: 'Document Agent', role: 'PDF Parsing & Chunking', status: 'Completed', icon: Database, color: 'bg-emerald-500 text-emerald-600 border-emerald-200' },
    { name: 'Extraction Agent', role: 'KPI Metrics & Financials', status: 'Completed', icon: BarChart2, color: 'bg-emerald-500 text-emerald-600 border-emerald-200' },
    { name: 'Red Flag Agent', role: 'Risk & Anomaly Detection', status: 'Scanning', icon: ShieldCheck, color: 'bg-amber-500 text-amber-600 border-amber-200' },
    { name: 'Research Agent', role: 'Vector RAG Search & Q&A', status: 'Active', icon: MessageSquare, color: 'bg-blue-500 text-blue-600 border-blue-200' },
    { name: 'Report Agent', role: 'PDF Synthesis & Export', status: 'Standby', icon: FileText, color: 'bg-slate-400 text-slate-600 border-slate-200' },
  ]

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* Top Context Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-blue-500/20">
            {data.company ? data.company.charAt(0) : 'T'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1">
                <Sparkles size={12} /> Active Research Session
              </span>
              <Badge variant="success">Verified 10-K</Badge>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-0.5">
              {data.company} — Financial Dashboard
            </h1>
            <p className="text-xs font-semibold text-slate-400 mt-0.5 flex items-center gap-2">
              <span>Fiscal Year {data.fiscal_year}</span>
              <span>•</span>
              <span className="flex items-center gap-1"><Clock size={12} /> Updated 2 mins ago</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <Button onClick={() => navigate('/upload')} icon={Upload} variant="outline" size="sm">
            Upload Filing
          </Button>
          <Button onClick={() => navigate('/report')} icon={FileText} variant="primary" size="sm">
            Executive Report
          </Button>
        </div>
      </div>

      {/* Multi-Agent AI Workflow Pipeline Node Canvas */}
      <Card title="Multi-Agent AI Pipeline Engine" subtitle="Interactive processing canvas across 5 specialized agents">
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
          {AGENT_PIPELINE.map((agent, idx) => {
            const Icon = agent.icon
            const isSelected = selectedAgent === idx
            return (
              <div
                key={idx}
                onClick={() => setSelectedAgent(idx)}
                className={`group cursor-pointer relative p-4 rounded-2xl border transition-all duration-300 ${
                  isSelected 
                    ? 'bg-blue-50/50 border-blue-300 ring-2 ring-blue-500/20 shadow-md' 
                    : 'bg-slate-50/80 border-slate-200/80 hover:border-slate-300 hover:bg-white'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 flex items-center justify-center font-bold text-slate-700 shadow-2xs group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    <Icon size={16} />
                  </div>

                  <div className="relative flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full ${agent.color.split(' ')[0]}`} />
                    <span className={`absolute -inset-0.5 rounded-full ${agent.color.split(' ')[0]} animate-ping opacity-75`} />
                  </div>
                </div>

                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Agent 0{idx + 1}</div>
                <div className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors mt-0.5">
                  {agent.name}
                </div>
                <div className="text-[11px] font-medium text-slate-500 truncate mt-0.5">{agent.role}</div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* 3D KPI Metrics Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BarChart2 size={18} className="text-blue-600" /> Extracted Financial Metrics
          </h2>
          <span className="text-xs font-semibold text-slate-400">Click flip icon for formula • Click card to maximize</span>
        </div>
        <MetricsPanel data={data} />
      </div>

      {/* Ratios Matrix Section */}
      <RatiosTable ratios={data.ratios} />

      {/* Visual Analytics Charts Section */}
      <div ref={chartRef} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Revenue Growth Trajectory" subtitle="Historical and projected annual revenue ($ Millions)">
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
              <span>FY 2023: $650M</span>
              <span>FY 2024: $714M</span>
              <span className="text-blue-600 font-bold">FY 2025: $879.9M</span>
            </div>
            {/* Animated Curved SVG Area Line Chart Matching Screenshot */}
            <div className="h-36 bg-slate-50/80 rounded-2xl border border-slate-100 p-3 relative flex items-center justify-center overflow-hidden">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 500 120">
                <defs>
                  <linearGradient id="dashboardRevenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={animateBars ? 0.35 : 0} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* Animated Gradient Area Fill */}
                <path
                  d="M 30,85 Q 230,60 470,18 L 470,110 L 30,110 Z"
                  fill="url(#dashboardRevenueGradient)"
                  className="transition-opacity duration-1000"
                />

                {/* Live Path Drawing Animated Stroke Line */}
                <path
                  d="M 30,85 Q 230,60 470,18"
                  fill="none"
                  stroke="#2563eb"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  style={{
                    strokeDasharray: 600,
                    strokeDashoffset: animateBars ? 0 : 600,
                    transition: 'stroke-dashoffset 1.2s ease-out'
                  }}
                />

                {/* Point Node 1: FY 2023 ($650M) */}
                <g className="group/pt cursor-pointer">
                  <circle cx="30" cy="85" r="5" fill="#ffffff" stroke="#2563eb" strokeWidth="3" />
                  <text x="30" y="72" textAnchor="middle" className="text-[10px] font-extrabold fill-slate-800">
                    $650M
                  </text>
                  <text x="30" y="115" textAnchor="middle" className="text-[10px] font-bold fill-slate-400">
                    FY 2023
                  </text>
                </g>

                {/* Point Node 2: FY 2024 ($714M) */}
                <g className="group/pt cursor-pointer">
                  <circle cx="230" cy="55" r="5" fill="#ffffff" stroke="#2563eb" strokeWidth="3" />
                  <text x="230" y="42" textAnchor="middle" className="text-[10px] font-extrabold fill-slate-800">
                    $714M
                  </text>
                  <text x="230" y="115" textAnchor="middle" className="text-[10px] font-bold fill-slate-400">
                    FY 2024
                  </text>
                </g>

                {/* Point Node 3: FY 2025 ($879.9M Peak) */}
                <g className="group/pt cursor-pointer">
                  <circle cx="470" cy="18" r="6" fill="#2563eb" stroke="#ffffff" strokeWidth="2.5" />
                  <text x="470" y="10" textAnchor="end" className="text-[11px] font-extrabold fill-blue-600">
                    $879.9M (Peak)
                  </text>
                  <text x="470" y="115" textAnchor="middle" className="text-[10px] font-bold fill-slate-400">
                    FY 2025
                  </text>
                </g>
              </svg>
            </div>
          </div>
        </Card>

        <Card title="Profitability Margin Analysis" subtitle="Net profit margin comparison vs industry standard">
          <div className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-700 font-bold">{data.company} Net Margin</span>
                <span className="text-emerald-600 font-bold">18.9% (Optimal)</span>
              </div>
              <div className="h-3.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60 p-0.5">
                <div 
                  style={{ width: animateBars ? '85%' : '0%' }}
                  className="h-full bg-emerald-500 rounded-full transition-all duration-1000 ease-out shadow-xs" 
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-600">Automotive Sector Benchmark</span>
                <span className="text-slate-500 font-bold">12.3%</span>
              </div>
              <div className="h-3.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60 p-0.5">
                <div 
                  style={{ width: animateBars ? '55%' : '0%' }}
                  className="h-full bg-slate-400 rounded-full transition-all duration-1000 ease-out delay-200" 
                />
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default WorkspaceDetailPage




