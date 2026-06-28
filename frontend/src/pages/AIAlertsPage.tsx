import { useCallback, useEffect, useState } from 'react'
import { aiApi, type AIEvent } from '../api/extensions'
import { useAuth } from '../context/AuthContext'
import { useFloor } from '../context/FloorContext'
import { useSocket } from '../context/SocketContext'

export function AIAlertsPage() {
  const { user } = useAuth()
  const { floor } = useFloor()
  const { on } = useSocket()
  const [alerts, setAlerts] = useState<AIEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [showResolved, setShowResolved] = useState(false)
  const [error, setError] = useState('')
  const [toast, setToast] = useState<string | null>(null)

  const load = useCallback(async (resolved = false) => {
    try {
      const data = await aiApi.getAlerts(resolved)
      setAlerts(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load(showResolved) }, [load, showResolved])

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(t)
  }, [toast])

  useEffect(() => {
    if (!user) return
    const unsub = on('ai_alert', (payload) => {
      const alert = payload as AIEvent
      if (alert.targetRole !== user.role) return
      setAlerts((prev) => [alert, ...prev])
      setToast(alert.message)
    })
    return unsub
  }, [on, user])

  const handleResolve = async (id: string) => {
    try {
      await aiApi.resolveAlert(id)
      setAlerts((prev) => prev.filter((a) => a.id !== id))
      window.dispatchEvent(new CustomEvent('foh:alert-dismissed'))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to resolve')
    }
  }

  const eventTypeColor: Record<string, { bg: string; color: string; label: string }> = {
    WAIT_ALERT: { bg: '#fff3cd', color: '#856404', label: 'Wait Alert' },
    DIRTY_ALERT: { bg: '#f8d7da', color: '#721c24', label: 'Dirty Table' },
    DEPARTURE_ALERT: { bg: '#d1ecf1', color: '#0c5460', label: 'Departure' },
    SEATING_SUGGESTION: { bg: '#d4edda', color: '#155724', label: 'Seating' },
    SHIFT_REPORT: { bg: '#e2e3e5', color: '#383d41', label: 'Report' },
  }

  if (loading) return <div className="page-loading"><div className="spinner" /></div>

  return (
    <div style={{ padding: '0 24px 40px' }}>
      {toast && (
        <div
          style={{
            position: 'fixed',
            top: 16,
            right: 16,
            zIndex: 1000,
            maxWidth: 360,
            padding: '12px 16px',
            background: '#1e293b',
            color: '#fff',
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
            fontSize: 14,
          }}
        >
          {toast}
        </div>
      )}

      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '24px 0 20px' }}>
        <div>
          <h2 style={{ margin: 0 }}>AI Alerts</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>Llama monitors tables and fires alerts automatically</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            type="button"
            className={`filter-chip ${!showResolved ? 'active' : ''}`}
            onClick={() => setShowResolved(false)}
          >
            Active ({alerts.filter(a => !a.resolved).length})
          </button>
          <button
            type="button"
            className={`filter-chip ${showResolved ? 'active' : ''}`}
            onClick={() => setShowResolved(true)}
          >
            Resolved
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fee', border: '1px solid #fcc', borderRadius: 8, padding: '10px 16px', marginBottom: 16, color: '#c00' }}>
          {error}
        </div>
      )}

      {alerts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#888' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✓</div>
          <p style={{ fontSize: 16 }}>No active alerts</p>
          <p style={{ fontSize: 13 }}>Llama checks every 2 minutes — you'll see alerts here when tables need attention</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {alerts.map((alert) => {
            const table = floor?.tables.find((t) => t.id === alert.tableId)
            const style = eventTypeColor[alert.eventType] ?? { bg: '#f5f5f5', color: '#444', label: alert.eventType }
            return (
              <div key={alert.id} style={{
                display: 'flex', gap: 14, padding: '14px 16px',
                background: '#fff', border: '1px solid #eee', borderRadius: 10,
                borderLeft: `4px solid ${style.color}`,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10,
                      background: style.bg, color: style.color,
                    }}>
                      {style.label}
                    </span>
                    {table && (
                      <span style={{ fontSize: 12, color: '#666' }}>Table {table.number}</span>
                    )}
                    <span style={{ fontSize: 11, color: '#aaa', marginLeft: 'auto' }}>
                      {new Date(alert.createdAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: '#333' }}>
                    {alert.message}
                  </p>
                </div>
                {!alert.resolved && (
                  <button
                    type="button"
                    onClick={() => handleResolve(alert.id)}
                    style={{
                      padding: '6px 12px', borderRadius: 6, border: '1px solid #ddd',
                      background: '#fff', fontSize: 12, cursor: 'pointer',
                      alignSelf: 'flex-start', whiteSpace: 'nowrap',
                    }}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
