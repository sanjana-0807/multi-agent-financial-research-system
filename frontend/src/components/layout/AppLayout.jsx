import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Navbar from './Navbar.jsx'

// Every route rendered inside <AppLayout> automatically gets the sidebar.
// Login is intentionally kept OUTSIDE this layout (see AppRouter.jsx) since
// an unauthenticated user shouldn't see app navigation before logging in.
function AppLayout() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <div className="flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
export default AppLayout
