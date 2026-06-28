import { OCCUPIED_STATUSES } from '../services/tableConfig'
import type { Floor, FloorStats } from '../types'

export function computeFloorStats(floor: Floor): FloorStats {
  const total = floor.tables.length
  const available = floor.tables.filter((t) => t.status === 'AVAILABLE').length
  const reserved = floor.tables.filter((t) => t.status === 'RESERVED').length
  const cleaning = floor.tables.filter((t) => t.status === 'CLEANING').length
  const occupied = floor.tables.filter((t) => OCCUPIED_STATUSES.includes(t.status)).length
  const occupancyRate = total > 0 ? Math.round((occupied / total) * 100) : 0

  return { total, available, occupied, reserved, cleaning, occupancyRate }
}
