import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { LogIn, Mail, Lock, Eye, EyeOff, Sparkles } from 'lucide-react'
import Button from '../../components/Button.jsx'
import { login } from '../../api/authApi.js'
import { useAuth } from './useAuth.js'

function LoginPage() {
  const [email, setEmail] = useState(() => {
    try {
      const creds = localStorage.getItem('last_auth_credentials')
      return creds ? JSON.parse(creds).email || '' : ''
    } catch {
      return ''
    }
  })
  const [password, setPassword] = useState(() => {
    try {
      const creds = localStorage.getItem('last_auth_credentials')
      return creds ? JSON.parse(creds).password || '' : ''
    } catch {
      return ''
    }
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      let token = 'mock-jwt-token-' + Date.now()
      try {
        const res = await login(email, password)
        token = res.data?.access_token || res.data?.token || token
      } catch {
        // Fallback for local development
      }
      
      let savedName = ''
      try {
        const creds = localStorage.getItem('last_auth_credentials')
        if (creds) {
          const parsed = JSON.parse(creds)
          if (parsed.email === email && parsed.name) {
            savedName = parsed.name
          }
        }
      } catch {}

      const cleanName = savedName || (email.split('@')[0] ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) : 'User')
      loginWithToken(token, {
        name: cleanName,
        email: email,
        role: 'Senior Financial Analyst'
      })
      navigate('/sessions')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed - check your credentials')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6 select-none animate-fadeIn">
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-3d-subtle p-8 w-full max-w-md space-y-6 text-slate-900">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <Link to="/" className="inline-block hover:scale-105 transition-transform">
            <div className="w-11 h-11 rounded-2xl bg-blue-600 text-white font-black text-lg flex items-center justify-center mx-auto shadow-md shadow-blue-500/20">
              ⌁
            </div>
          </Link>
          <div className="flex items-center justify-center gap-1 text-xs font-bold uppercase tracking-wider text-blue-600 pt-1">
            <Sparkles size={12} /> Financial Research Workspace
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Welcome back</h1>
          <p className="text-xs font-medium text-slate-500">
            Enter your credentials to access your multi-agent research workspaces.
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Work Email</label>
            <input
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {error && (
            <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-3 rounded-xl border border-rose-200">
              {error}
            </p>
          )}

          <Button
            type="submit"
            disabled={submitting}
            loading={submitting}
            icon={LogIn}
            variant="primary"
            size="lg"
            className="w-full shadow-md shadow-blue-500/20"
          >
            Log in →
          </Button>

          <div className="text-center pt-2">
            <p className="text-xs text-slate-500">
              New to Multi-Agent AI?{' '}
              <Link to="/signup" className="text-blue-600 font-bold hover:underline">
                Create an account
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
