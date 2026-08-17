import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { LogIn, Mail, Lock, Cpu, Sparkles, ShieldCheck, Eye, EyeOff, CheckCircle2 } from 'lucide-react'
import Input from '../../components/Input.jsx'
import Button from '../../components/Button.jsx'
import { login } from '../../api/authApi.js'
import { useAuth } from './useAuth.js'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [demoFilled, setDemoFilled] = useState(false)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()

  function handleFillDemo() {
    setEmail('admin@gmail.com')
    setPassword('admin123')
    setError(null)
    setDemoFilled(true)
    setTimeout(() => setDemoFilled(false), 2000)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const res = await login(email, password)
      const token = res.data?.access_token || res.data?.token
      if (!token) {
        throw new Error('No token returned from server')
      }
      loginWithToken(token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed - check your credentials')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6 select-none animate-fadeIn">
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle shadow-3d-hover transition-all duration-300 p-8 w-full max-w-md space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center mx-auto shadow-md shadow-blue-500/20">
            <Cpu size={24} className="animate-pulse" />
          </div>
          <div className="flex items-center justify-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-600">
            <Sparkles size={12} /> Multi-Agent AI System
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Log in to Platform</h1>
          <p className="text-xs font-medium text-slate-500">
            Access financial research, RAG search, and automated reports.
          </p>
        </div>

        {/* Demo Auto-Fill Banner */}
        <div className="bg-blue-50/60 rounded-xl p-3 border border-blue-100 flex items-center justify-between">
          <div className="text-xs font-semibold text-blue-900 flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-blue-600" />
            <span>Need quick access?</span>
          </div>
          <button
            type="button"
            onClick={handleFillDemo}
            className="flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-2xs"
          >
            {demoFilled ? <CheckCircle2 size={12} /> : null}
            <span>{demoFilled ? 'Demo Filled!' : 'Auto-fill Demo'}</span>
          </button>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="admin@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={Mail}
            required
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={Lock}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-slate-400 hover:text-slate-600 p-1 rounded-md"
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
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
            className="w-full"
          >
            Log in
          </Button>
        </form>

        {/* Footer Navigation Link */}
        <p className="text-xs font-semibold text-slate-500 text-center pt-2 border-t border-slate-100">
          Don't have an account?{' '}
          <Link to="/signup" className="text-blue-600 font-bold hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage


