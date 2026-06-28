import { useCallback, useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useFloor } from '../context/FloorContext'
import { useSocket } from '../context/SocketContext'
import { canEditFloor } from '../lib/permissions'
import { computeFloorStats } from '../lib/floorStats'
import { newLabel, newSection } from '../lib/floorTemplates'
import { AddTableModal } from '../components/floor/AddTableModal'
import {
  FloorLayoutToolbar,
  LayoutEditorPanel,
} from '../components/floor/LayoutEditorPanel'
import type { CanvasSelection } from '../components/floor/FloorPlanCanvas'
import { FloorPlanCanvas } from '../components/floor/FloorPlanCanvas'
import { FloorStatsBar } from '../components/floor/FloorStatsBar'
import { StatusLegend } from '../components/floor/StatusLegend'
import { TableDetailPanel } from '../components/floor/TableDetailPanel'
import { SeatGuestModal } from '../components/floor/SeatGuestModal'
import type { FloorLabelKind, RectBounds, Table } from '../types'

export function FloorPage() {
  const { user } = useAuth()
  const { joinFloor } = useSocket()
  const {
    floor,
    sessions,
    loading,
    error,
    updateTable,
    refresh,
    addTable,
    saveFloor,
    resetFloorLayout,
  } = useFloor()
  const [selection, setSelection] = useState<CanvasSelection>(null)
  const [showAddTable, setShowAddTable] = useState(false)
  const [seatTable, setSeatTable] = useState<Table | null>(null)

  const editable = user ? canEditFloor(user.role) : false
  const selectedTable =
    selection?.type === 'table' ? floor?.tables.find((t) => t.id === selection.id) : undefined
  const stats = useMemo(() => (floor ? computeFloorStats(floor) : null), [floor])

  useEffect(() => {
    if (floor?.id) joinFloor(floor.id)
  }, [floor?.id, joinFloor])

  const handleSectionChange = useCallback(
    (sectionId: string, bounds: RectBounds) => {
      if (!floor) return
      saveFloor({
        ...floor,
        sections: floor.sections.map((s) => (s.id === sectionId ? { ...s, bounds } : s)),
      })
    },
    [floor, saveFloor],
  )

  const handleLabelChange = useCallback(
    (labelId: string, bounds: RectBounds) => {
      if (!floor) return
      saveFloor({
        ...floor,
        labels: floor.labels.map((l) => (l.id === labelId ? { ...l, bounds } : l)),
      })
    },
    [floor, saveFloor],
  )

  const handleAddSection = useCallback(async () => {
    if (!floor) return
    const name = window.prompt('Section name', 'New section')
    if (!name?.trim()) return
    const section = newSection(name.trim(), floor.width, floor.height, floor.sections.length)
    await saveFloor({ ...floor, sections: [...floor.sections, section] })
    setSelection({ type: 'section', id: section.id })
  }, [floor, saveFloor])

  const handleAddLabel = useCallback(
    async (kind: FloorLabelKind) => {
      if (!floor) return
      const defaults: Record<FloorLabelKind, string> = {
        ENTRANCE: 'Entrance',
        KITCHEN: 'Kitchen',
        BAR: 'Bar',
        CUSTOM: 'Area',
      }
      const text = window.prompt('Label text', defaults[kind]) ?? defaults[kind]
      const label = newLabel(kind, text, floor.width, floor.height)
      await saveFloor({ ...floor, labels: [...floor.labels, label] })
      setSelection({ type: 'label', id: label.id })
    },
    [floor, saveFloor],
  )

  const handleReset = useCallback(async () => {
    if (
      !confirm(
        'Start fresh? This removes all tables, sections, and custom layout. Entrance and kitchen markers will reset to defaults.',
      )
    ) {
      return
    }
    await resetFloorLayout()
    setSelection(null)
  }, [resetFloorLayout])

  const handleCanvasSize = useCallback(
    async (width: number, height: number) => {
      if (!floor || width < 400 || height < 300) return
      await saveFloor({ ...floor, width, height })
    },
    [floor, saveFloor],
  )

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
        <p>Loading floor plan…</p>
      </div>
    )
  }

  if (error || !floor) {
    return (
      <div className="page-error">
        <p>{error ?? 'Floor not found'}</p>
        <button type="button" className="btn btn-primary" onClick={() => refresh()}>
          Retry
        </button>
      </div>
    )
  }

  const layoutSelection =
    selection?.type === 'section' || selection?.type === 'label' ? selection : null

  return (
    <div className="floor-page">
      <header className="floor-page-header">
        <div>
          <h2 className="floor-page-title">{floor.name}</h2>
          <p className="muted floor-page-sub">
            {editable
              ? 'Edit layout: sections, markers, tables — drag and resize on the canvas'
              : 'Tap a table to seat guests or update status'}
          </p>
        </div>
        <div className="floor-page-actions">
          {editable && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowAddTable(true)}
            >
              + Add table
            </button>
          )}
        </div>
      </header>

      {editable && (
        <FloorLayoutToolbar
          floor={floor}
          editable={editable}
          onAddSection={handleAddSection}
          onAddLabel={handleAddLabel}
          onReset={handleReset}
          onCanvasSize={handleCanvasSize}
        />
      )}

      {stats && <FloorStatsBar stats={stats} />}

      <div className="floor-legend-row">
        <StatusLegend />
      </div>

      <div className="floor-workspace">
        <div className="floor-canvas-column">
          <FloorPlanCanvas
            floor={floor}
            sessions={sessions}
            editable={editable}
            selection={selection}
            onSelect={setSelection}
            onTableChange={updateTable}
            onSectionChange={handleSectionChange}
            onLabelChange={handleLabelChange}
          />
        </div>
        <aside className="floor-side-column">
          {layoutSelection ? (
            <LayoutEditorPanel
              floor={floor}
              selection={layoutSelection}
              onClose={() => setSelection(null)}
              onSaveFloor={saveFloor}
            />
          ) : selectedTable ? (
            <TableDetailPanel
              floor={floor}
              table={selectedTable}
              onClose={() => setSelection(null)}
              onSeatGuests={() => setSeatTable(selectedTable)}
            />
          ) : (
            <div className="table-panel table-panel-empty">
              <div className="empty-state-icon" aria-hidden>
                ◫
              </div>
              <h3>Select on the floor</h3>
              <p className="muted">
                {editable
                  ? 'Click a table, section (Indoor/Outdoor), or marker (Entrance/Kitchen) to edit. Use the layout toolbar to add or start fresh.'
                  : 'Click a table to view status and seat guests.'}
              </p>
            </div>
          )}
        </aside>
      </div>

      {seatTable && (
        <SeatGuestModal table={seatTable} onClose={() => setSeatTable(null)} />
      )}

      {showAddTable && (
        <AddTableModal
          floor={floor}
          onClose={() => setShowAddTable(false)}
          onAdd={async (payload) => {
            const t = await addTable(payload)
            setSelection({ type: 'table', id: t.id })
          }}
        />
      )}
    </div>
  )
}
