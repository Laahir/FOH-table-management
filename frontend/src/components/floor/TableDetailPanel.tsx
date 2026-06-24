import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useFloor } from '../../context/FloorContext'
import { canEditFloor, canSeatGuests } from '../../lib/permissions'
import { STATUS_CONFIG } from '../../services/tableConfig'
import type { Floor, Table, TableType } from '../../types'
import { OccupancyTimer } from './OccupancyTimer'
import { PrintQRButton } from './PrintQRButton'
import { SeatGuestModal } from './SeatGuestModal'
import { StatusActions } from './StatusActions'

interface TableDetailPanelProps {
  floor: Floor
  table: Table
  onClose: () => void
}

export function TableDetailPanel({ floor, table, onClose }: TableDetailPanelProps) {
  const { user } = useAuth()
  const { sessions, changeStatus, updateTable, deleteTable } = useFloor()
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [layoutError, setLayoutError] = useState<string | null>(null)
  const [showSeat, setShowSeat] = useState(false)

  const session = sessions.find(
    (s) =>
      s.tableId === table.id &&
      ['SEATED', 'ACTIVE', 'BILLING', 'PAID'].includes(s.status),
  )
  const section = floor.sections.find((s) => s.id === table.sectionId)
  const editable = user ? canEditFloor(user.role) : false
  const canSeat = user ? canSeatGuests(user.role) : false

  async function handleStatus(next: typeof table.status) {
    setStatusLoading(true)
    setStatusError(null)
    try {
      await changeStatus(table.id, next)
    } catch (e) {
      setStatusError(e instanceof Error ? e.message : 'Status update failed')
    } finally {
      setStatusLoading(false)
    }
  }

  return (
    <aside className="table-panel">
      <div className="panel-header">
        <div>
          <p className="panel-eyebrow">{section?.name ?? 'Floor'}</p>
          <h2>Table {table.number}</h2>
        </div>
        <button type="button" className="btn-icon" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>

      <div
        className="status-banner"
        style={{
          backgroundColor: STATUS_CONFIG[table.status].bg,
          borderColor: STATUS_CONFIG[table.status].border,
          color: STATUS_CONFIG[table.status].text,
        }}
      >
        {STATUS_CONFIG[table.status].label}
        {session && (
          <span className="status-banner__timer">
            <OccupancyTimer seatedAt={session.seatedAt} />
          </span>
        )}
      </div>

      <dl className="detail-list">
        <div>
          <dt>Capacity</dt>
          <dd>
            {editable ? (
              <input
                type="number"
                min={1}
                max={20}
                className="input input-sm"
                value={table.capacity}
                onChange={(e) =>
                  updateTable(table.id, { capacity: Number(e.target.value) })
                }
              />
            ) : (
              `${table.capacity} guests`
            )}
          </dd>
        </div>
        {editable && (
          <>
            <div>
              <dt>Type</dt>
              <dd>
                <select
                  className="input"
                  value={table.type}
                  onChange={(e) =>
                    updateTable(table.id, { type: e.target.value as TableType })
                  }
                >
                  <option value="STANDARD">Standard</option>
                  <option value="BOOTH">Booth</option>
                  <option value="BAR">Bar</option>
                  <option value="VIP">VIP</option>
                </select>
              </dd>
            </div>
            <div>
              <dt>Size (px)</dt>
              <dd className="size-inputs">
                <input
                  type="number"
                  className="input input-sm"
                  min={48}
                  value={table.width}
                  onChange={(e) =>
                    updateTable(table.id, { width: Number(e.target.value) })
                  }
                  aria-label="Width"
                />
                <span>×</span>
                <input
                  type="number"
                  className="input input-sm"
                  min={48}
                  value={table.height}
                  onChange={(e) =>
                    updateTable(table.id, { height: Number(e.target.value) })
                  }
                  aria-label="Height"
                />
              </dd>
            </div>
          </>
        )}
        {session && (
          <>
            {session.guestName && (
              <div>
                <dt>Guest</dt>
                <dd>{session.guestName}</dd>
              </div>
            )}
            <div>
              <dt>Party size</dt>
              <dd>{session.partySize} guests</dd>
            </div>
          </>
        )}
      </dl>

      {statusError && <p className="form-error">{statusError}</p>}

      <div className="panel-section">
        <h3>Update status</h3>
        <StatusActions
          current={table.status}
          onSelect={handleStatus}
          loading={statusLoading}
        />
      </div>

      {/* QR code — always visible so staff can print/share anytime */}
      <div className="panel-section">
        <h3>Guest QR code</h3>
        <PrintQRButton tableId={table.id} tableNumber={table.number} />
      </div>

      {editable && (
        <div className="panel-section">
          <button
            type="button"
            className="btn btn-ghost btn-block layout-delete-btn"
            onClick={async () => {
              if (!confirm(`Remove table ${table.number} from the floor plan?`)) return
              setLayoutError(null)
              try {
                await deleteTable(table.id)
                onClose()
              } catch (e) {
                setLayoutError(e instanceof Error ? e.message : 'Could not remove table')
              }
            }}
          >
            Remove table from layout
          </button>
          {layoutError && <p className="form-error">{layoutError}</p>}
        </div>
      )}

      <div className="panel-actions">
        {canSeat && ['AVAILABLE', 'RESERVED'].includes(table.status) && (
          <button
            type="button"
            className="btn btn-primary btn-block"
            onClick={() => setShowSeat(true)}
          >
            Seat guests here
          </button>
        )}
        {table.status === 'CLEANING' && (
          <button
            type="button"
            className="btn btn-secondary btn-block"
            onClick={() => handleStatus('AVAILABLE')}
            disabled={statusLoading}
          >
            Mark as clean
          </button>
        )}
      </div>

      {showSeat && (
        <SeatGuestModal
          table={table}
          onClose={() => setShowSeat(false)}
        />
      )}
    </aside>
  )
}
