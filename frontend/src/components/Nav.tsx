import { NavLink } from 'react-router-dom'
import { useAuth } from '../lib/useAuth'
import { BarChart2, Target, BookOpen, User } from 'lucide-react'

const links = [
  { to: '/',         label: 'Meta',       icon: BarChart2  },
  { to: '/radar',    label: 'Teams',      icon: Target     },
  { to: '/record',   label: 'My Record',  icon: BookOpen   },
  { to: '/account',  label: 'Account',    icon: User       },
]

export default function Nav() {
  const { user } = useAuth()
  return (
    <nav style={{
      background: '#161b27', borderBottom: '1px solid #2d3748',
      padding: '0 24px', display: 'flex', alignItems: 'center', gap: 8,
      position: 'sticky', top: 0, zIndex: 100,
    }}>
      <span style={{ fontWeight: 800, fontSize: 18, color: '#3b82f6', marginRight: 16, padding: '14px 0' }}>
        Dataslate
      </span>
      {links.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === '/'} style={({ isActive }) => ({
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '14px 12px', fontSize: 14, fontWeight: 500,
          color: isActive ? '#3b82f6' : '#94a3b8',
          borderBottom: isActive ? '2px solid #3b82f6' : '2px solid transparent',
          textDecoration: 'none', transition: 'color 0.15s',
        })}>
          <Icon size={15} />
          {label}
        </NavLink>
      ))}
      {user && (
        <span style={{ marginLeft: 'auto', fontSize: 13, color: '#64748b' }}>
          {user.username} · {user.elo.toFixed(0)} ELO
        </span>
      )}
    </nav>
  )
}
