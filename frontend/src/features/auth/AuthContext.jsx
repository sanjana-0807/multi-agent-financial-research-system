import { createContext, useState } from 'react'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('authToken'))

  const loginWithToken = (jwt) => {
    localStorage.setItem('authToken', jwt)
    setToken(jwt)
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, loginWithToken, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
