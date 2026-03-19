import { QueuePanel } from './components/QueuePanel'
import { ReviewTable } from './components/ReviewTable'
import { StatsCards } from './components/StatsCards'
import { useDashboard } from './hooks/useDashboard'

export function App() {
  const { reviews, stats, queue, loading, refresh, deleteReview } = useDashboard(5000)

  return (
    <div style={{ minHeight: '100vh', background: '#13131f', color: '#e0e0e0', fontFamily: 'system-ui, sans-serif' }}>
      <header
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid #2a2a3e',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28 }}>🦀</span>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Pedroclaw</h1>
            <span style={{ fontSize: 11, color: '#888' }}>Squad XI Dashboard</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {loading && <span style={{ color: '#888', fontSize: 12 }}>Carregando...</span>}
          <button
            onClick={refresh}
            style={{
              background: '#2a2a3e',
              border: '1px solid #3a3a4e',
              color: '#e0e0e0',
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            Atualizar
          </button>
        </div>
      </header>

      <main style={{ padding: 24, maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>
        <StatsCards stats={stats} />
        <QueuePanel queue={queue} />
        <ReviewTable reviews={reviews} onDelete={deleteReview} />
      </main>

      <footer style={{ padding: '16px 24px', textAlign: 'center', color: '#444', fontSize: 11 }}>
        Pedroclaw v0.1.0 | Squad XI: Aratu 🦀 Coral 🪸 Nautilo 🐚 Baiacu 🐡
      </footer>
    </div>
  )
}
