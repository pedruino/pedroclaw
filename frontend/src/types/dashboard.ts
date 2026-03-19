export type ReviewStatus = 'pending' | 'running' | 'completed' | 'failed'

export type ReviewLog = {
  id: number
  project_id: number
  mr_iid: number
  mr_title: string
  source_branch: string
  author: string
  engine: string
  status: ReviewStatus
  total_findings: number
  critical_count: number
  warning_count: number
  suggestion_count: number
  duration_seconds: number
  squad_details: Record<string, unknown>
  error_message: string
  created_at: string | null
  completed_at: string | null
}

export type Stats = {
  total_reviews: number
  completed: number
  failed: number
  running: number
  total_findings: number
  total_critical: number
  avg_duration_seconds: number
}

export type ActiveTask = {
  id: string
  name: string
  worker: string
  args: Record<string, unknown>
  started: number | null
}

export type QueueStatus = {
  active: ActiveTask[]
  queued: number
  scheduled: number
}
