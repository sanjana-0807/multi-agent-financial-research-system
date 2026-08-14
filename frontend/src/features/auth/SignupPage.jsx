import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserPlus, User, Mail, Lock, Cpu, Sparkles } from 'lucide-react'
import Input from '../../components/Input.jsx'
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
      await signup(username, email, password, password)
      navigate('/login')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        setError(detail[0].msg)
      } else {
        setError('Signup failed - try again with different credentials')
      }
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
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Create an Account</h1>
          <p className="text-xs font-medium text-slate-500">
            Join the platform to perform automated financial research & risk analysis.
          </p>
        </div>

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full Name / Username"
            type="text"
            placeholder="John Doe"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            icon={User}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="analyst@firm.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={Mail}
            required
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={Lock}
            required
          />

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
            className="w-full"
          >
            Create Account
          </Button>
        </form>

        {/* Footer Navigation Link */}
        <p className="text-xs font-semibold text-slate-500 text-center pt-2 border-t border-slate-100">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 font-bold hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default SignupPage

