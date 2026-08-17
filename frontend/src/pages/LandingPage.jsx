import { Link, useNavigate } from 'react-router-dom'
import { BarChart3, ShieldCheck, GitCompare, FileText, ArrowRight, Cpu, Sparkles, Database, CheckCircle2, Zap, TrendingUp, DollarSign, Landmark } from 'lucide-react'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'

const features = [
  { icon: BarChart3, title: 'Automated Financial Extraction', desc: 'Extraction Agent parses balance sheets, income statements, and cash flows from 10-K disclosures.' },
  { icon: ShieldCheck, title: 'Red Flag & Risk Scanner', desc: 'Red Flag Agent scans accounting anomalies, leverage spikes, and revenue discrepancies.' },
  { icon: GitCompare, title: 'Company Comparison Matrix', desc: 'Comparison Agent evaluates side-by-side competitor performance and margin benchmarks.' },
  { icon: FileText, title: 'Executive Report Synthesis', desc: 'Report Agent synthesizes multi-agent research findings into downloadable PDF reports.' },
]

const AI_AGENTS = [
  { step: '01', name: 'Document Agent', role: 'Parses 10-K/10-Q PDFs', icon: Database },
  { step: '02', name: 'Extraction Agent', role: 'KPI Metrics & Financials', icon: BarChart3 },
  { step: '03', name: 'Red Flag Agent', role: 'Anomaly & Risk Detection', icon: ShieldCheck },
  { step: '04', name: 'Research Agent', role: 'Vector RAG Search & Q&A', icon: Cpu },
  { step: '05', name: 'Report Agent', role: 'PDF Synthesis & Export', icon: FileText },
]

function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans select-none">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
              <Cpu size={22} className="animate-pulse" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1">
                <Sparkles size={10} /> Team 2
              </span>
              <h1 className="font-extrabold text-slate-900 text-sm tracking-tight leading-tight">
                Multi-Agent AI Financial Research
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={() => navigate('/login')} variant="outline" size="sm">
              Log in
            </Button>
            <Button onClick={() => navigate('/signup')} variant="primary" size="sm" icon={ArrowRight}>
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-white border-b border-slate-200/80 py-16 md:py-20 relative overflow-hidden">
        {/* Subtle top glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-blue-500/10 blur-3xl rounded-full pointer-events-none" />

        <div className="max-w-5xl mx-auto px-6 text-center space-y-6 relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200/80 shadow-2xs">
            <Sparkles size={14} className="text-blue-600 animate-pulse" />
            <span>Multi-Agent AI Platform for Business Insights</span>
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight max-w-4xl mx-auto">
            Development of Multi-Agent AI Analysis System for Financial Research and Business Insights
          </h1>

          <p className="text-base md:text-lg font-medium text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Automate corporate report analysis with specialized AI agents working together to extract metrics, calculate financial ratios, scan red flags, and synthesize executive research reports.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Button onClick={() => navigate('/signup')} variant="primary" size="lg" icon={ArrowRight}>
              Get Started Free
            </Button>
            <Button onClick={() => navigate('/dashboard')} variant="outline" size="lg">
              Explore Demo Dashboard
            </Button>
          </div>

          {/* 3D Interactive Hero Preview Mockup Card */}
          <div className="pt-8 max-w-4xl mx-auto perspective-1000">
            <div className="bg-slate-900 text-white rounded-2xl p-6 border border-slate-800 shadow-2xl transition-all duration-700 hover:rotate-0 transform rotateX-3 shadow-blue-500/10 text-left space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-400">
                  <Sparkles size={14} /> Live Agent Workspace Preview
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Verified 10-K Ingestion
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700/80 space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Total Revenue</div>
                  <div className="text-xl font-extrabold text-white">$879.9M</div>
                  <div className="text-[10px] font-bold text-emerald-400">+23.4% YoY</div>
                </div>
                <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700/80 space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Net Profit Margin</div>
                  <div className="text-xl font-extrabold text-white">18.9%</div>
                  <div className="text-[10px] font-bold text-emerald-400">Above Benchmark</div>
                </div>
                <div className="bg-slate-800/80 rounded-xl p-3 border border-slate-700/80 space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Risk Scan</div>
                  <div className="text-xl font-extrabold text-emerald-400">Compliant</div>
                  <div className="text-[10px] font-bold text-slate-400">0 High-Risk Alerts</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Multi-Agent Architecture Pipeline Section */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-600 flex items-center justify-center gap-1">
            <Zap size={14} /> Autonomous Workflow
          </span>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            5 Specialized AI Agents Working in Harmony
          </h2>
          <p className="text-sm font-medium text-slate-500">
            Each agent executes targeted tasks to transform raw PDF filings into actionable business intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {AI_AGENTS.map(({ step, name, role, icon: Icon }) => (
            <div 
              key={step} 
              className="group bg-white rounded-2xl p-4 border border-slate-200/80 shadow-3d-subtle shadow-3d-hover hover:border-blue-300 transition-all text-center space-y-2 cursor-pointer"
            >
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center mx-auto font-bold shadow-2xs group-hover:bg-blue-600 group-hover:text-white transition-colors">
                <Icon size={20} />
              </div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Step {step}</div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{name}</h3>
              <p className="text-[11px] font-medium text-slate-500 leading-snug">{role}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Capabilities Grid */}
      <section className="bg-white border-t border-b border-slate-200/80 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Enterprise Financial Analytics Capabilities
            </h2>
            <p className="text-sm font-medium text-slate-500">
              Built for financial analysts, investment researchers, and decision makers.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map(({ icon: Icon, title, desc }) => (
              <Card key={title} hover3D={true} padding="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 border border-blue-100 flex items-center justify-center flex-shrink-0 font-bold shadow-xs">
                    <Icon size={24} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 mb-1 tracking-tight">{title}</h3>
                    <p className="text-xs font-medium text-slate-600 leading-relaxed">{desc}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-white text-center border-t border-slate-200/80">
        <div className="max-w-4xl mx-auto px-6 space-y-2">
          <p className="text-xs font-semibold text-slate-500">
            Development of Multi-Agent AI Analysis System for Financial Research and Business Insights
          </p>
          <p className="text-[11px] text-slate-400 font-medium">
            © 2026 Team 2 • Financial Research Platform
          </p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage


