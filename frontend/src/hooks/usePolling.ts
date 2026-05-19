import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Visibility-aware, abortable polling with exponential backoff.
 *
 * - First fetch is immediate (no waiting for the first interval).
 * - Hidden tabs skip the actual fetch but keep the timer armed. When the tab
 *   becomes visible again, fetches immediately.
 * - Consecutive failures back off exponentially up to `maxBackoffMs`; the
 *   backoff resets on the next success.
 * - In-flight fetches are aborted on unmount and when the next tick starts.
 * - The `fetcher` is read via ref so callers don't have to memoize it.
 *
 * NOTE: This hook does not yet do anything special with 401 responses. Once
 * PR 3 (token-expiry handling) lands, `apiFetch` will throw `UnauthorizedError`
 * which will propagate here; we'll add a one-line catch then to flip
 * `enabled=false` and let the auth context handle the redirect.
 */

export interface UsePollingOptions<T> {
  /** Called once per tick. Should respect the AbortSignal. */
  fetcher: (signal: AbortSignal) => Promise<T>
  /** Base interval between ticks, in ms. */
  intervalMs: number
  /** Set to false to stop polling (e.g. on logout). Default: true. */
  enabled?: boolean
  /** Upper bound for backoff after repeated failures. Default: 2 min. */
  maxBackoffMs?: number
}

export interface UsePollingResult<T> {
  data: T | null
  error: Error | null
  /** True only during the very first load. Subsequent refreshes don't flip it. */
  isLoading: boolean
  /** Wall-clock time of the most recent successful fetch. */
  lastUpdated: Date | null
  /** Trigger an immediate refetch (cancels any pending fetch). */
  refresh: () => void
}

const VISIBILITY_HIDDEN = 'hidden'

export function usePolling<T>({
  fetcher,
  intervalMs,
  enabled = true,
  maxBackoffMs = 120_000,
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [refreshCounter, setRefreshCounter] = useState(0)

  // Keep the latest fetcher in a ref so the polling effect doesn't need to
  // restart on every render. Callers can pass an inline closure safely.
  const fetcherRef = useRef(fetcher)
  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  const refresh = useCallback(() => {
    setRefreshCounter((c) => c + 1)
  }, [])

  useEffect(() => {
    if (!enabled) return

    let cancelled = false
    let failures = 0
    let timer: ReturnType<typeof setTimeout> | null = null
    let abort: AbortController | null = null

    const scheduleNext = () => {
      if (cancelled) return
      const delay = Math.min(intervalMs * 2 ** failures, maxBackoffMs)
      timer = setTimeout(tick, delay)
    }

    const tick = async () => {
      if (cancelled) return

      // Skip the actual fetch when the tab is hidden, but keep the timer
      // running so we resume on the same cadence.
      if (typeof document !== 'undefined' && document.visibilityState === VISIBILITY_HIDDEN) {
        scheduleNext()
        return
      }

      // Abort any in-flight fetch before starting a new one.
      if (abort) abort.abort()
      abort = new AbortController()

      try {
        const result = await fetcherRef.current(abort.signal)
        if (cancelled) return
        setData(result)
        setError(null)
        setLastUpdated(new Date())
        failures = 0
      } catch (err) {
        if (cancelled) return
        // AbortError isn't a real failure — it's cleanup.
        if ((err as Error).name === 'AbortError') return
        setError(err as Error)
        failures += 1
      } finally {
        if (!cancelled) setIsLoading(false)
      }

      scheduleNext()
    }

    const onVisibility = () => {
      if (cancelled) return
      if (document.visibilityState !== VISIBILITY_HIDDEN) {
        if (timer) {
          clearTimeout(timer)
          timer = null
        }
        void tick()
      }
    }

    document.addEventListener('visibilitychange', onVisibility)
    void tick()

    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
      if (abort) abort.abort()
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [intervalMs, enabled, maxBackoffMs, refreshCounter])

  return { data, error, isLoading, lastUpdated, refresh }
}

export default usePolling
