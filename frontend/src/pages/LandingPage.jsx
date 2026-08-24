import { useNavigate } from 'react-router-dom'
import { ArrowRight, Sparkles, Database, BarChart3, ShieldCheck, Cpu, FileText, CheckCircle2 } from 'lucide-react'
import Button from '../components/Button.jsx'

function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans select-none flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white font-black text-lg flex items-center justify-center shadow-md shadow-blue-500/20">
              ⌁
            </div>
            <span className="font-extrabold text-slate-900 text-lg tracking-tight">Multi-Agent AI</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-xs font-bold text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              Log in
            </button>
            <Button onClick={() => navigate('/signup')} variant="primary" size="sm" icon={ArrowRight}>
              Create Account
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-16 lg:py-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 text-xs font-extrabold border border-blue-200/80 shadow-2xs">
            <Sparkles size={13} className="text-blue-600" />
            <span>Multi-Agent Financial Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-tight">
            From filings to <span className="text-blue-600">clear conviction.</span>
          </h1>

          <p className="text-base sm:text-lg font-medium text-slate-600 max-w-xl leading-relaxed">
            Multi-Agent AI brings your disclosures, financial signals, and AI research agents into one focused workspace—so your next decision is strictly grounded in the source.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button onClick={() => navigate('/signup')} variant="primary" size="lg" icon={ArrowRight}>
              Start researching free →
            </Button>
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="px-5 py-3 rounded-xl border border-slate-300 hover:border-slate-400 text-sm font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 transition-all shadow-xs cursor-pointer"
            >
              Explore workspace
            </button>
          </div>

          {/* Mini Proof Badges */}
          <div className="flex items-center gap-8 pt-6 text-xs text-slate-500 font-semibold border-t border-slate-200">
            <div>
              <div className="text-2xl font-extrabold text-slate-900">6</div>
              <div>Specialist agents</div>
            </div>
            <div>
              <div className="text-2xl font-extrabold text-slate-900">100%</div>
              <div>Source-grounded</div>
            </div>
            <div>
              <div className="text-2xl font-extrabold text-slate-900">1 place</div>
              <div>For every session</div>
            </div>
          </div>
        </div>

        {/* Hero Preview Card */}
        <div className="lg:col-span-5">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-3d-subtle space-y-4 transform rotate-1 hover:rotate-0 transition-transform duration-300">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-xs font-bold text-slate-800">FY25 Research Overview</span>
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-300" />
                <span className="w-2 h-2 rounded-full bg-slate-300" />
                <span className="w-2 h-2 rounded-full bg-slate-300" />
              </div>
            </div>

            {/* Preview Chart Bars */}
            <div className="h-36 flex items-end gap-2 pt-4 px-3 bg-slate-50 rounded-2xl border border-slate-100">
              <div className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg h-[43%]" />
              <div className="flex-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t-lg h-[55%]" />
              <div className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg h-[48%]" />
              <div className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg h-[76%]" />
              <div className="flex-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t-lg h-[69%]" />
              <div className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg h-[89%]" />
              <div className="flex-1 bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg h-[84%]" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[10px] text-slate-500 font-semibold block">Revenue Growth</span>
                <span className="text-base font-extrabold text-slate-900 mt-0.5 block">14.6%</span>
              </div>
              <div className="p-3.5 bg-amber-50/60 rounded-xl border border-amber-200/80">
                <span className="text-[10px] text-amber-700 font-semibold block">Risk Signals</span>
                <span className="text-base font-extrabold text-amber-700 mt-0.5 block">3 identified</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 5-Agent Strip */}
      <div className="border-t border-slate-200 bg-white py-6">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-slate-900">Document Agent</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Parse & index filings</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-slate-900">Extraction Agent</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Surface key metrics</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-slate-900">Red Flag Agent</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Find anomalies early</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-xs font-bold text-slate-900">Comparison Agent</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Benchmark peers</div>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 col-span-2 sm:col-span-1">
            <div className="text-xs font-bold text-slate-900">Report Agent</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Shape the narrative</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
