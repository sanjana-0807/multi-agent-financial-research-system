import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../features/auth/useAuth.js'

// wraps routes that require login - if there's no token, bounce to /login
// instead of showing the page
function ProtectedRoute() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export default ProtectedRoute
