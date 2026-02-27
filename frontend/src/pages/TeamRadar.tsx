import { useEffect, useState } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { getKillTeams, getVoteSummary, getMyVote, castVote, getNotes, addNote, upvoteNote } from '../lib/api'
import type { KillTeam, VoteSummary, CommunityNote } from '../lib/types'
import { useAuth } from '../lib/useAuth'
import { ThumbsUp, Send } from 'lucide-react'

// Radar axes for each team are derived from meta characteristics
function buildRadarData(team: KillTeam) {
  const playMap: Record<string, Record<string, number>> = {
    Ranged:   { Ranged: 9, Melee: 2, Assault: 4, Mobility: 5, Durability: 5, Tricksy: 3 },
    Melee:    { Ranged: 2, Melee: 9, Assault: 6, Mobility: 6, Durability: 5, Tricksy: 3 },
    Assault:  { Ranged: 4, Melee: 6, Assault: 9, Mobility: 7, Durability: 5, Tricksy: 3 },
    Mixed:    { Ranged: 6, Melee: 6, Assault: 5, Mobility: 5, Durability: 5, Tricksy: 4 },
    Variable: { Ranged: 6, Melee: 6, Assault: 5, Mobility: 5, Durability: 5, Tricksy: 6 },
  }
  const sizeMap: Record<string, number> = {
    Horde: 7, Midrange: 5, Elite: 6, 'Hyper-elite': 8, Mixed: 5,
  }
  const tricksyMap: Record<string, number> = { Low: 2, Mod: 5, High: 9 }

  const base = playMap[team.play ?? 'Mixed'] ?? playMap['Mixed']
  const durability = sizeMap[team.size ?? 'Mixed'] ?? 5
  const tricksy = tricksyMap[team.tricksy ?? ''] ?? base.Tricksy

  return [
    { axis: 'Ranged',     value: base.Ranged },
    { axis: 'Melee',      value: base.Melee },
    { axis: 'Assault',    value: base.Assault },
    { axis: 'Mobility',   value: base.Mobility },
    { axis: 'Durability', value: durability },
    { axis: 'Tricksy',    value: tricksy },
  ]
}

export default function TeamRadar() {
  const { user } = useAuth()
  const [teams, setTeams]           = useState<KillTeam[]>([])
  const [selected, setSelected]     = useState<KillTeam | null>(null)
  const [search, setSearch]         = useState('')
  const [votes, setVotes]           = useState<VoteSummary | null>(null)
  const [myVote, setMyVote]         = useState<number | null>(null)
  const [voteVal, setVoteVal]       = useState(5)
  const [notes, setNotes]           = useState<CommunityNote[]>([])
  const [noteText, setNoteText]     = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { getKillTeams().then(setTeams) }, [])

  const selectTeam = async (team: KillTeam) => {
    setSelected(team)
    setNoteText('')
    const [v, n] = await Promise.all([getVoteSummary(team.name), getNotes(team.name)])
    setVotes(v)
    setNotes(n)
    if (user) {
      const mv = await getMyVote(team.name)
      setMyVote(mv.score)
      setVoteVal(mv.score ?? 5)
    }
  }

  const handleVote = async () => {
    if (!selected) return
    setSubmitting(true)
    try {
      const res = await castVote(selected.name, voteVal)
      setVotes(res.summary)
      setMyVote(voteVal)
    } finally { setSubmitting(false) }
  }

  const handleNote = async () => {
    if (!selected || !noteText.trim()) return
    setSubmitting(true)
    try {
      const note = await addNote(selected.name, noteText)
      setNotes(prev => [note, ...prev])
      setNoteText('')
    } finally { setSubmitting(false) }
  }

  const handleUpvote = async (note_id: number) => {
    await upvoteNote(note_id)
    setNotes(prev => prev.map(n => n.id === note_id ? { ...n, upvotes: n.upvotes + 1 } : n))
  }

  const filtered = teams.filter(t => t.name.toLowerCase().includes(search.toLowerCase()))
  const radarData = selected ? buildRadarData(selected) : []

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 49px)', overflow: 'hidden' }}>
      {/* Sidebar — team list */}
      <div style={{
        width: 240, background: '#161b27', borderRight: '1px solid #2d3748',
        display: 'flex', flexDirection: 'column', flexShrink: 0,
      }}>
        <div style={{ padding: 12 }}>
          <input
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {filtered.map(team => (
            <button key={team.name} onClick={() => selectTeam(team)} style={{
              width: '100%', textAlign: 'left', padding: '10px 16px',
              background: selected?.name === team.name ? '#1e3a5f' : 'transparent',
              border: 'none', borderLeft: selected?.name === team.name ? '3px solid #3b82f6' : '3px solid transparent',
              color: selected?.name === team.name ? '#e2e8f0' : '#94a3b8',
              cursor: 'pointer', fontSize: 13, fontWeight: selected?.name === team.name ? 600 : 400,
            }}>
              {team.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
        {!selected ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
            Select a kill team to view its profile
          </div>
        ) : (
          <div style={{ maxWidth: 900, margin: '0 auto' }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{selected.name}</h1>
            <div style={{ display: 'flex', gap: 6, marginBottom: 24, flexWrap: 'wrap' }}>
              {selected.cyrac_rank && <Chip label={`CYRAC #${selected.cyrac_rank} (${selected.cyrac_tier})`} color="#f59e0b" />}
              {selected.size && <Chip label={selected.size} color="#22c55e" />}
              {selected.play && <Chip label={selected.play} color="#3b82f6" />}
              {selected.tricksy && <Chip label={`${selected.tricksy} Tricksy`} color="#8b5cf6" />}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              {/* Radar */}
              <Card title="Team Profile">
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#2d3748" />
                    <PolarAngleAxis dataKey="axis" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                    <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
                    <Tooltip
                      contentStyle={{ background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>

              {/* Voting */}
              <Card title="Community Rating">
                {votes && votes.vote_count > 0 ? (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 36, fontWeight: 800, color: '#3b82f6', marginBottom: 4 }}>
                      {votes.avg_score.toFixed(1)}<span style={{ fontSize: 16, color: '#64748b' }}>/10</span>
                    </div>
                    <div style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>{votes.vote_count} votes</div>
                    {/* Distribution bars */}
                    <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', height: 48 }}>
                      {[1,2,3,4,5,6,7,8,9,10].map(n => {
                        const count = votes.distribution[n] ?? 0
                        const max   = Math.max(...Object.values(votes.distribution), 1)
                        return (
                          <div key={n} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div style={{
                              width: '100%', background: '#3b82f6',
                              height: `${(count / max) * 40}px`, borderRadius: '3px 3px 0 0',
                              minHeight: count > 0 ? 3 : 0,
                            }} />
                            <div style={{ fontSize: 9, color: '#475569', marginTop: 2 }}>{n}</div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ) : (
                  <p style={{ color: '#475569', fontSize: 13, marginBottom: 16 }}>No votes yet — be the first.</p>
                )}

                {user ? (
                  <div>
                    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>
                      {myVote ? `Your vote: ${myVote}/10` : 'Your vote'}
                    </div>
                    <input
                      type="range" min={1} max={10} value={voteVal}
                      onChange={e => setVoteVal(Number(e.target.value))}
                      style={{ width: '100%', marginBottom: 8 }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#475569', marginBottom: 12 }}>
                      <span>1 — Weak</span>
                      <span style={{ fontWeight: 700, color: '#3b82f6', fontSize: 16 }}>{voteVal}</span>
                      <span>10 — Broken</span>
                    </div>
                    <Btn onClick={handleVote} disabled={submitting}>
                      {myVote ? 'Update Vote' : 'Submit Vote'}
                    </Btn>
                  </div>
                ) : (
                  <p style={{ fontSize: 12, color: '#475569' }}>Login to vote</p>
                )}
              </Card>
            </div>

            {/* Community notes */}
            <Card title="Community Notes & Combos" style={{ marginTop: 24 }}>
              {user && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <input
                    placeholder="Share an operative combo, tip, or matchup note..."
                    value={noteText}
                    onChange={e => setNoteText(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleNote()}
                    style={{ ...inputStyle, flex: 1 }}
                  />
                  <button onClick={handleNote} disabled={submitting || !noteText.trim()} style={{
                    background: '#3b82f6', border: 'none', borderRadius: 8,
                    padding: '6px 12px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center',
                  }}>
                    <Send size={14} />
                  </button>
                </div>
              )}
              {notes.length === 0 ? (
                <p style={{ color: '#475569', fontSize: 13 }}>No notes yet. {user ? 'Add the first one!' : 'Login to contribute.'}</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {notes.map(note => (
                    <div key={note.id} style={{
                      background: '#161b27', border: '1px solid #2d3748',
                      borderRadius: 8, padding: 12,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: '#3b82f6' }}>{note.username}</span>
                        <button onClick={() => handleUpvote(note.id)} style={{
                          display: 'flex', alignItems: 'center', gap: 4,
                          background: 'none', border: 'none', color: '#64748b',
                          cursor: 'pointer', fontSize: 12,
                        }}>
                          <ThumbsUp size={12} /> {note.upvotes}
                        </button>
                      </div>
                      <p style={{ fontSize: 13, color: '#e2e8f0', lineHeight: 1.5 }}>{note.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: '#161b27', border: '1px solid #2d3748', borderRadius: 12, padding: 20, ...style }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</h3>
      {children}
    </div>
  )
}

function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      padding: '3px 10px', borderRadius: 10, fontSize: 12, fontWeight: 600,
      background: color + '22', color, border: `1px solid ${color}44`,
    }}>{label}</span>
  )
}

function Btn({ children, onClick, disabled }: { children: React.ReactNode; onClick: () => void; disabled?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      width: '100%', padding: '8px 0', background: disabled ? '#2d3748' : '#3b82f6',
      border: 'none', borderRadius: 8, color: 'white', fontWeight: 600,
      fontSize: 13, cursor: disabled ? 'not-allowed' : 'pointer',
    }}>{children}</button>
  )
}

const inputStyle: React.CSSProperties = {
  background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8,
  padding: '7px 12px', color: '#e2e8f0', fontSize: 13,
}
