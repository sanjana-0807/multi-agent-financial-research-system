import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sparkles, Upload, FileText, ShieldCheck, Inbox, Plus, Layers,
  TrendingUp, TrendingDown, AlertTriangle, Maximize2, X, Scale, CheckSquare, Building2, Check,
  GitCompare, Trophy, Cpu, CheckCircle2, ArrowRight
} from 'lucide-react'
import Button from '../components/Button.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { formatCurrency } from '../utils/formatCurrency.js'
import { getLatestDocumentForCompany } from '../api/documentsApi.js'
import { runComparison } from '../api/comparisonApi.js'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function WorkspaceDetailPage() {
  const {
    activeWorkspace, companies, activeCompany, activeDocument,
    extractionData, redFlagData, selectCompany, refreshCompanies
  } = useWorkspace()
  const [activeTab, setActiveTab] = useState('overview')
  const [comparisonState, setComparisonState] = useState({
  companyAId: '', companyBId: '', result: null, compareError: null
})
  const navigate = useNavigate()

  const hasData = Boolean(extractionData && extractionData.revenue)
  const currentDoc = activeDocument?.filename || 'No document uploaded yet'

  const TABS = [
    { id: 'overview', label: 'Overview', icon: '◈', title: 'Research overview', desc: 'Source-grounded analysis from your uploaded documents.' },
    { id: 'document', label: 'Document Agent', icon: '▣', title: 'Document Agent', desc: 'Manage and verify the source documents indexed in this workspace.' },
    { id: 'extraction', label: 'Extraction Agent', icon: '⌁', title: 'Extraction Agent', desc: 'Key financial metrics and trends identified from your documents.' },
    { id: 'flags', label: 'Red Flag Agent', icon: '⚑', title: 'Red Flag Agent', desc: 'Potential risks, auditor qualifications, and anomalies requiring attention.' },
    { id: 'comparison', label: 'Comparison Agent', icon: '⇄', title: 'Comparison Agent', desc: 'Benchmark financial performance across company documents.' },
    { id: 'report', label: 'Report Agent', icon: '▤', title: 'Report Agent', desc: 'Compile your analysis into an analyst-style research report.' }
  ]
  const currentTabInfo = TABS.find(t => t.id === activeTab) || TABS[0]
  // Maps a red flag's raw category to a human-readable group heading.
// Anything not listed falls into "Other Findings" automatically.
const FLAG_CATEGORY_GROUPS = {
  rising_debt: 'Financial Risk',
  falling_margins: 'Financial Risk',
  auditor_remarks: 'Auditor Remarks',
}
  // No workspace open at all — the only case that blocks the whole page.
  if (!activeWorkspace) {
    return (
      <div className="p-6 md:p-12 max-w-4xl mx-auto space-y-6 animate-fadeIn select-none">
        <div className="bg-white rounded-3xl p-12 border border-slate-200 text-center space-y-5 shadow-3d-subtle">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
            <Inbox size={32} />
          </div>
          <div>
            <h2 className="text-2xl font-extrabold text-slate-900">No Active Research Session</h2>
            <p className="text-sm text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
              Open or create a session to begin uploading and analyzing financial disclosures.
            </p>
          </div>
          <div className="pt-2 flex justify-center gap-3">
            <Button onClick={() => navigate('/sessions')} icon={Plus} variant="primary" size="lg">
              Manage Sessions
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const rev = extractionData?.revenue ? formatCurrency(extractionData.revenue) : '—'
  const netInc = extractionData?.net_profit ? formatCurrency(extractionData.net_profit) : '—'
  const totalAssets = extractionData?.assets ? formatCurrency(extractionData.assets) : '—'
  const totalLiab = extractionData?.liabilities ? formatCurrency(extractionData.liabilities) : '—'
  const cashFlow = extractionData?.cash_flow ? formatCurrency(extractionData.cash_flow) : '—'
  const epsVal = (extractionData?.eps !== undefined && extractionData?.eps !== null) ? `$${extractionData.eps}` : '—'
  const opMargin = extractionData?.ratios?.net_profit_margin != null ? `${extractionData.ratios.net_profit_margin}%` : '—'
  const debtEq = extractionData?.ratios?.debt_to_equity != null ? `${extractionData.ratios.debt_to_equity}×` : '—'
  const currentRatio = extractionData?.ratios?.current_ratio != null ? `${extractionData.ratios.current_ratio}` : '—'

  const flags = redFlagData?.flags || []
  const overallRisk = redFlagData?.overall_risk || 'LOW'

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6 animate-fadeIn select-none relative pb-24">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">{currentTabInfo.title}</h1>
          <p className="text-xs font-medium text-slate-500 mt-1">{currentTabInfo.desc}</p>
        </div>
        <Button onClick={() => navigate('/upload')} icon={Plus} variant="outline" size="sm">
          Add Document
        </Button>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-200/80">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === t.id ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>{t.icon}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
  !hasData ? (
    <EmptyTabState
      title={activeCompany ? `No processed document for ${activeCompany.name}` : 'No company selected'}
      desc="Upload a filing for this company, or pick a different company from the Document tab to view its overview."
      onUpload={() => navigate('/upload')}
    />
  ) : (
    <OverviewTab
      extractionData={extractionData}
      overallRisk={overallRisk}
      flags={flags}
      currentDoc={currentDoc}
      rev={rev} netInc={netInc} totalAssets={totalAssets} totalLiab={totalLiab} cashFlow={cashFlow} epsVal={epsVal}
      opMargin={opMargin} currentRatio={currentRatio} debtEq={debtEq}
      companies={companies}
      activeCompany={activeCompany}
      onSelectCompany={(c) => selectCompany(c)}
      onGoToFlags={() => setActiveTab('flags')}
      onGoToDocument={() => setActiveTab('document')}
      onGoToComparison={() => setActiveTab('comparison')}
      onUpload={() => navigate('/upload')}
    />
  )
)}

      {activeTab === 'document' && (
        <DocumentTab
          companies={companies}
          activeCompany={activeCompany}
          onSelectCompany={(c) => { selectCompany(c); setActiveTab('overview') }}
          onAddDocument={() => navigate('/upload')}
        />
      )}

      {activeTab === 'extraction' && (
  !hasData ? (
    <EmptyTabState
      title="No extraction results yet"
      desc="Upload and process a document for this company to see extracted metrics."
      onUpload={() => navigate('/upload')}
    />
  ) : (
  <div className="space-y-6">
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-900">Extracted Financial Metrics</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          {extractionData?.company || '—'} · FY {extractionData?.fiscal_year || '—'}
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
  {[
    ['Total Revenue', rev], ['Net Profit', netInc], ['Total Assets', totalAssets],
    ['Total Liabilities', totalLiab], ['Operating Cash Flow', cashFlow], ['Diluted EPS', epsVal],
  ].map(([label, val]) => (
    <div key={label} className="bg-slate-50 rounded-xl p-3.5 border border-slate-100 space-y-1">
      <span className="text-[11px] font-semibold text-slate-400">{label}</span>
      <div className="text-lg font-extrabold text-slate-900">{val === '—' ? val : (label === 'Diluted EPS' ? val : `$${val}`)}</div>
    </div>
  ))}
</div>
    </div>

    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
  <h3 className="text-base font-bold text-slate-900">Financial Ratios</h3>
  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
    {[
      ['Net Profit Margin', opMargin], ['Current Ratio', currentRatio], ['Debt-to-Equity', debtEq],
    ].map(([label, val]) => (
      <div key={label} className="bg-slate-50 rounded-xl p-3.5 border border-slate-100 space-y-1">
        <span className="text-[11px] font-semibold text-slate-400">{label}</span>
        <div className="text-lg font-extrabold text-slate-900">{val}</div>
        {val === '—' && (
          <p className="text-[10px] text-slate-400 leading-snug pt-0.5">
            Not available — this filing didn't include the breakdown needed to compute it.
          </p>
        )}
      </div>
    ))}
  </div>
</div>
  </div>
  )
)}

      {activeTab === 'flags' && (
  !hasData ? (
    <EmptyTabState
      title="No red flag results yet"
      desc="Upload and process a document for this company to see risk findings."
      onUpload={() => navigate('/upload')}
    />
  ) : (
  <div className="space-y-6">
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
            overallRisk === 'HIGH' ? 'bg-rose-100 text-rose-700' : overallRisk === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
          }`}>
            Overall Risk: {overallRisk}
          </span>
          <h3 className="text-xl font-extrabold text-slate-900 mt-2">Red Flag Agent Findings</h3>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          ['HIGH', 'bg-rose-50 border-rose-200 text-rose-700'],
          ['MEDIUM', 'bg-amber-50 border-amber-200 text-amber-800'],
          ['LOW', 'bg-slate-50 border-slate-200 text-slate-600'],
        ].map(([sev, cls]) => {
          const count = flags.filter((f) => f.severity === sev).length
          return (
            <div key={sev} className={`rounded-xl border p-3 text-center ${cls}`}>
              <div className="text-lg font-extrabold">{count}</div>
              <div className="text-[10px] font-bold uppercase tracking-wide">{sev}</div>
            </div>
          )
        })}
      </div>
    </div>

    {flags.length === 0 ? (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-10 text-center shadow-3d-subtle">
        <p className="text-xs text-slate-400">No red flags identified.</p>
      </div>
    ) : (
      Object.entries(
        flags.reduce((groups, flag) => {
          const groupName = FLAG_CATEGORY_GROUPS[flag.category] || 'Other Findings'
          if (!groups[groupName]) groups[groupName] = []
          groups[groupName].push(flag)
          return groups
        }, {})
      ).map(([groupName, groupFlags]) => {
        const GroupIcon = groupName === 'Financial Risk' ? TrendingDown : groupName === 'Auditor Remarks' ? Scale : AlertTriangle
        return (
          <div key={groupName} className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
                <GroupIcon size={14} />
              </div>
              <h4 className="text-sm font-bold text-slate-900">{groupName}</h4>
              <span className="text-[10px] font-semibold text-slate-400">({groupFlags.length})</span>
            </div>
            <div className="space-y-3">
              {groupFlags.map((flag, idx) => (
                <div key={idx} className={`p-4 rounded-xl border space-y-1.5 ${
                  flag.severity === 'HIGH' ? 'bg-rose-50/60 border-rose-200' : flag.severity === 'MEDIUM' ? 'bg-amber-50/60 border-amber-200/70' : 'bg-slate-50 border-slate-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">{flag.category}</span>
                      <h4 className="text-xs font-bold text-slate-900">{flag.title}</h4>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                      flag.severity === 'HIGH' ? 'bg-rose-500 text-white' : flag.severity === 'MEDIUM' ? 'bg-amber-500 text-white' : 'bg-slate-400 text-white'
                    }`}>
                      {flag.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{flag.explanation}</p>
                  {flag.evidence && (
                    <div className="text-[11px] font-semibold text-slate-700 bg-white px-2.5 py-1 rounded-md border border-slate-200/60 inline-block mt-1">
                      🔍 Evidence: <span className="font-mono text-blue-700">{flag.evidence}</span>
                      {flag.page_number ? ` (p.${flag.page_number})` : ''}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })
    )}
  </div>
  )
)}
      {activeTab === 'comparison' && (
  <ComparisonTab
    workspace={activeWorkspace}
    companies={companies}
    onAddDocument={() => navigate('/upload')}
    comparisonState={comparisonState}
    setComparisonState={setComparisonState}
  />
)}

      {activeTab === 'report' && (
        <div className="bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 text-white rounded-3xl p-8 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <h3 className="text-lg font-bold">Analyst Research Report</h3>
            <p className="text-xs text-blue-100 max-w-lg leading-relaxed">Report generation is not available yet.</p>
          </div>
        </div>
      )}
    </div>
  )
}

function EmptyTabState({ title, desc, onUpload }) {
  return (
    <div className="bg-white rounded-3xl border border-slate-200 p-10 text-center space-y-4 shadow-3d-subtle">
      <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
        <Inbox size={28} />
      </div>
      <div>
        <h3 className="text-base font-bold text-slate-900">{title}</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1.5 leading-relaxed">{desc}</p>
      </div>
      <Button onClick={onUpload} icon={Upload} variant="primary" size="md">
        Upload Financial Document
      </Button>
    </div>
  )
}

// Document Agent tab — lists every company in the workspace with its
// document status, lets the user click into any of them to view its
// overview, and offers a button to add a new document/company.
function DocumentTab({ companies, activeCompany, onSelectCompany, onAddDocument }) {
  const [statusByCompany, setStatusByCompany] = useState({})
  const [loadingStatus, setLoadingStatus] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function loadStatuses() {
      setLoadingStatus(true)
      const results = {}
      for (const c of companies) {
        try {
          const res = await getLatestDocumentForCompany(c.id)
          results[c.id] = res.data
        } catch {
          results[c.id] = null
        }
      }
      if (!cancelled) {
        setStatusByCompany(results)
        setLoadingStatus(false)
      }
    }
    if (companies.length > 0) loadStatuses()
    else setLoadingStatus(false)
    return () => { cancelled = true }
  }, [companies])

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-5">
      <div>
  <h3 className="text-base font-bold text-slate-900">Workspace Documents</h3>
  <p className="text-xs text-slate-500 mt-0.5">Every company and document indexed in this session.</p>
</div>

      {companies.length === 0 ? (
        <div className="text-center py-10 space-y-2">
          <Building2 size={28} className="mx-auto text-slate-300" />
          <p className="text-xs text-slate-400">No companies in this session yet.</p>
        </div>
      ) : loadingStatus ? (
        <div className="text-center py-10 text-xs text-slate-400">Loading document status...</div>
      ) : (
        <div className="space-y-2">
          {companies.map((c) => {
            const doc = statusByCompany[c.id]
            const isSelected = activeCompany?.id === c.id
            return (
              <button
                key={c.id}
                type="button"
                onClick={() => onSelectCompany(c)}
                className={`w-full flex items-center justify-between p-4 rounded-xl border text-left transition-colors ${
                  isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-blue-100 text-blue-700 font-extrabold text-xs flex items-center justify-center">
                    {doc ? 'PDF' : <FileText size={16} />}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900">{c.name} <span className="text-slate-400 font-semibold">({c.ticker})</span></div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{doc?.filename || 'No document uploaded'}</div>
                  </div>
                </div>
                {doc ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                    <Check size={11} /> {doc.status}
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold text-slate-400">No document</span>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
// Overview tab — a genuine synthesis, not a duplicate of Extraction/Red
// Flag. Shows: (1) an auto-generated one-line verdict, (2) the metrics
// grid for quick reference, (3) only the single most severe red flag
// with a link to the full list, (4) a workspace-wide company status
// row, and (5) suggested next steps based on gaps in the current data.
function OverviewTab({
  extractionData, overallRisk, flags, currentDoc,
  rev, netInc, totalAssets, totalLiab, cashFlow, epsVal, opMargin, currentRatio, debtEq,
  companies, activeCompany, onSelectCompany, onGoToFlags, onGoToDocument, onGoToComparison, onUpload
}) {
  const [statusByCompany, setStatusByCompany] = useState({})

  useEffect(() => {
    let cancelled = false
    async function loadStatuses() {
      const results = {}
      for (const c of companies) {
        try {
          const res = await getLatestDocumentForCompany(c.id)
          results[c.id] = res.data
        } catch {
          results[c.id] = null
        }
      }
      if (!cancelled) setStatusByCompany(results)
    }
    if (companies.length > 0) loadStatuses()
    return () => { cancelled = true }
  }, [companies])

  // 1. Executive summary — one sentence combining risk + standout ratios.
  const company = extractionData?.company || 'This company'
  const margin = extractionData?.ratios?.net_profit_margin
  const debtToEquity = extractionData?.ratios?.debt_to_equity
  const concerns = []
  if (margin != null && margin < 10) concerns.push('thin profit margins')
  if (debtToEquity != null && debtToEquity > 1) concerns.push('elevated leverage')
  const strengths = []
  if (extractionData?.revenue) strengths.push('strong revenue')
  if (extractionData?.assets) strengths.push('a solid asset base')
  let summary = `${company} shows ${overallRisk} overall risk`
  if (concerns.length > 0) summary += `, driven by ${concerns.join(' and ')}`
  if (strengths.length > 0) summary += `, offset by ${strengths.join(' and ')}`
  summary += '.'

  // 2. Top risk only — highest severity flag, rest stay in Red Flag tab.
  const severityRank = { HIGH: 0, MEDIUM: 1, LOW: 2 }
  const topFlag = [...flags].sort((a, b) => (severityRank[a.severity] ?? 3) - (severityRank[b.severity] ?? 3))[0]

  // 3. Next steps — gaps in the current data, each with a jump-to-tab link.
  const nextSteps = []
  if (currentRatio === '—') {
    nextSteps.push({
      text: 'Current Ratio is unavailable — upload a filing with full balance sheet detail to compute it.',
      action: onGoToDocument, actionLabel: 'Go to Document Agent'
    })
  }
  if (companies.length < 2) {
    nextSteps.push({
      text: 'Add a peer company to unlock the Comparison Agent.',
      action: onGoToComparison, actionLabel: 'Go to Comparison Agent'
    })
  }
  const missingDocCount = companies.filter((c) => statusByCompany[c.id] === null).length
  if (missingDocCount > 0) {
    nextSteps.push({
      text: `${missingDocCount} compan${missingDocCount === 1 ? 'y has' : 'ies have'} no document uploaded yet.`,
      action: onGoToDocument, actionLabel: 'Go to Document Agent'
    })
  }
  if (topFlag?.severity === 'HIGH') {
    nextSteps.push({
      text: 'A HIGH severity red flag needs review before this session is finalized.',
      action: onGoToFlags, actionLabel: 'Go to Red Flag Agent'
    })
  }

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <div className={`rounded-2xl p-5 border flex items-start gap-3 ${
        overallRisk === 'HIGH' ? 'bg-rose-50 border-rose-200' : overallRisk === 'MEDIUM' ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'
      }`}>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
          overallRisk === 'HIGH' ? 'bg-rose-500 text-white' : overallRisk === 'MEDIUM' ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white'
        }`}>
          <Sparkles size={16} />
        </div>
        <div>
          <span className="text-[10px] font-extrabold uppercase tracking-wide text-slate-500">Executive Summary</span>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">{summary}</p>
        </div>
      </div>

      {/* Workspace-Wide Company Snapshot */}
      {companies.length > 1 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-3d-subtle">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900">Companies in This Session</h3>
            <button onClick={onGoToDocument} className="text-[11px] font-bold text-blue-600 hover:underline">Manage →</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {companies.map((c) => {
              const doc = statusByCompany[c.id]
              const isActive = activeCompany?.id === c.id
              return (
                <button
                  key={c.id}
                  onClick={() => onSelectCompany(c)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-bold border transition-colors ${
                    isActive ? 'bg-blue-50 border-blue-300 text-blue-700' : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${doc ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  {c.ticker} {doc ? '· Ready' : '· No document'}
                </button>
              )
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-5">
          <div>
            <h3 className="text-base font-bold text-slate-900">Extracted Key Financials</h3>
            <p className="text-xs text-slate-500 mt-0.5">Extracted from {currentDoc}</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              ['Total Revenue', rev], ['Net Profit', netInc], ['Total Assets', totalAssets],
              ['Total Liabilities', totalLiab], ['Operating Cash Flow', cashFlow], ['Diluted EPS', epsVal],
            ].map(([label, val]) => (
              <div key={label} className="bg-slate-50 border border-slate-100 rounded-xl p-3.5 space-y-1">
                <span className="text-[11px] font-semibold text-slate-400">{label}</span>
                <div className="text-lg font-extrabold text-slate-900 tracking-tight">{val}</div>
              </div>
            ))}
          </div>
          <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 font-extrabold text-xs flex items-center justify-center">PDF</div>
              <div>
                <div className="text-xs font-bold text-slate-800">{currentDoc}</div>
                <div className="text-[10px] text-slate-400 font-medium">Indexed · Verified Extraction · ChromaDB</div>
              </div>
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">Ready</span>
          </div>
        </div>

        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Financial Ratios & Health</h3>
            <p className="text-xs text-slate-500 mt-0.5">Composite signal from extracted metrics</p>
          </div>
          <div className="space-y-2 text-xs font-semibold text-slate-700 pt-2">
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
              <span>Net Profit Margin</span><span className="font-bold text-slate-900">{opMargin}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
              <span>Current Ratio</span><span className="font-bold text-slate-900">{currentRatio}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg">
              <span>Debt-to-Equity</span><span className="font-bold text-slate-900">{debtEq}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Top Risk Only */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Top Priority Signal</h3>
            <p className="text-xs text-slate-500 mt-0.5">Highest-severity finding · {flags.length} total</p>
          </div>
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
            overallRisk === 'HIGH' ? 'bg-rose-100 text-rose-700 border border-rose-200'
            : overallRisk === 'MEDIUM' ? 'bg-amber-100 text-amber-800 border border-amber-200'
            : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
          }`}>
            Overall Risk: {overallRisk}
          </span>
        </div>
        {topFlag ? (
          <div className={`flex items-start gap-3 p-3.5 rounded-xl border ${
            topFlag.severity === 'HIGH' ? 'bg-rose-50/60 border-rose-200' : topFlag.severity === 'MEDIUM' ? 'bg-amber-50/60 border-amber-200/70' : 'bg-slate-50 border-slate-200'
          }`}>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase mt-0.5 ${
              topFlag.severity === 'HIGH' ? 'bg-rose-500 text-white' : topFlag.severity === 'MEDIUM' ? 'bg-amber-500 text-white' : 'bg-slate-400 text-white'
            }`}>
              {topFlag.severity}
            </span>
            <div>
              <h4 className="text-xs font-bold text-slate-900">{topFlag.title}</h4>
              <p className="text-xs text-slate-600 mt-0.5">{topFlag.explanation}</p>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 text-center py-4">No red flags identified for this document.</p>
        )}
        <button onClick={onGoToFlags} className="flex items-center gap-1 text-xs font-bold text-blue-600 hover:underline">
          View all {flags.length} findings <ArrowRight size={12} />
        </button>
      </div>

      {/* Next Steps */}
      {nextSteps.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-3">
          <h3 className="text-base font-bold text-slate-900">Suggested Next Steps</h3>
          <div className="space-y-2">
            {nextSteps.map((step, idx) => (
              <div key={idx} className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <p className="text-xs text-slate-700">{step.text}</p>
                <button onClick={step.action} className="flex items-center gap-1 text-[11px] font-bold text-blue-600 hover:underline whitespace-nowrap">
                  {step.actionLabel} <ArrowRight size={11} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
// Small circular progress ring used by Industry Rankings — deliberately
// a different visual shape from the horizontal bar charts below it, so
// the two sections don't read as repetitive.
function ScoreRing({ percent, color, size = 72, strokeWidth = 7 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.max(0, Math.min(100, percent)) / 100) * circumference
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90 flex-shrink-0">
      <circle cx={size / 2} cy={size / 2} r={radius} stroke="#e2e8f0" strokeWidth={strokeWidth} fill="none" />
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        stroke={color} strokeWidth={strokeWidth} fill="none"
        strokeDasharray={circumference} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.8s ease' }}
      />
    </svg>
  )
}
// Comparison Agent tab — dropdown company pickers (instead of a card
// grid, to save vertical space) plus a lightweight bar-chart visual
// for the ratio comparison, alongside the exact-value table.
// Comparison Agent tab — dropdown company pickers (instead of a card
// grid, to save vertical space) plus recharts bar charts for the
// ratio comparison, alongside the exact-value table.
function ComparisonTab({ workspace, companies, onAddDocument, comparisonState, setComparisonState }) {
  const { companyAId, companyBId, result, compareError } = comparisonState
  const [comparing, setComparing] = useState(false)

  const canCompare = companyAId && companyBId && companyAId !== companyBId

  function handleChangeA(id) {
    setComparisonState((prev) => ({ ...prev, companyAId: id, result: null, compareError: null }))
  }

  function handleChangeB(id) {
    setComparisonState((prev) => ({ ...prev, companyBId: id, result: null, compareError: null }))
  }

  async function handleRunComparison() {
    if (!workspace || !canCompare) return
    setComparing(true)
    setComparisonState((prev) => ({ ...prev, compareError: null }))
    try {
      const res = await runComparison(workspace.id, [companyAId, companyBId])
      setComparisonState((prev) => ({ ...prev, result: res.data }))
    } catch (err) {
      setComparisonState((prev) => ({
        ...prev,
        compareError: err.response?.data?.detail || 'Comparison failed — make sure both companies have a processed document.'
      }))
    } finally {
      setComparing(false)
    }
  }

  if (companies.length < 2) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-10 text-center space-y-4 shadow-3d-subtle">
      <GitCompare size={28} className="mx-auto text-slate-300" />
      <div>
        <h3 className="text-base font-bold text-slate-900">Add a second company to compare</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1.5">
          This workspace currently has only {companies.length} compan{companies.length === 1 ? 'y' : 'ies'}. Use the "Add Document" button above to add another company before running a comparison.
        </p>
      </div>
    </div>
  )
}

  let tickers = []
  let financialRows = []
  let ratioMetricRows = []
  const colors = ['#2563eb', '#10b981']

  if (result) {
  tickers = Object.keys(result.ratio_comparisons[0]?.values || {})
  // Split by magnitude so currency-scale metrics (revenue, assets...) go to
  // the bar chart, and ratio-scale metrics (EPS, debt-to-equity...) go to
  // KPI cards instead — they're different units and shouldn't share an axis.
  const isRatioScale = (row) => Math.max(...tickers.map((t) => Math.abs(Number(row.values[t]) || 0))) < 100
  const financialMetricRows = result.ratio_comparisons.filter((row) => !isRatioScale(row))
  ratioMetricRows = result.ratio_comparisons.filter((row) => isRatioScale(row))
  financialRows = financialMetricRows.map((row) => {
    const entry = { name: row.ratio_name }
    tickers.forEach((t) => { entry[t] = Number(row.values[t]) })
    return entry
  })
}

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
        <div>
  <h3 className="text-base font-bold text-slate-900">Select Two Companies</h3>
  <p className="text-xs text-slate-500 mt-0.5">Choose two companies from this workspace to benchmark.</p>
</div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Company A</label>
            <select
              value={companyAId}
              onChange={(e) => handleChangeA(e.target.value)}
              className="w-full mt-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-800"
            >
              <option value="">Select a company…</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id} disabled={c.id === companyBId}>
                  {c.name} ({c.ticker})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Company B</label>
            <select
              value={companyBId}
              onChange={(e) => handleChangeB(e.target.value)}
              className="w-full mt-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-800"
            >
              <option value="">Select a company…</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id} disabled={c.id === companyAId}>
                  {c.name} ({c.ticker})
                </option>
              ))}
            </select>
          </div>
        </div>

        <Button
          onClick={handleRunComparison}
          disabled={!canCompare || comparing}
          loading={comparing}
          icon={Cpu}
          variant="primary"
          size="md"
          className="w-full"
        >
          Compare Selected Companies
        </Button>
        {compareError && (
          <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-3 rounded-xl border border-rose-200">{compareError}</p>
        )}
      </div>

      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                <Trophy size={18} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Industry Rankings</h3>
                <p className="text-xs text-slate-500">{result.summary}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
  {result.industry_rankings.map((r) => {
    const maxScore = Math.max(...result.industry_rankings.map((x) => x.score))
    const pct = maxScore > 0 ? (r.score / maxScore) * 100 : 0
    const ringColor = r.rank === 1 ? '#f59e0b' : '#94a3b8'
    return (
      <div key={r.ticker} className={`p-4 rounded-xl border flex items-center gap-4 ${
        r.rank === 1 ? 'bg-amber-50/60 border-amber-300' : 'bg-white border-slate-200/80'
      }`}>
        <div className="relative flex-shrink-0">
          <ScoreRing percent={pct} color={ringColor} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-black text-slate-800">{r.score}</span>
          </div>
        </div>
        <div>
          <div className={`inline-flex w-7 h-7 rounded-lg items-center justify-center font-black text-xs mb-1 ${
            r.rank === 1 ? 'bg-amber-500 text-white' : 'bg-slate-300 text-slate-700'
          }`}>
            #{r.rank}
          </div>
          <h4 className="text-xs font-extrabold text-slate-900">{r.ticker}</h4>
          <span className="text-[10px] font-semibold text-slate-400">Score: {r.score}</span>
        </div>
      </div>
    )
  })}
</div>
          </div>

          {financialRows.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
              <h3 className="text-base font-bold text-slate-900">Financial Metrics Comparison</h3>
              <ResponsiveContainer width="100%" height={Math.max(220, financialRows.length * 70)}>
                <BarChart data={financialRows} layout="vertical" margin={{ top: 8, right: 32, left: 8, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} tickFormatter={(v) => v.toLocaleString()} />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fontWeight: 600, fill: '#334155' }} />
                  <Tooltip formatter={(v) => v.toLocaleString()} contentStyle={{ fontSize: 12, borderRadius: 10, border: '1px solid #e2e8f0' }} />
                  <Legend wrapperStyle={{ fontSize: 11, fontWeight: 600 }} />
                  {tickers.map((t, i) => (
                    <Bar key={t} dataKey={t} name={t} fill={colors[i % colors.length]} radius={[0, 6, 6, 0]} barSize={16} animationDuration={800} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {ratioMetricRows.length > 0 && (
  <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
    <h3 className="text-base font-bold text-slate-900">Ratio Metrics Comparison</h3>
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {ratioMetricRows.map((row) => {
        const [tickerA, tickerB] = tickers
        const valA = Number(row.values[tickerA])
        const valB = Number(row.values[tickerB])
        const best = row.best_performer
        const smaller = Math.min(Math.abs(valA), Math.abs(valB))
        const larger = Math.max(Math.abs(valA), Math.abs(valB))
        const deltaPct = smaller > 0 ? ((larger - smaller) / smaller * 100).toFixed(1) : null

        return (
          <div key={row.ratio_name} className="rounded-xl border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700">{row.ratio_name}</span>
              <span className="text-[10px] font-bold text-emerald-600 uppercase">Best: {best}</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
  {tickers.map((t) => {
    const isBest = t === best
    const rawVal = row.values[t]
    const numVal = Number(rawVal)
    const displayVal = !isNaN(numVal) ? numVal.toFixed(2) : rawVal
    return (
      <div
        key={t}
        title={String(rawVal)}
        className={`rounded-lg p-3 text-center border ${
          isBest ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-100'
        }`}
      >
        <div className="text-[10px] font-bold text-slate-500">{t}</div>
        <div className={`text-base font-extrabold mt-0.5 truncate ${isBest ? 'text-emerald-700' : 'text-slate-700'}`}>
          {displayVal}
        </div>
      </div>
    )
  })}
</div>
            {deltaPct && (
              <div className="flex items-center justify-center gap-1.5 text-[11px] font-bold text-emerald-600">
                <TrendingUp size={12} />
                <span>{best} leads by {deltaPct}%</span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  </div>
)}

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">
            <h3 className="text-base font-bold text-slate-900 mb-4">Ratio Comparison — Table</h3>
            <table className="w-full text-xs text-left">
              <thead className="text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-2 pr-4">Metric</th>
                  {tickers.map((ticker) => (
                    <th key={ticker} className="py-2 pr-4">{ticker}</th>
                  ))}
                  <th className="py-2">Best</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.ratio_comparisons.map((row) => (
                  <tr key={row.ratio_name}>
                    <td className="py-2 pr-4 font-semibold text-slate-800">{row.ratio_name}</td>
                    {Object.entries(row.values).map(([ticker, val]) => (
                      <td key={ticker} className="py-2 pr-4">{val}</td>
                    ))}
                    <td className="py-2 font-bold text-emerald-600">{row.best_performer}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end">
            <Button
  onClick={() => setComparisonState({ companyAId: '', companyBId: '', result: null, compareError: null })}
  variant="outline"
  size="sm"
>
  Run Again
</Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default WorkspaceDetailPage