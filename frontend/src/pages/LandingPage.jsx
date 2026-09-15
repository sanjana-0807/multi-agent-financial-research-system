import { useNavigate } from 'react-router-dom'
import {
  ArrowRight, Sparkles, Database, BarChart3, ShieldCheck, Cpu, FileText, CheckCircle2,
  Upload, ScanSearch, GitCompareArrows, ClipboardList, AlertTriangle, Clock, FileWarning,
  Layers
} from 'lucide-react'
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
      <main className="max-w-7xl mx-auto px-6 py-16 lg:py-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center w-full">
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 text-xs font-extrabold border border-blue-200/80 shadow-2xs">
            <Sparkles size={13} className="text-blue-600" />
            <span>Multi-Agent Financial Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-tight">
            From filings to <span className="text-blue-600">clear conviction.</span>
          </h1>

          <p className="text-base sm:text-lg font-medium text-slate-600 max-w-xl leading-relaxed">
            Read every filing like an analyst who has time to.
Multi-Agent AI extracts the numbers, flags the risks, and benchmarks against peers — so you get an analyst's read on a 10-K without spending the afternoon in it.
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

          <div className="flex items-center gap-2.5 pt-6 text-xs text-slate-500 font-semibold border-t border-slate-200 max-w-md">
            <FileText size={14} className="text-slate-400 shrink-0" />
            <span>Works with 10-Ks, 10-Qs, and annual reports—every figure traced back to its page.</span>
          </div>
        </div>

        {/* Hero Preview Card — annotated filing excerpt */}
        <div className="lg:col-span-5">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-3d-subtle space-y-5 hover:-translate-y-1 hover:shadow-lg transition-all duration-300 relative overflow-hidden">
            {/* subtle top accent */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-cyan-400 to-blue-600" />

            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileText size={14} className="text-slate-400" />
                <span className="text-xs font-bold text-slate-800">Tesla, Inc. · 10-K, Item 7A</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
                p. 46
              </span>
            </div>

            <p className="text-[13px] leading-relaxed text-slate-700">
              The Company ended the period with cash and cash equivalents of{' '}
              <span className="bg-blue-50 border-b-2 border-blue-400 px-0.5 rounded-t-sm font-semibold text-blue-800">
                $16.4 billion
              </span>
              , while{' '}
              <span className="bg-amber-50 border-b-2 border-amber-400 px-0.5 rounded-t-sm font-semibold text-amber-800">
                accounts payable grew faster than revenue for the third straight quarter
              </span>
              . Operating margin held{' '}
              <span className="bg-cyan-50 border-b-2 border-cyan-400 px-0.5 rounded-t-sm font-semibold text-cyan-800">
                roughly in line with the peer average
              </span>
              .
            </p>

            <div className="space-y-2.5 pt-1 border-t border-slate-100">
              <div className="flex items-start gap-2.5 pt-3">
                <div className="w-6 h-6 rounded-md bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 mt-0.5">
                  <BarChart3 size={13} />
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">
                  <span className="font-bold text-slate-700">Extraction Agent</span> pulled the cash position straight from the balance sheet.
                </p>
              </div>
              <div className="flex items-start gap-2.5">
                <div className="w-6 h-6 rounded-md bg-amber-100 text-amber-600 flex items-center justify-center shrink-0 mt-0.5">
                  <ShieldCheck size={13} />
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">
                  <span className="font-bold text-slate-700">Red Flag Agent</span> caught payables outgrowing revenue before it became a trend.
                </p>
              </div>
              <div className="flex items-start gap-2.5">
                <div className="w-6 h-6 rounded-md bg-cyan-100 text-cyan-600 flex items-center justify-center shrink-0 mt-0.5">
                  <GitCompareArrows size={13} />
                </div>
                <p className="text-[11px] text-slate-500 leading-snug">
                  <span className="font-bold text-slate-700">Comparison Agent</span> benchmarked the margin against sector peers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ============================================================ */}
      {/* PROBLEM SECTION */}
      {/* ============================================================ */}
      <section className="border-t border-slate-200 bg-white py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-50 text-rose-700 text-xs font-extrabold border border-rose-200/80">
              <AlertTriangle size={13} />
              <span>The problem with manual research</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Annual reports are long. Your time isn't.
            </h2>
            <p className="text-sm sm:text-base font-medium text-slate-500">
              A 10-K can run 200+ pages. Reading five of them to compare competitors, by hand, before every decision, doesn't scale.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center">
                <Clock size={20} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Hours per filing</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Manually scanning a single annual report for the numbers that matter can eat an entire afternoon—before you've even started comparing it to anything.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
                <FileWarning size={20} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Easy to miss red flags</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Thin margins, rising debt, inconsistent cash flow—warning signs buried in footnotes are easy to skim past under time pressure.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center">
                <GitCompareArrows size={20} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Comparisons take forever</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Benchmarking one company against its peers means repeating the same extraction work again and again, then reconciling it all by hand.
              </p>
            </div>
          </div>
        </div>
      </section>


      {/* ============================================================ */}
      {/* AGENT SHOWCASE SECTION */}
      {/* ============================================================ */}
      <section className="border-t border-slate-200 bg-white py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto space-y-3 mb-12">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-50 text-purple-700 text-xs font-extrabold border border-purple-200/80">
              <Layers size={13} />
              <span>Six specialists, one workspace</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              A research team.
            </h2>
            <p className="text-sm sm:text-base font-medium text-slate-500">
              Each agent has one job and does it well—so every output stays traceable back to the source document.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center">
                <Database size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Document Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Parses and indexes filings—including scanned pages via OCR—so every claim can be traced to a page.</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-cyan-100 text-cyan-600 flex items-center justify-center">
                <BarChart3 size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Extraction Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Surfaces key metrics and financial ratios directly from the document, ready for analysis.</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-rose-100 text-rose-600 flex items-center justify-center">
                <ShieldCheck size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Red Flag Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Applies rule-based checks to catch early warning signs before they become expensive surprises.</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center">
                <GitCompareArrows size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Comparison Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Benchmarks a company against its peers, side by side, using consistent, extracted data.</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center">
                <Sparkles size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Research Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Answers your open-ended questions about the filing, grounded strictly in the uploaded source.</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center">
                <FileText size={17} />
              </div>
              <h3 className="text-sm font-bold text-slate-900">Report Agent</h3>
              <p className="text-xs text-slate-500 leading-relaxed">Compiles findings from every agent into one structured, exportable analyst report.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* SAMPLE OUTPUT PREVIEW SECTION */}
      {/* ============================================================ */}
      <section className="border-t border-slate-200 bg-slate-50 py-16">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 space-y-5">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-extrabold border border-emerald-200/80">
              <CheckCircle2 size={13} />
              <span>What you walk away with</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight leading-tight">
              A finished analysis, not a wall of chunks.
            </h2>
            <p className="text-sm sm:text-base font-medium text-slate-500 leading-relaxed">
              Every session ends with the same thing: extracted financials, flagged risks, peer comparisons, and a written summary—all cited back to the exact filing they came from.
            </p>
            <ul className="space-y-2.5 text-sm font-medium text-slate-700">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
                Key metrics extracted automatically
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
                Risk signals with severity ratings
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
                Side-by-side peer benchmarking
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
                Exportable, source-cited report
              </li>
            </ul>
          </div>

          <div className="lg:col-span-7">
            <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-3d-subtle space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-xs font-bold text-slate-800">Tesla, Inc. — Risk Summary</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200">HIGH RISK</span>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-500 font-semibold block">Net Profit Margin</span>
                  <span className="text-base font-extrabold text-slate-900 mt-0.5 block">4.1%</span>
                </div>
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-500 font-semibold block">Debt-to-Equity</span>
                  <span className="text-base font-extrabold text-slate-900 mt-0.5 block">0.66x</span>
                </div>
                <div className="p-3.5 bg-amber-50/60 rounded-xl border border-amber-200/80">
                  <span className="text-[10px] text-amber-700 font-semibold block">Red Flags</span>
                  <span className="text-base font-extrabold text-amber-700 mt-0.5 block">3 found</span>
                </div>
              </div>

              <div className="space-y-2 pt-1">
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-rose-50/60 border border-rose-100">
                  <AlertTriangle size={14} className="text-rose-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="text-xs font-bold text-slate-800 block">Thin profit margins</span>
                    <span className="text-[11px] text-slate-500">Net margin trails sector average despite strong revenue growth.</span>
                  </div>
                </div>
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-50/60 border border-amber-100">
                  <AlertTriangle size={14} className="text-amber-500 mt-0.5 shrink-0" />
                  <div>
                    <span className="text-xs font-bold text-slate-800 block">Rising operating costs</span>
                    <span className="text-[11px] text-slate-500">Cost growth is outpacing revenue growth over the trailing period.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* FINAL CTA SECTION */}
      {/* ============================================================ */}
      <section className="border-t border-slate-200 bg-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            Stop reading filings alone.
          </h2>
          <p className="text-sm sm:text-base font-medium text-slate-500 max-w-xl mx-auto">
            Create a workspace, upload your first disclosure, and see what the agents find in minutes.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button onClick={() => navigate('/signup')} variant="primary" size="lg" icon={ArrowRight}>
              Start researching free →
            </Button>
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="px-5 py-3 rounded-xl border border-slate-300 hover:border-slate-400 text-sm font-bold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 transition-all shadow-xs cursor-pointer"
            >
              Log in
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-slate-50 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 font-medium">
          <span>© {new Date().getFullYear()} Multi-Agent AI. All rights reserved.</span>
          <span>Built for analysts who read the filing, not just the headline.</span>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage