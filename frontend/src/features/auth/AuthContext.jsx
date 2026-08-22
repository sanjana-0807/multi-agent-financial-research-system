import { createContext, useState, useEffect } from 'react'

export const AuthContext = createContext(null)

const DEFAULT_USER = {
  name: 'User',
  email: '',
  initial: 'U',
  role: 'Senior Financial Analyst'
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('authToken'))
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user_profile')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem('user_profile', JSON.stringify(user))
    }
  }, [user])

  const loginWithToken = (jwt, customUser = null) => {
    localStorage.setItem('authToken', jwt)
    setToken(jwt)
    if (customUser) {
      const initial = (customUser.name || customUser.email || 'U').charAt(0).toUpperCase()
      const updatedUser = {
        name: customUser.name || 'User',
        email: customUser.email || '',
        initial: initial,
        role: customUser.role || 'Senior Financial Analyst'
      }
      setUser(updatedUser)
      localStorage.setItem('user_profile', JSON.stringify(updatedUser))
    }
  }

  const updateUser = (updatedFields) => {
    setUser((prev) => {
      const updated = {
        ...(prev || DEFAULT_USER),
        ...updatedFields,
        initial: (updatedFields.name || (prev && prev.name) || 'U').charAt(0).toUpperCase()
      }
      localStorage.setItem('user_profile', JSON.stringify(updated))
      return updated
    })
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('user_profile')
    localStorage.removeItem('last_auth_credentials')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        user: user || DEFAULT_USER,
        updateUser,
        loginWithToken,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
