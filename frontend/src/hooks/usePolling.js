import { useEffect, useRef } from 'react'

// Calls `callback` every `interval` ms while `enabled` is true.
// Stops automatically when `enabled` flips to false or component unmounts.
// Used by useResearchJob to poll job status until completion.
function usePolling(callback, interval = 3000, enabled = true) {
  const savedCallback = useRef(callback)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return

    const id = setInterval(() => savedCallback.current(), interval)
    return () => clearInterval(id)
  }, [interval, enabled])
}

export default usePolling
