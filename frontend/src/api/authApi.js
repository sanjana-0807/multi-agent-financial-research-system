import axiosClient from './axiosClient.js'

// Matches backend/routes/auth.py
// POST /auth/signup - accepts username, email, password, confirm_password
// POST /auth/login - checks credentials, returns a JWT token
export function signup(username, email, password, confirmPassword) {
  return axiosClient.post('/auth/signup', {
    username,
    email,
    password,
    confirm_password: confirmPassword,
  })
}

export function login(email, password) {
  return axiosClient.post('/auth/login', { username: email, password })
}