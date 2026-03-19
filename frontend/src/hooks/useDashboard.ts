import { useCallback, useEffect, useState } from 'react'
import type { QueueStatus, ReviewLog, Stats } from '../types/dashboard'

const API_BASE = '/api/dashboard'

export function useDashboard(pollInterval = 5000) {
  const [reviews, setReviews] = useState<ReviewLog[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [queue, setQueue] = useState<QueueStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = useCallback(async () => {
    try {
      const [reviewsRes, statsRes, queueRes] = await Promise.all([
        fetch(`${API_BASE}/reviews?limit=30`),
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/queue`),
      ])

      if (reviewsRes.ok) setReviews(await reviewsRes.json())
      if (statsRes.ok) setStats(await statsRes.json())
      if (queueRes.ok) setQueue(await queueRes.json())
    } catch (err) {
      console.error('Dashboard fetch failed:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteReview = useCallback(async (id: number) => {
    try {
      const res = await fetch(`${API_BASE}/reviews/${id}`, { method: 'DELETE' })
      if (res.ok) {
        setReviews((prev) => prev.filter((r) => r.id !== id))
        fetchAll()
      }
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }, [fetchAll])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, pollInterval)
    return () => clearInterval(interval)
  }, [fetchAll, pollInterval])

  return { reviews, stats, queue, loading, refresh: fetchAll, deleteReview }
}
