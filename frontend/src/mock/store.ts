import { createEmptyFloor } from '../lib/floorTemplates'
import { DEMO_PASSWORD, DEMO_USERS, INITIAL_FLOOR } from './data'
import { isValidTransition } from '../lib/statusTransitions'
import type {
  AuthUser,
  CreateTablePayload,
  CreateUserPayload,
  DiningSession,
  Floor,
  LoginResponse,
  SeatGuestPayload,
  Table,
  TableStatus,
  User,
} from '../types'

const STORAGE_KEY = 'foh-mock-store'

interface StoreState {
  users: User[]
  floor: Floor
  sessions: DiningSession[]
  passwords: Record<string, string>
}

const LEGACY_SECTION_BOUNDS: Record<string, { x: number; y: number; width: number; height: number }> =
  {
    'sec-indoor': { x: 40, y: 48, width: 580, height: 300 },
    'sec-outdoor': { x: 40, y: 380, width: 420, height: 200 },
    'sec-bar': { x: 680, y: 48, width: 280, height: 300 },
  }

function migrateFloor(floor: Floor): Floor {
  const w = floor.width ?? 1000
  const h = floor.height ?? 620
  return {
    ...floor,
    width: w,
    height: h,
    sections: (floor.sections ?? []).map((s, i) => ({
      ...s,
      bounds:
        s.bounds ??
        LEGACY_SECTION_BOUNDS[s.id] ?? {
          x: 40 + (i % 2) * 320,
          y: 48 + Math.floor(i / 2) * 200,
          width: 400,
          height: 200,
        },
    })),
    labels:
      floor.labels ??
      [
        {
          id: 'lbl-entrance',
          kind: 'ENTRANCE' as const,
          text: 'Entrance',
          bounds: { x: w / 2 - 100, y: h - 56, width: 200, height: 44 },
        },
        {
          id: 'lbl-kitchen',
          kind: 'KITCHEN' as const,
          text: 'Kitchen',
          bounds: { x: w - 140, y: 12, width: 120, height: 44 },
        },
      ],
    tables: floor.tables.map((t) => ({
      ...t,
      shape: t.shape ?? (t.type === 'BAR' ? 'CIRCLE' : 'RECTANGLE'),
    })),
  }
}

function loadState(): StoreState {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as StoreState
      parsed.floor = migrateFloor(parsed.floor)
      return parsed
    } catch {
      /* fall through */
    }
  }
  return {
    users: structuredClone(DEMO_USERS),
    floor: structuredClone(INITIAL_FLOOR),
    sessions: [],
    passwords: Object.fromEntries(DEMO_USERS.map((u) => [u.email, DEMO_PASSWORD])),
  }
}

let state = loadState()

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function delay(ms = 280) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function activeSessionForTable(tableId: string): DiningSession | undefined {
  return state.sessions.find(
    (s) => s.tableId === tableId && !['PAID', 'CLEANING', 'AVAILABLE'].includes(s.status),
  )
}

export async function mockLogin(
  email: string,
  password: string,
): Promise<LoginResponse> {
  await delay()
  const user = state.users.find((u) => u.email === email && u.isActive)
  if (!user || state.passwords[email] !== password) {
    throw new Error('Invalid email or password')
  }
  const expiresAt = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString()
  return {
    accessToken: `mock-token-${user.id}`,
    expiresAt,
    user: { id: user.id, name: user.name, email: user.email, role: user.role },
  }
}

export async function mockGetMe(token: string): Promise<AuthUser> {
  await delay(120)
  const userId = token.replace('mock-token-', '')
  const user = state.users.find((u) => u.id === userId && u.isActive)
  if (!user) throw new Error('Unauthorized')
  return { id: user.id, name: user.name, email: user.email, role: user.role }
}

export async function mockGetFloor(): Promise<Floor> {
  await delay(150)
  return structuredClone(state.floor)
}

export async function mockUpdateFloor(floor: Floor): Promise<Floor> {
  await delay()
  state.floor = structuredClone(floor)
  persist()
  return structuredClone(state.floor)
}

export async function mockUpdateTable(tableId: string, patch: Partial<Table>): Promise<Table> {
  await delay()
  const table = state.floor.tables.find((t) => t.id === tableId)
  if (!table) throw new Error('Table not found')
  Object.assign(table, patch)
  persist()
  return structuredClone(table)
}

export async function mockPatchTableStatus(
  tableId: string,
  status: TableStatus,
): Promise<Table> {
  await delay()
  const table = state.floor.tables.find((t) => t.id === tableId)
  if (!table) throw new Error('Table not found')
  if (!isValidTransition(table.status, status)) {
    const err = new Error(`Invalid transition from ${table.status} to ${status}`)
    ;(err as Error & { status: number }).status = 400
    throw err
  }
  const session = activeSessionForTable(tableId)
  if (status === 'SEATED' && session) {
    const err = new Error('Table already has an active session')
    ;(err as Error & { status: number }).status = 409
    throw err
  }
  table.status = status
  if (session) session.status = status
  persist()
  return structuredClone(table)
}

export async function mockCreateSession(payload: SeatGuestPayload): Promise<DiningSession> {
  await delay()
  const table = state.floor.tables.find((t) => t.id === payload.tableId)
  if (!table) throw new Error('Table not found')
  if (payload.partySize > table.capacity) {
    const err = new Error('Party size exceeds table capacity')
    ;(err as Error & { status: number }).status = 400
    throw err
  }
  if (!['AVAILABLE', 'RESERVED'].includes(table.status)) {
    const err = new Error('Table is not available for seating')
    ;(err as Error & { status: number }).status = 400
    throw err
  }
  if (activeSessionForTable(payload.tableId)) {
    const err = new Error('Table already has an active session')
    ;(err as Error & { status: number }).status = 409
    throw err
  }
  const session: DiningSession = {
    id: `sess-${Date.now()}`,
    tableId: payload.tableId,
    guestName: payload.guestName,
    partySize: payload.partySize,
    seatedAt: new Date().toISOString(),
    status: 'SEATED',
  }
  table.status = 'SEATED'
  state.sessions.push(session)
  persist()
  return structuredClone(session)
}

export async function mockCloseSession(sessionId: string): Promise<DiningSession> {
  await delay()
  const session = state.sessions.find((s) => s.id === sessionId)
  if (!session) throw new Error('Session not found')
  const table = state.floor.tables.find((t) => t.id === session.tableId)
  if (table) table.status = 'CLEANING'
  session.status = 'CLEANING'
  persist()
  return structuredClone(session)
}

export async function mockDeleteTable(tableId: string): Promise<void> {
  await delay()
  const session = activeSessionForTable(tableId)
  if (session) {
    throw new Error('Cannot remove table with an active session. Release the table first.')
  }
  state.floor.tables = state.floor.tables.filter((t) => t.id !== tableId)
  state.sessions = state.sessions.filter((s) => s.tableId !== tableId)
  persist()
}

export async function mockResetFloorLayout(): Promise<Floor> {
  await delay()
  state.floor = createEmptyFloor({
    id: state.floor.id,
    name: state.floor.name,
    width: state.floor.width,
    height: state.floor.height,
  })
  state.sessions = []
  persist()
  return structuredClone(state.floor)
}

export async function mockAddTable(payload: CreateTablePayload): Promise<Table> {
  await delay()
  const w = payload.width ?? (payload.shape === 'CIRCLE' ? 64 : 88)
  const h = payload.height ?? (payload.shape === 'CIRCLE' ? 64 : 72)
  const table: Table = {
    id: `t-${Date.now()}`,
    sectionId: payload.sectionId,
    number: payload.number,
    capacity: payload.capacity,
    type: payload.type,
    shape: payload.shape,
    status: 'AVAILABLE',
    x: payload.x ?? 200,
    y: payload.y ?? 200,
    width: w,
    height: h,
    rotation: 0,
  }
  state.floor.tables.push(table)
  persist()
  return structuredClone(table)
}

export async function mockGetSessions(): Promise<DiningSession[]> {
  await delay(100)
  return structuredClone(state.sessions)
}

export async function mockGetUsers(): Promise<User[]> {
  await delay()
  return structuredClone(state.users)
}

export async function mockCreateUser(payload: CreateUserPayload): Promise<User> {
  await delay()
  if (state.users.some((u) => u.email === payload.email)) {
    throw new Error('Email already exists')
  }
  const user: User = {
    id: `u-${Date.now()}`,
    name: payload.name,
    email: payload.email,
    role: payload.role,
    isActive: true,
  }
  state.users.push(user)
  state.passwords[payload.email] = payload.password
  persist()
  return structuredClone(user)
}

export async function mockSetUserActive(userId: string, isActive: boolean): Promise<User> {
  await delay()
  const user = state.users.find((u) => u.id === userId)
  if (!user) throw new Error('User not found')
  user.isActive = isActive
  persist()
  return structuredClone(user)
}

export function mockResetStore() {
  state = {
    users: structuredClone(DEMO_USERS),
    floor: structuredClone(INITIAL_FLOOR),
    sessions: [],
    passwords: Object.fromEntries(DEMO_USERS.map((u) => [u.email, DEMO_PASSWORD])),
  }
  persist()
}
