import ReportPreview from '../features/report/ReportPreview.jsx'
import ReportExportButton from '../features/report/ReportExportButton.jsx'

const MOCK_REPORT = {
  title: 'Tesla Inc. — Financial Analysis Report FY 2025',
  generated_at: 'August 5, 2026',
  summary: 'Tesla Inc. demonstrated strong revenue growth in FY 2025, with total revenue reaching $879.9M. Net profit margins remain healthy at 18.9%, though the company\'s debt-to-equity ratio of 0.38 suggests conservative leverage. EPS of $8.47 reflects solid shareholder value creation.',
  sections: [
    { heading: 'Revenue Analysis', content: 'Total revenue of $879,891K represents a 23% year-over-year increase. The automotive segment contributed 87% of total revenue, with energy generation and storage accounting for the remaining 13%.' },
    { heading: 'Profitability', content: 'Net profit of $74,982K yields a net profit margin of 18.9%, exceeding the industry average of 12.3%. Operating expenses were well-controlled, with SG&A costs declining as a percentage of revenue.' },
    { heading: 'Balance Sheet', content: 'Total assets of $247.5B provide a strong foundation. Current ratio of 1.8 indicates healthy short-term liquidity. The conservative debt-to-equity ratio of 0.38 leaves room for strategic leverage if needed.' },
  ]
}

function ReportPage() {
  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Report</h1>
        <p className="text-gray-500">Generated financial research report.</p>
      </div>
      <ReportPreview report={MOCK_REPORT} />
      <ReportExportButton reportId="R001" />
    </div>
  )
}
export default ReportPage
