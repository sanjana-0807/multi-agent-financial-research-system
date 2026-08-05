import { Routes, Route } from 'react-router-dom'
import AppLayout from '../components/layout/AppLayout.jsx'
import ProtectedRoute from '../components/layout/ProtectedRoute.jsx'
import WorkspaceDetailPage from '../pages/WorkspaceDetailPage.jsx'
import LandingPage from '../pages/LandingPage.jsx'
import LoginPage from '../features/auth/LoginPage.jsx'
import SignupPage from '../features/auth/SignupPage.jsx'
import WorkspaceList from '../features/workspace/WorkspaceList.jsx'
import DocumentUpload from '../features/documents/DocumentUpload.jsx'
import DocumentList from '../features/documents/DocumentList.jsx'
import MetricsPage from '../pages/MetricsPage.jsx'
import RatiosPage from '../pages/RatiosPage.jsx'
import ResearchPromptForm from '../features/research/ResearchPromptForm.jsx'
import ComparisonPage from '../pages/ComparisonPage.jsx'
import RedFlagsPage from '../pages/RedFlagsPage.jsx'
import ReportPage from '../pages/ReportPage.jsx'
import SettingsPage from '../pages/SettingsPage.jsx'
import NotFoundPage from '../pages/NotFoundPage.jsx'

function AppRouter() {
  return (
    <Routes>
      {/* Landing page — no sidebar */}
      <Route path="/" element={<LandingPage />} />

      {/* All app routes — sidebar + navbar */}
      <Route element={<AppLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/dashboard" element={<WorkspaceDetailPage />} />
        <Route path="/upload" element={<DocumentUpload />} />
        <Route path="/sessions" element={<WorkspaceList />} />
        <Route path="/upload-history" element={<DocumentList />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/ratios" element={<RatiosPage />} />
        <Route path="/chat" element={<ResearchPromptForm />} />
        <Route path="/red-flags" element={<RedFlagsPage />} />
        <Route path="/comparison" element={<ComparisonPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
export default AppRouter
