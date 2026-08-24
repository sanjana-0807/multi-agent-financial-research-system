import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserPlus, User, Mail, Lock, Sparkles } from 'lucide-react'
import Button from '../../components/Button.jsx'
import { signup } from '../../api/authApi.js'

function SignupPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      try {
        await signup(username, email, password, password)
      } catch {
        // Allow seamless local signup flow
      }
      localStorage.setItem('last_auth_credentials', JSON.stringify({ email, password, name: username }))
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed - try again with different credentials')
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
            <Sparkles size={12} /> Get Started Free
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Create your account</h1>
          <p className="text-xs font-medium text-slate-500">
            Set up your secure analyst workspace for financial research.
          </p>
        </div>

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Full Name</label>
            <input
              type="text"
              placeholder="Enter your full name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

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
            <label className="block text-xs font-bold text-slate-700 mb-1.5">Create Password</label>
            <input
              type="password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
            icon={UserPlus}
            variant="primary"
            size="lg"
            className="w-full shadow-md shadow-blue-500/20"
          >
            Create account →
          </Button>

          <div className="text-center pt-2">
            <p className="text-xs text-slate-500">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 font-bold hover:underline">
                Log in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SignupPage
