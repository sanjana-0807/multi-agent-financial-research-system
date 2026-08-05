// Email validation
export function isValidEmail(email) {
  if (!email) return false
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

// Password validation — at least 6 characters
export function isValidPassword(password) {
  return typeof password === 'string' && password.length >= 6
}

// Check if a file is a PDF and within size limit
export function isValidPdfFile(file, maxSizeMB = 10) {
  if (!file) return { valid: false, error: 'No file selected' }
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    return { valid: false, error: 'Only PDF files are allowed' }
  }
  if (file.size > maxSizeMB * 1024 * 1024) {
    return { valid: false, error: `File must be under ${maxSizeMB}MB` }
  }
  return { valid: true, error: null }
}

// Check if a value is a non-empty string
export function isNonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0
}
