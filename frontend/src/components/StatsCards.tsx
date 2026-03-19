import type { Stats } from '../types/dashboard'

type Props = { stats: Stats | null }

export function StatsCards({ stats }: Props) {
  if (!stats) return null

  const cards = [
    { label: 'Reviews', value: stats.total_reviews, color: '#6366f1' },
    { label: 'Em andamento', value: stats.running, color: '#f59e0b' },
    { label: 'Achados', value: stats.total_findings, color: '#8b5cf6' },
    { label: 'Criticos', value: stats.total_critical, color: '#ef4444' },
    { label: 'Falhas', value: stats.failed, color: '#dc2626' },
    { label: 'Tempo medio', value: `${stats.avg_duration_seconds}s`, color: '#06b6d4' },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            background: '#1e1e2e',
            borderRadius: 8,
            padding: '16px 20px',
            borderLeft: `3px solid ${card.color}`,
          }}
        >
          <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>{card.label}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: '#e0e0e0' }}>{card.value}</div>
        </div>
      ))}
    </div>
  )
}
