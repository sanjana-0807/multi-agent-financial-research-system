import { useState, useEffect } from 'react'

// Delays updating a value until the user stops changing it for `delay` ms.
// Useful for search inputs — avoids firing an API call on every keystroke.
function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}

export default useDebounce
