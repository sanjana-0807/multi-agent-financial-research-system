import axiosClient from './axiosClient.js'

// Matches backend/routes/auth.py
// POST /signup - accepts email + password
// POST /login - checks credentials, returns a JWT token
export function signup(email, password) {
  return axiosClient.post('/signup', { email, password })
}

export function login(email, password) {
  return axiosClient.post('/login', { email, password })
}
