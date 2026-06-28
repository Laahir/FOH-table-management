import { getNextStatuses, STATUS_CONFIG } from '../../services/tableConfig'
import { OccupancyTimer } from '../floor/OccupancyTimer'
import type { DiningSession, Table, TableStatus } from '../../types'

interface SessionCardProps {
  session: DiningSession
  table?: Table
  sectionName?: string
  onAdvance: (tableId: string, status: TableStatus) => void
  onRelease: (sessionId: string) => void
}

export function SessionCard({
  session,
  table,
  sectionName,
  onAdvance,
  onRelease,
}: SessionCardProps) {
  const status = session.status as TableStatus
  const cfg = STATUS_CONFIG[status]
  const next = getNextStatuses(status)
  const primaryNext = next[0]

  return (
    <article className="session-card" style={{ borderLeftColor: cfg.border }}>
      <div className="session-card__main">
        <div className="session-card__header">
          <span className="session-table-badge">T{table?.number ?? '?'}</span>
          {sectionName && <span className="session-section-tag">{sectionName}</span>}
          <span
            className="session-status-pill"
            style={{ backgroundColor: cfg.bg, color: cfg.text, borderColor: cfg.border }}
          >
            {cfg.label}
          </span>
        </div>
        <h3 className="session-card__title">
          {session.guestName || 'Walk-in'}
          <span className="muted"> · party of {session.partySize}</span>
        </h3>
        <p className="session-card__meta">
          <OccupancyTimer seatedAt={session.seatedAt} /> seated
          {table && (
            <span>
              {' '}
              · {table.capacity} seats
            </span>
          )}
        </p>
      </div>

      <div className="session-card__actions">
        {primaryNext && !['CLEANING', 'AVAILABLE'].includes(status) && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => onAdvance(session.tableId, primaryNext)}
          >
            → {STATUS_CONFIG[primaryNext].label}
          </button>
        )}
        {next.length > 1 && !['CLEANING', 'AVAILABLE'].includes(status) && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onAdvance(session.tableId, next[1])}
          >
            → {STATUS_CONFIG[next[1]].label}
          </button>
        )}
        {!['CLEANING', 'AVAILABLE'].includes(status) && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => onRelease(session.id)}
          >
            Release table
          </button>
        )}
      </div>
    </article>
  )
}
