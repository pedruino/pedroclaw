import type { QueueStatus } from '../types/dashboard'

type Props = { queue: QueueStatus | null }

export function QueuePanel({ queue }: Props) {
  if (!queue) return null

  return (
    <div style={{ background: '#1e1e2e', borderRadius: 8, padding: 20 }}>
      <h2 style={{ margin: '0 0 12px', fontSize: 16, color: '#e0e0e0' }}>
        Fila de processamento
      </h2>

      <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
        <div>
          <span style={{ color: '#888', fontSize: 12 }}>Ativos</span>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#22c55e' }}>{queue.active.length}</div>
        </div>
        <div>
          <span style={{ color: '#888', fontSize: 12 }}>Na fila</span>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f59e0b' }}>{queue.queued}</div>
        </div>
        <div>
          <span style={{ color: '#888', fontSize: 12 }}>Agendados</span>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#6366f1' }}>{queue.scheduled}</div>
        </div>
      </div>

      {queue.active.length > 0 && (
        <div>
          {queue.active.map((task) => (
            <div
              key={task.id}
              style={{
                padding: '8px 12px',
                background: '#2a2a3e',
                borderRadius: 6,
                marginBottom: 6,
                fontSize: 13,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <span style={{ color: '#22c55e', marginRight: 8 }}>●</span>
                <span style={{ color: '#e0e0e0' }}>{task.name}</span>
                <span style={{ color: '#888', marginLeft: 8 }}>
                  MR #{String(task.args?.mr_iid ?? task.args?.issue_iid ?? '?')}
                </span>
              </div>
              <span style={{ color: '#666', fontSize: 11 }}>{task.worker}</span>
            </div>
          ))}
        </div>
      )}

      {queue.active.length === 0 && queue.queued === 0 && (
        <div style={{ color: '#666', fontSize: 13 }}>Nenhuma task em processamento.</div>
      )}
    </div>
  )
}
