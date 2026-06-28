import { useCallback, useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { aiApi, type AIEvent } from '../../api/extensions'
import { useAuth } from '../../context/AuthContext'
import { useSocket } from '../../context/SocketContext'
import { canEditFloor, canManageUsers } from '../../lib/permissions'

function canManageMenu(role: string) { return role === 'OWNER' || role === 'MANAGER' }
function canViewReports(role: string) { return role === 'OWNER' || role === 'MANAGER' }

const NAV = [
  { to: '/floor',        label: 'Floor plan',    icon: '◫',  ownerOnly: false, managerOnly: false },
  { to: '/sessions',     label: 'Sessions',      icon: '☰',  ownerOnly: false, managerOnly: false },
  { to: '/reservations', label: 'Reservations',  icon: '📅', ownerOnly: false, managerOnly: false },
  { to: '/menu',         label: 'Menu',          icon: '🍽',  ownerOnly: false, managerOnly: true  },
  { to: '/alerts',       label: 'AI Alerts',     icon: '🔔', ownerOnly: false, managerOnly: true  },
  { to: '/reports',      label: 'Reports',       icon: '📊', ownerOnly: false, managerOnly: true  },
  { to: '/users',        label: 'Team',          icon: '◎',  ownerOnly: true,  managerOnly: false },
] as const

function AlertBadge({ count }: { count: number }) {
  if (count <= 0) return null
  return (
    <span
      style={{
        position: 'absolute',
        top: -4,
        right: -8,
        minWidth: 18,
        height: 18,
        padding: '0 5px',
        borderRadius: 9,
        background: '#dc2626',
        color: '#fff',
        fontSize: 11,
        fontWeight: 700,
        lineHeight: '18px',
        textAlign: 'center',
      }}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

export function AppShell() {
  const { user, logout } = useAuth()
  const { connected, on } = useSocket()
  const [alertCount, setAlertCount] = useState(0)

  const refreshAlertCount = useCallback(async () => {
    if (!user || !canManageMenu(user.role)) return
    try {
      const alerts = await aiApi.getAlerts(false)
      setAlertCount(alerts.length)
    } catch {
      /* ignore — badge stays at last count */
    }
  }, [user])

  useEffect(() => {
    refreshAlertCount()
  }, [refreshAlertCount])

  useEffect(() => {
    if (!user) return
    const unsub = on('ai_alert', (payload) => {
      const alert = payload as AIEvent
      if (alert.targetRole === user.role) {
        setAlertCount((c) => c + 1)
      }
    })
    return unsub
  }, [on, user])

  useEffect(() => {
    const onDismissed = () => setAlertCount((c) => Math.max(0, c - 1))
    window.addEventListener('foh:alert-dismissed', onDismissed)
    return () => window.removeEventListener('foh:alert-dismissed', onDismissed)
  }, [])

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark">FOH</span>
          <div>
            <strong>Host Stand</strong>
            <span className="brand-sub">Table management</span>
          </div>
        </div>

        <nav className="app-nav" aria-label="Main">
          {NAV.map((item) => {
            if (item.ownerOnly && (!user || !canManageUsers(user.role))) return null
            if (item.managerOnly && (!user || !canManageMenu(user.role))) return null
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <span
                  className="nav-item__icon"
                  aria-hidden
                  style={item.to === '/alerts' ? { position: 'relative' } : undefined}
                >
                  {item.icon}
                  {item.to === '/alerts' && <AlertBadge count={alertCount} />}
                </span>
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        {user && canEditFloor(user.role) && (
          <p className="sidebar-hint">Layout edit enabled</p>
        )}

        <div className="sidebar-footer">
          <span className={`socket-indicator ${connected ? 'socket-indicator--live' : ''}`}>
            <span className="socket-indicator__dot" />
            {connected ? 'Live sync' : 'Offline'}
          </span>
        </div>
      </aside>

      <div className="app-content">
        <nav className="mobile-nav" aria-label="Mobile">
          {NAV.map((item) => {
            if (item.ownerOnly && (!user || !canManageUsers(user.role))) return null
            if (item.managerOnly && (!user || !canManageMenu(user.role))) return null
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? 'active' : '')}
              >
                {item.label}
                {item.to === '/alerts' && alertCount > 0 ? ` (${alertCount})` : ''}
              </NavLink>
            )
          })}
        </nav>
        <header className="app-topbar">
          <div className="topbar-title">
            <h1>Main Dining</h1>
            <p className="muted">Tonight&apos;s service</p>
          </div>
          <div className="topbar-user">
            <span className={`role-badge role-${user?.role.toLowerCase()}`}>{user?.role}</span>
            <span className="user-name">{user?.name}</span>
            <button type="button" className="btn btn-ghost btn-sm" onClick={logout}>Sign out</button>
          </div>
        </header>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
