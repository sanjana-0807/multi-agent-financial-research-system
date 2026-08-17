import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './features/auth/AuthContext.jsx'
import { WorkspaceProvider } from './context/WorkspaceContext.jsx'
import AppRouter from './router/AppRouter.jsx'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <WorkspaceProvider>
          <AppRouter />
        </WorkspaceProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
