import { useEffect, useState, useMemo } from 'react'
import { getMeta } from '../lib/api'
import type { MetaEntry } from '../lib/types'

const TIER_COLORS: Record<string, string> = {
  S: '#f59e0b', A: '#22c55e', B: '#3b82f6', C: '#8b5cf6', D: '#6b7280', Unranked: '#374151',
}
const SIZE_COLORS: Record<string, string> = {
  Horde: '#22c55e', Midrange: '#3b82f6', Elite: '#f59e0b', 'Hyper-elite': '#ef4444', Mixed: '#8b5cf6',
}
const PLAY_COLORS: Record<string, string> = {
  Ranged: '#3b82f6', Melee: '#ef4444', Assault: '#f59e0b', Mixed: '#8b5cf6', Variable: '#6b7280',
}
const TRICKSY_COLORS: Record<string, string> = { Low: '#22c55e', Mod: '#f59e0b', High: '#ef4444' }

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 10,
      fontSize: 11, fontWeight: 600,
      background: color + '22', color, border: `1px solid ${color}44`,
    }}>{label}</span>
  )
}

function MultiFilter({ label, options, value, onChange }: {
  label: string; options: string[]; value: string[]; onChange: (v: string[]) => void
}) {
  const toggle = (opt: string) =>
    onChange(value.includes(opt) ? value.filter(v => v !== opt) : [...value, opt])
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
      <span style={{ fontSize: 12, color: '#64748b' }}>{label}:</span>
      {options.map(opt => (
        <button key={opt} onClick={() => toggle(opt)} style={{
          padding: '3px 8px', borderRadius: 8, fontSize: 11, cursor: 'pointer',
          border: '1px solid #2d3748',
          background: value.includes(opt) ? '#3b82f6' : 'transparent',
          color: value.includes(opt) ? 'white' : '#94a3b8',
        }}>{opt}</button>
      ))}
    </div>
  )
}

function Spinner() {
  return <div style={{ display: 'flex', justifyContent: 'center', padding: 60, color: '#64748b' }}>Loading...</div>
}

function scoreColor(v: number | null) {
  if (!v) return '#64748b'
  if (v >= 7) return '#22c55e'
  if (v >= 4) return '#f59e0b'
  return '#ef4444'
}

const inputStyle: React.CSSProperties = {
  background: '#1e2130', border: '1px solid #2d3748', borderRadius: 8,
  padding: '6px 12px', color: '#e2e8f0', fontSize: 13,
}

type SortKey = 'ppo_rank' | 'ppo_winrate' | 'ppo_games' | 'faction_elo' | 'cyrac_rank'

export default function Meta() {
  const [data, setData]               = useState<MetaEntry[]>([])
  const [loading, setLoading]         = useState(true)
  const [sortBy, setSortBy]           = useState<SortKey>('ppo_rank')
  const [filterSize, setFilterSize]   = useState<string[]>([])
  const [filterPlay, setFilterPlay]   = useState<string[]>([])
  const [search, setSearch]           = useState('')

  useEffect(() => {
    getMeta().then(setData).finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    let d = [...data]
    if (search)            d = d.filter(r => r.name.toLowerCase().includes(search.toLowerCase()))
    if (filterSize.length) d = d.filter(r => r.size && filterSize.includes(r.size))
    if (filterPlay.length) d = d.filter(r => r.play && filterPlay.includes(r.play))
    d.sort((a, b) => {
      if (sortBy === 'ppo_rank')    return (a.ppo_rank ?? 999) - (b.ppo_rank ?? 999)
      if (sortBy === 'ppo_winrate') return (b.ppo_winrate ?? 0) - (a.ppo_winrate ?? 0)
      if (sortBy === 'ppo_games')   return (b.ppo_games ?? 0) - (a.ppo_games ?? 0)
      if (sortBy === 'faction_elo') return ((b as MetaEntry).faction_elo ?? 0) - ((a as MetaEntry).faction_elo ?? 0)
      if (sortBy === 'cyrac_rank')  return (a.cyrac_rank ?? 999) - (b.cyrac_rank ?? 999)
      return a.name.localeCompare(b.name)
    })
    return d
  }, [data, sortBy, filterSize, filterPlay, search])

  if (loading) return <Spinner />

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Meta Rankings</h1>
      <p style={{ color: '#64748b', marginBottom: 24, fontSize: 14 }}>
        CYRAC expert tier list · Community votes · Team characteristics
      </p>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <input placeholder="Search team..." value={search} onChange={e => setSearch(e.target.value)} style={inputStyle} />
        <select value={sortBy} onChange={e => setSortBy(e.target.value as SortKey)} style={inputStyle}>
          <option value="ppo_rank">Sort: PPO Tier</option>
          <option value="ppo_winrate">Sort: Win Rate</option>
          <option value="ppo_games">Sort: Games Played</option>
          <option value="faction_elo">Sort: Faction ELO</option>
          <option value="cyrac_rank">Sort: CYRAC Rank</option>
        </select>
        <MultiFilter label="Size" options={['Horde','Midrange','Elite','Hyper-elite','Mixed']} value={filterSize} onChange={setFilterSize} />
        <MultiFilter label="Play" options={['Ranged','Melee','Assault','Mixed','Variable']} value={filterPlay} onChange={setFilterPlay} />
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #2d3748', color: '#64748b' }}>
              {['#','Kill Team','PPO Tier','PPO Win%','Faction ELO','PPO Games','PPO Placing%','CYRAC','Community','Votes','Size','Play Style','Tricksy'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
     <tbody>
            {filtered.map((row, i) => (
              <tr key={row.name} style={{ borderBottom: '1px solid #1e2130', background: i % 2 === 0 ? 'transparent' : '#ffffff04' }}>
                <td style={{ padding: '10px 12px', color: '#475569' }}>{i + 1}</td>
                <td style={{ padding: '10px 12px', fontWeight: 600 }}>{row.name}</td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  {row.ppo_tier ? <Badge label={`#${row.ppo_rank} ${row.ppo_tier}`} color={TIER_COLORS[row.ppo_tier] ?? '#888'} /> : <span style={{ color: '#666' }}>—</span>}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  {row.ppo_winrate != null
                    ? <span style={{ fontWeight: 700, color: row.ppo_winrate >= 55 ? '#4ade80' : row.ppo_winrate >= 45 ? '#facc15' : '#f87171' }}>{row.ppo_winrate}%</span>
                    : <span style={{ color: '#666' }}>—</span>}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{ fontWeight: 700, color: '#f59e0b' }}>{(row as MetaEntry).faction_elo?.toFixed(0) ?? '—'}</span>
                  {(row as MetaEntry).faction_elo_provisional && <span style={{ fontSize: 10, color: '#475569', marginLeft: 4 }}>P</span>}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center', color: '#64748b', fontSize: 12 }}>
                  {row.ppo_games != null && row.ppo_picks != null ? `${row.ppo_picks}p / ${row.ppo_games}g` : '—'}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  {row.ppo_placing_rate != null ? <span style={{ fontWeight: 600, color: '#94a3b8' }}>{row.ppo_placing_rate}%</span> : <span style={{ color: '#666' }}>—</span>}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  {row.cyrac_rank ? <Badge label={`#${row.cyrac_rank} ${row.cyrac_tier}`} color={TIER_COLORS[row.cyrac_tier] ?? '#888'} /> : '—'}
                </td>
                <td style={{ padding: '10px 12px', fontWeight: 700, color: scoreColor(row.community_score) }}>
                  {row.community_score ? row.community_score.toFixed(1) : '—'}
                </td>
                <td style={{ padding: '10px 12px', color: '#64748b' }}>{row.vote_count}</td>
                <td style={{ padding: '10px 12px' }}>{row.size && <Badge label={row.size} color={SIZE_COLORS[row.size] ?? '#888'} />}</td>
                <td style={{ padding: '10px 12px' }}>{row.play && <Badge label={row.play} color={PLAY_COLORS[row.play] ?? '#888'} />}</td>
                <td style={{ padding: '10px 12px' }}>{row.tricksy && <Badge label={row.tricksy} color={TRICKSY_COLORS[row.tricksy] ?? '#888'} />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Acknowledgements */}
      <div style={{ marginTop: 48, borderTop: '1px solid #1e2130', paddingTop: 24 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Acknowledgements</h3>
        <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.8 }}>
          📊 Tournament win rate data provided by{' '}
          <a href="https://www.pretentiousplasticops.com" target="_blank" rel="noopener noreferrer" style={{ color: '#94a3b8', textDecoration: 'underline' }}>
            Pretentious Plastic Ops
          </a>
          {' '}— sourced from Best Coast Pairings & Tabletop Herald.
        </p>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 6, lineHeight: 1.8 }}>
          🎖️ Expert tier rankings provided by{' '}
          <a href="https://www.canyourollacrit.com" target="_blank" rel="noopener noreferrer" style={{ color: '#94a3b8', textDecoration: 'underline' }}>
            Can You Roll a Crit
          </a>
          {' '}(CYRAC).
        </p>
        <p style={{ fontSize: 13, color: '#64748b', marginTop: 6, lineHeight: 1.8 }}>
          🙏 Special thanks to <strong style={{ color: '#94a3b8' }}>Parth K</strong> for their support and contributions to this project.
        </p>
      </div>
    </div>
  )
}
