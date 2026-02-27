import { useEffect, useState } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { logMatch, getMatches, getMatchStats } from '../lib/api'
import type { Match, MatchBody, TeamStat } from '../lib/types'
import { useAuth } from '../lib/useAuth'

const MATCHUP_TIPS: Record<string, string[]> = {
  Ranged:   ['Use cover aggressively to close distance', 'Prioritise their observers and spotters early', 'Dash flanking operatives turn 1 to threaten their backline'],
  Melee:    ['Maintain range — shoot before they engage', 'Use fall back actions to kite', 'Crit op objectives often win you the game before they reach you'],
  Assault:  ['Contest the midfield or concede board control', 'Focus fire to reduce their activation advantage', 'Watch for ploy-driven charges out of cover'],
  Mixed:    ['Identify their key operative and remove it first', 'Play the objectives — mixed teams often outscore in Tac Ops', 'Don\'t overcommit to a single flank'],
  Variable: ['Assume worst-case loadout until you see their list', 'Variable teams often peak turn 2-3, play for the long game', 'Control the engagement range — they thrive in flexibility'],
}

function getTipsForPlay(play: string | undefined) {
  return MATCHUP_TIPS[play ?? 'Mixed'] ?? MATCHUP_TIPS['Mixed']
}

export default function MyRecord() {
  const { user } = useAuth()
  const [matches, setMatches]     = useState<Match[]>([])
  const [teamStats, setTeamStats] = useState<TeamStat[]>([])
  const [loading, setLoading]     = useState(true)
  const [tab, setTab]             = useState<'log' | 'history' | 'charts'>('log')

  // Form state
  const [teams, setTeams]         = useState<string[]>([])
  const [form, setForm]           = useState<MatchBody>({
    my_team: '', opponent_team: '', my_score: 0, opponent_score: 0, outcome: 'W',
  })
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess]       = useState('')

  useEffect(() => {
    import('../lib/api').then(({ getKillTeams }) => getKillTeams().then(d => setTeams(d.map(t => t.name))))
    if (user) {
      Promise.all([getMatches(), getMatchStats()]).then(([m, s]) => {
        setMatches(m)
        setTeamStats(s.team_stats)
      }).finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [user])

  const handleSubmit = async () => {
    if (!form.my_team || !form.opponent_team) return
    setSubmitting(true)
    try {
      await logMatch(form)
      const [m, s] = await Promise.all([getMatches(), getMatchStats()])
      setMatches(m)
      setTeamStats(s.team_stats)
      setSuccess('Match logged!')
      setTimeout(() => setSuccess(''), 3000)
      setForm({ my_team: form.my_team, opponent_team: '', my_score: 0, opponent_score: 0, outcome: 'W' })
    } finally { setSubmitting(false) }
  }

  if (!user) return <AuthGate />

  // ELO timeline data
  const eloData = matches.slice().reverse().map((m, i) => ({
    game: i + 1,
    elo: m.elo_after,
    outcome: m.outcome,
  }))

  // Score differential
  const diffData = matches.slice(0, 20).reverse().map((m, i) => ({
    game: i + 1,
    diff: m.my_score - m.opponent_score,
    outcome: m.outcome,
  }))

  const totalGames = user.wins + user.draws + user.losses
  const winRate    = totalGames ? ((user.wins / totalGames) * 100).toFixed(0) : '0'

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>{user.username}'s Record</h1>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 2 }}>
            {user.wins}W · {user.draws}D · {user.losses}L · {winRate}% Win Rate
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: '#3b82f6' }}>{user.player_elo.toFixed(0)}</div>
          <div style={{ fontSize: 12, color: '#64748b' }}>ELO Rating</div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #2d3748' }}>
        {(['log', 'history', 'charts'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 16px', background: 'none', border: 'none',
            borderBottom: tab === t ? '2px solid #3b82f6' : '2px solid transparent',
            color: tab === t ? '#3b82f6' : '#64748b',
            cursor: 'pointer', fontSize: 13, fontWeight: tab === t ? 600 : 400, textTransform: 'capitalize',
          }}>{t === 'log' ? 'Log Match' : t === 'history' ? 'History' : 'Charts'}</button>
        ))}
      </div>

      {/* Log a match */}
      {tab === 'log' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <Section title="Match Result">
              <Label>Your Kill Team</Label>
              <Select value={form.my_team} onChange={v => setForm(f => ({ ...f, my_team: v }))} options={teams} />
              <Label>Opponent Kill Team</Label>
              <Select value={form.opponent_team} onChange={v => setForm(f => ({ ...f, opponent_team: v }))} options={teams} />
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <Label>Your Score</Label>
                  <NumInput value={form.my_score} onChange={v => setForm(f => ({ ...f, my_score: v }))} />
                </div>
                <div style={{ flex: 1 }}>
                  <Label>Opp Score</Label>
                  <NumInput value={form.opponent_score} onChange={v => setForm(f => ({ ...f, opponent_score: v }))} />
                </div>
              </div>
              <Label>Outcome</Label>
              <div style={{ display: 'flex', gap: 8 }}>
                {(['W', 'D', 'L'] as const).map(o => (
                  <button key={o} onClick={() => setForm(f => ({ ...f, outcome: o }))} style={{
                    flex: 1, padding: '8px 0', borderRadius: 8, border: 'none',
                    fontWeight: 700, fontSize: 14, cursor: 'pointer',
                    background: form.outcome === o
                      ? (o === 'W' ? '#22c55e' : o === 'D' ? '#f59e0b' : '#ef4444')
                      : '#1e2130',
                    color: form.outcome === o ? 'white' : '#64748b',
                  }}>{o === 'W' ? 'Win' : o === 'D' ? 'Draw' : 'Loss'}</button>
                ))}
              </div>
              <Label>Opponent Username (optional)</Label>
              <input style={{ ...inputStyle, width: '100%' }} placeholder="For ELO matching..."
                value={form.opponent_name ?? ''} onChange={e => setForm(f => ({ ...f, opponent_name: e.target.value }))} />
            </Section>
          </div>

          <div>
            <Section title="Objective Breakdown (optional)">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  ['Your Tac Ops', 'tac_ops_score'], ['Opp Tac Ops', 'opp_tac_ops_score'],
                  ['Your Crit Ops', 'crit_ops_score'], ['Opp Crit Ops', 'opp_crit_ops_score'],
                  ['Your Kill Ops', 'kill_ops_score'], ['Opp Kill Ops', 'opp_kill_ops_score'],
                  ['Ops Lost', 'ops_lost'], ['Ops Killed', 'ops_killed'],
                ].map(([label, key]) => (
                  <div key={key}>
                    <Label>{label}</Label>
                    <NumInput
                      value={(form as Record<string, number | undefined>)[key] ?? 0}
                      onChange={v => setForm(f => ({ ...f, [key]: v }))}
                    />
                  </div>
                ))}
              </div>
              <Label>Notes</Label>
              <textarea style={{ ...inputStyle, width: '100%', height: 80, resize: 'vertical' }}
                placeholder="Mission, key moments..."
                value={form.notes ?? ''}
                onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              />
            </Section>

            {/* Matchup tips */}
            {form.opponent_team && (() => {
              // We'd ideally look up the opponent team's play style from loaded teams
              const tips = getTipsForPlay(undefined)
              return (
                <Section title={`Tips vs ${form.opponent_team}`} style={{ marginTop: 16 }}>
                  <ul style={{ paddingLeft: 16 }}>
                    {tips.map((tip, i) => (
                      <li key={i} style={{ fontSize: 13, color: '#94a3b8', marginBottom: 6, lineHeight: 1.5 }}>{tip}</li>
                    ))}
                  </ul>
                </Section>
              )
            })()}

            <button onClick={handleSubmit} disabled={submitting || !form.my_team || !form.opponent_team}
              style={{
                marginTop: 16, width: '100%', padding: '10px 0',
                background: '#3b82f6', border: 'none', borderRadius: 8,
                color: 'white', fontWeight: 700, fontSize: 14,
                cursor: submitting ? 'not-allowed' : 'pointer',
                opacity: submitting ? 0.7 : 1,
              }}>
              {submitting ? 'Logging...' : 'Log Match'}
            </button>
            {success && <p style={{ color: '#22c55e', textAlign: 'center', marginTop: 8, fontSize: 13 }}>{success}</p>}
          </div>
        </div>
      )}

      {/* History */}
      {tab === 'history' && (
        loading ? <Spinner /> : matches.length === 0 ? (
          <p style={{ color: '#64748b', textAlign: 'center', paddingTop: 40 }}>No matches logged yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {matches.map(m => (
              <div key={m.id} style={{
                background: '#161b27', border: '1px solid #2d3748', borderRadius: 10,
                padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 16,
                borderLeft: `3px solid ${m.outcome === 'W' ? '#22c55e' : m.outcome === 'D' ? '#f59e0b' : '#ef4444'}`,
              }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: m.outcome === 'W' ? '#22c55e' : m.outcome === 'D' ? '#f59e0b' : '#ef4444', width: 28 }}>
                  {m.outcome}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{m.my_team} vs {m.opponent_team}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>
                    {m.my_score} – {m.opponent_score} · {new Date(m.played_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: m.elo_change >= 0 ? '#22c55e' : '#ef4444' }}>
                    {m.elo_change >= 0 ? '+' : ''}{m.elo_change.toFixed(1)}
                  </div>
                  <div style={{ fontSize: 11, color: '#475569' }}>ELO</div>
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* Charts */}
      {tab === 'charts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {eloData.length > 1 && (
            <Section title="ELO Over Time">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={eloData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                  <XAxis dataKey="game" stroke="#475569" tick={{ fontSize: 11 }} label={{ value: 'Game', position: 'insideBottom', fill: '#475569', fontSize: 11 }} />
                  <YAxis stroke="#475569" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="elo" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          )}

          {diffData.length > 0 && (
            <Section title="Score Differential (Last 20 Games)">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={diffData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                  <XAxis dataKey="game" stroke="#475569" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8 }} />
                  <Bar dataKey="diff" name="Score Diff" fill="#3b82f6"
                    label={false}
                    // Colour bars by outcome
                    isAnimationActive={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {teamStats.length > 0 && (
            <Section title="Performance by Kill Team">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={teamStats}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                  <XAxis dataKey="my_team" stroke="#475569" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
                  <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8 }} />
                  <Legend />
                  <Bar dataKey="wins"   name="Wins"   fill="#22c55e" stackId="a" />
                  <Bar dataKey="draws"  name="Draws"  fill="#f59e0b" stackId="a" />
                  <Bar dataKey="losses" name="Losses" fill="#ef4444" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}
        </div>
      )}
    </div>
  )
}

function Section({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: '#161b27', border: '1px solid #2d3748', borderRadius: 12, padding: 16, ...style }}>
      <h3 style={{ fontSize: 12, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4, marginTop: 10 }}>{children}</div>
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)} style={{ ...inputStyle, width: '100%' }}>
      <option value="">Select...</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

function NumInput({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <input type="number" min={0} max={99} value={value}
      onChange={e => onChange(Number(e.target.value))}
      style={{ ...inputStyle, width: '100%' }} />
  )
}

function AuthGate() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 100px)', flexDirection: 'column', gap: 12 }}>
      <p style={{ color: '#64748b' }}>Login to view your record</p>
      <a href="/account" style={{ color: '#3b82f6', fontSize: 14 }}>Go to Account →</a>
    </div>
  )
}

function Spinner() {
  return <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Loading...</div>
}

const inputStyle: React.CSSProperties = {
  background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8,
  padding: '7px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none',
}
