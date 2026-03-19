import type { ReviewLog, ReviewStatus } from '../types/dashboard'

type Props = {
  reviews: ReviewLog[]
  onDelete: (id: number) => void
}

const STATUS_STYLE: Record<ReviewStatus, { bg: string; text: string; label: string }> = {
  pending: { bg: '#3b3b4f', text: '#a0a0b0', label: 'Pendente' },
  running: { bg: '#422006', text: '#fbbf24', label: 'Revisando...' },
  completed: { bg: '#052e16', text: '#22c55e', label: 'Concluido' },
  failed: { bg: '#450a0a', text: '#ef4444', label: 'Falhou' },
}

function StatusBadge({ status, error }: { status: ReviewStatus; error?: string }) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.pending
  return (
    <div>
      <span
        style={{
          background: style.bg,
          color: style.text,
          padding: '2px 8px',
          borderRadius: 4,
          fontSize: 11,
          fontWeight: 600,
          cursor: error ? 'help' : 'default',
        }}
        title={error || undefined}
      >
        {style.label}
      </span>
      {error && (
        <div
          style={{
            color: '#ef4444',
            fontSize: 10,
            marginTop: 4,
            maxWidth: 180,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={error}
        >
          {error}
        </div>
      )}
    </div>
  )
}

function FindingsBadges({ review }: { review: ReviewLog }) {
  if (review.total_findings === 0 && review.status === 'completed') {
    return <span style={{ color: '#22c55e', fontSize: 12 }}>✅</span>
  }
  if (review.total_findings === 0) return <span style={{ color: '#666' }}>-</span>
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {review.critical_count > 0 && (
        <span style={{ color: '#ef4444', fontSize: 12 }}>🔴 {review.critical_count}</span>
      )}
      {review.warning_count > 0 && (
        <span style={{ color: '#fbbf24', fontSize: 12 }}>🟡 {review.warning_count}</span>
      )}
      {review.suggestion_count > 0 && (
        <span style={{ color: '#a78bfa', fontSize: 12 }}>💡 {review.suggestion_count}</span>
      )}
    </div>
  )
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'agora'
  if (minutes < 60) return `${minutes}min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

export function ReviewTable({ reviews, onDelete }: Props) {
  return (
    <div style={{ background: '#1e1e2e', borderRadius: 8, padding: 20 }}>
      <h2 style={{ margin: '0 0 12px', fontSize: 16, color: '#e0e0e0' }}>Reviews recentes</h2>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333', color: '#888', textAlign: 'left' }}>
              <th style={{ padding: '8px 12px' }}>MR</th>
              <th style={{ padding: '8px 12px' }}>Branch</th>
              <th style={{ padding: '8px 12px' }}>Autor</th>
              <th style={{ padding: '8px 12px' }}>Status</th>
              <th style={{ padding: '8px 12px' }}>Achados</th>
              <th style={{ padding: '8px 12px' }}>Tempo</th>
              <th style={{ padding: '8px 12px' }}>Quando</th>
              <th style={{ padding: '8px 12px', width: 40 }}></th>
            </tr>
          </thead>
          <tbody>
            {reviews.map((review) => (
              <tr
                key={review.id}
                style={{
                  borderBottom: '1px solid #2a2a3e',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#252538')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ color: '#e0e0e0', fontWeight: 500 }}>
                    !{review.mr_iid}
                  </div>
                  <div style={{ color: '#888', fontSize: 11, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {review.mr_title}
                  </div>
                </td>
                <td style={{ padding: '10px 12px', color: '#a78bfa', fontSize: 12 }}>
                  {review.source_branch}
                </td>
                <td style={{ padding: '10px 12px', color: '#888' }}>
                  {review.author}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <StatusBadge status={review.status} error={review.error_message || undefined} />
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <FindingsBadges review={review} />
                </td>
                <td style={{ padding: '10px 12px', color: '#888' }}>
                  {review.duration_seconds > 0 ? `${review.duration_seconds.toFixed(1)}s` : '...'}
                </td>
                <td style={{ padding: '10px 12px', color: '#666', fontSize: 11 }}>
                  {timeAgo(review.created_at)}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <button
                    onClick={() => onDelete(review.id)}
                    title="Remover review"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#666',
                      cursor: 'pointer',
                      fontSize: 14,
                      padding: 4,
                      borderRadius: 4,
                      transition: 'color 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = '#666')}
                  >
                    ✕
                  </button>
                </td>
              </tr>
            ))}
            {reviews.length === 0 && (
              <tr>
                <td colSpan={8} style={{ padding: 24, textAlign: 'center', color: '#666' }}>
                  Nenhum review registrado ainda.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
