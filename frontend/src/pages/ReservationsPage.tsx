import { useCallback, useEffect, useState } from 'react'
import { reservationsApi, type Reservation } from '../api/extensions'
import { useFloor } from '../context/FloorContext'

interface FormState {
  tableId: string; guestName: string; partySize: string
  reservedFor: string; reservedUntil: string; notes: string
}

const EMPTY_FORM: FormState = {
  tableId: '', guestName: '', partySize: '2',
  reservedFor: '', reservedUntil: '', notes: '',
}

export function ReservationsPage() {
  const { floor } = useFloor()
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await reservationsApi.list()
      setReservations(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async () => {
    if (!form.tableId || !form.guestName || !form.reservedFor || !form.reservedUntil) return
    setSaving(true)
    try {
      const r = await reservationsApi.create({
        tableId: form.tableId,
        guestName: form.guestName,
        partySize: parseInt(form.partySize),
        reservedFor: new Date(form.reservedFor).toISOString(),
        reservedUntil: new Date(form.reservedUntil).toISOString(),
        notes: form.notes || undefined,
      })
      setReservations((prev) => [...prev, r])
      setShowForm(false)
      setForm(EMPTY_FORM)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create')
    } finally {
      setSaving(false)
    }
  }

  const handleRelease = async (id: string, guestName: string) => {
    if (!confirm(`Release reservation for ${guestName}?`)) return
    try {
      const updated = await reservationsApi.release(id)
      setReservations((prev) => prev.map((r) => (r.id === id ? updated : r)))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to release')
    }
  }

  const statusColor: Record<string, string> = {
    PENDING: '#1a73e8', SEATED: '#1e6b3c', RELEASED: '#888', CANCELLED: '#c00',
  }

  const availableTables = floor?.tables.filter((t) =>
    t.status === 'AVAILABLE' || t.status === 'RESERVED'
  ) ?? []

  if (loading) return <div className="page-loading"><div className="spinner" /></div>

  return (
    <div style={{ padding: '0 24px 40px' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '24px 0 20px' }}>
        <div>
          <h2 style={{ margin: 0 }}>Reservations</h2>
          <p className="muted" style={{ margin: '4px 0 0' }}>Tables auto-release if guests don't arrive by the reserved time</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>+ New reservation</button>
      </div>

      {error && (
        <div style={{ background: '#fee', border: '1px solid #fcc', borderRadius: 8, padding: '10px 16px', marginBottom: 16, color: '#c00' }}>
          {error} <button style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setError('')}>✕</button>
        </div>
      )}

      {reservations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#888' }}>
          <p style={{ fontSize: 16 }}>No reservations yet</p>
          <p style={{ fontSize: 13 }}>Click "New reservation" to hold a table for a future booking</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[...reservations]
            .sort((a, b) => new Date(a.reservedFor).getTime() - new Date(b.reservedFor).getTime())
            .map((r) => {
              const table = floor?.tables.find((t) => t.id === r.tableId)
              return (
                <div key={r.id} style={{
                  display: 'flex', alignItems: 'center', gap: 16, padding: '14px 16px',
                  background: '#fff', border: '1px solid #eee', borderRadius: 10,
                  opacity: ['RELEASED', 'CANCELLED'].includes(r.status) ? 0.6 : 1,
                }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 8, background: '#f5f5f5',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: 14,
                  }}>
                    {table?.number ?? '?'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 500, fontSize: 14 }}>{r.guestName}</span>
                      <span style={{ fontSize: 12, color: '#666' }}>· Party of {r.partySize}</span>
                      <span style={{
                        fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10,
                        background: `${statusColor[r.status]}20`,
                        color: statusColor[r.status],
                      }}>{r.status}</span>
                    </div>
                    <p style={{ margin: '3px 0 0', fontSize: 12, color: '#888' }}>
                      {new Date(r.reservedFor).toLocaleString()} → auto-release at {new Date(r.reservedUntil).toLocaleTimeString()}
                    </p>
                    {r.notes && <p style={{ margin: '2px 0 0', fontSize: 12, color: '#aaa' }}>{r.notes}</p>}
                  </div>
                  {r.status === 'PENDING' && (
                    <button
                      type="button"
                      onClick={() => handleRelease(r.id, r.guestName)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #ddd', background: '#fff', fontSize: 12, cursor: 'pointer' }}
                    >
                      Release
                    </button>
                  )}
                </div>
              )
            })}
        </div>
      )}

      {showForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 24, width: '100%', maxWidth: 460, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 20px', fontSize: 18 }}>New reservation</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Table *</label>
                <select className="input" value={form.tableId} onChange={(e) => setForm((f) => ({ ...f, tableId: e.target.value }))} style={{ width: '100%' }}>
                  <option value="">Select a table</option>
                  {availableTables.map((t) => (
                    <option key={t.id} value={t.id}>Table {t.number} (capacity {t.capacity})</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Guest name *</label>
                  <input className="input" value={form.guestName} onChange={(e) => setForm((f) => ({ ...f, guestName: e.target.value }))} placeholder="Smith" style={{ width: '100%' }} />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Party size</label>
                  <input className="input" type="number" min="1" max="20" value={form.partySize} onChange={(e) => setForm((f) => ({ ...f, partySize: e.target.value }))} style={{ width: '100%' }} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Arrival time *</label>
                  <input className="input" type="datetime-local" value={form.reservedFor} onChange={(e) => setForm((f) => ({ ...f, reservedFor: e.target.value }))} style={{ width: '100%' }} />
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Auto-release at *</label>
                  <input className="input" type="datetime-local" value={form.reservedUntil} onChange={(e) => setForm((f) => ({ ...f, reservedUntil: e.target.value }))} style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>Notes</label>
                <input className="input" value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} placeholder="Window seat preferred…" style={{ width: '100%' }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleCreate} disabled={saving || !form.tableId || !form.guestName || !form.reservedFor || !form.reservedUntil}>
                {saving ? 'Creating…' : 'Create reservation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
