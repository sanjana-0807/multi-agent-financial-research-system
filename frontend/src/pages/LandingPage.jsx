import { Link } from 'react-router-dom'
import { BarChart3, Shield, GitCompare, FileText, ArrowRight } from 'lucide-react'

const features = [
  { icon: BarChart3, title: 'Financial Extraction', desc: 'Automatically extract key metrics from annual reports and 10-K filings.' },
  { icon: Shield, title: 'Red Flag Detection', desc: 'AI-powered identification of financial risks and accounting anomalies.' },
  { icon: GitCompare, title: 'Company Comparison', desc: 'Compare financial performance across multiple companies side by side.' },
  { icon: FileText, title: 'Report Generation', desc: 'Generate comprehensive research reports with a single click.' },
]

function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Multi-Agent Financial Research
          </h1>
          <p className="text-lg text-gray-500 mb-8 max-w-2xl mx-auto">
            Upload financial documents and let AI agents extract metrics, detect risks,
            compare companies, and generate reports — all automatically.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              to="/signup"
              className="flex items-center gap-2 bg-blue-600 text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Get Started <ArrowRight size={16} />
            </Link>
            <Link
              to="/login"
              className="bg-gray-100 text-gray-700 rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              Log in
            </Link>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-xl font-semibold text-gray-900 text-center mb-10">
          Powered by Specialized AI Agents
        </h2>
        <div className="grid grid-cols-2 gap-5">
          {features.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center mb-3">
                <Icon size={20} className="text-blue-600" />
              </div>
              <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 py-6 text-center">
        <p className="text-xs text-gray-400">
          © 2026 Multi-Agent Financial Research System — Infosys Springboard Internship
        </p>
      </div>
    </div>
  )
}

export default LandingPage
