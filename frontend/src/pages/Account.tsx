import { useState } from 'react'
import { useAuth } from '../lib/useAuth'
import { useNavigate } from 'react-router-dom'

export default function Account() {
  const { user, login, register, logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab]           = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)

  if (user) return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px' }}>
      <div style={{ background: '#161b27', border: '1px solid #2d3748', borderRadius: 16, padding: 32, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>👤</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{user.username}</h2>
        <p style={{ color: '#64748b', fontSize: 13, marginBottom: 24 }}>
          {user.wins}W · {user.draws}D · {user.losses}L · {user.player_elo.toFixed(0)} ELO
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => { navigate('/record') }} style={{ ...btnStyle, flex: 1, background: '#3b82f6' }}>
            My Record
          </button>
          <button onClick={logout} style={{ ...btnStyle, flex: 1, background: '#374151' }}>
            Logout
          </button>
        </div>
      </div>
    </div>
  )

  const handleSubmit = async () => {
    setError('')
    if (!username.trim() || !password.trim()) { setError('Fill in all fields.'); return }
    if (tab === 'register' && password !== confirm) { setError("Passwords don't match."); return }
    if (tab === 'register' && password.length < 6)  { setError('Password must be 6+ characters.'); return }
    setLoading(true)
    try {
      if (tab === 'login') await login(username, password)
      else                 await register(username, password)
      navigate('/record')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px' }}>
      <div style={{ background: '#161b27', border: '1px solid #2d3748', borderRadius: 16, padding: 32 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24, textAlign: 'center' }}>Killrate</h1>

        <div style={{ display: 'flex', marginBottom: 24, borderBottom: '1px solid #2d3748' }}>
          {(['login', 'register'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setError('') }} style={{
              flex: 1, padding: '8px 0', background: 'none', border: 'none',
              borderBottom: tab === t ? '2px solid #3b82f6' : '2px solid transparent',
              color: tab === t ? '#3b82f6' : '#64748b',
              cursor: 'pointer', fontSize: 13, fontWeight: 600, textTransform: 'capitalize',
            }}>{t}</button>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)}
            style={inputStyle} onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)}
            style={inputStyle} onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          {tab === 'register' && (
            <input placeholder="Confirm password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
              style={inputStyle} onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          )}
          {error && <p style={{ color: '#ef4444', fontSize: 13 }}>{error}</p>}
          <button onClick={handleSubmit} disabled={loading} style={{ ...btnStyle, background: '#3b82f6', opacity: loading ? 0.7 : 1 }}>
            {loading ? '...' : tab === 'login' ? 'Login' : 'Create Account'}
          </button>
        </div>

        {tab === 'login' && (
          <p style={{ color: '#475569', fontSize: 12, textAlign: 'center', marginTop: 16 }}>
            No account? <button onClick={() => setTab('register')} style={{ background: 'none', border: 'none', color: '#3b82f6', cursor: 'pointer', fontSize: 12 }}>Register</button>
          </p>
        )}
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8,
  padding: '10px 14px', color: '#e2e8f0', fontSize: 14, outline: 'none', width: '100%',
}
const btnStyle: React.CSSProperties = {
  padding: '10px 0', border: 'none', borderRadius: 8,
  color: 'white', fontWeight: 700, fontSize: 14, cursor: 'pointer',
}
