// API base URL — axiosClient reads from env, but this provides a fallback reference
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Polling interval for research job status checks (ms)
export const POLL_INTERVAL = 3000

// Job status enums — matches backend response values
export const JOB_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
}

// Document upload constraints
export const MAX_FILE_SIZE_MB = 10
export const ALLOWED_FILE_TYPES = ['.pdf']

// Auth token key in localStorage
export const AUTH_TOKEN_KEY = 'authToken'

// Default pagination
export const DEFAULT_PAGE_SIZE = 20
