import type { KillTeam, MetaEntry, VoteSummary, CommunityNote, Match, User, MatchBody, TeamStat } from './types'

const BASE = '/api'

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('kt_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path, { headers: authHeaders() })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// ── Kill teams ────────────────────────────────────────────────────────────────
export const getKillTeams  = () => get<KillTeam[]>('/killteams')
export const getMeta       = () => get<MetaEntry[]>('/meta')

// ── Votes ─────────────────────────────────────────────────────────────────────
export const getVoteSummary = (team: string) =>
  get<VoteSummary>(`/votes/${encodeURIComponent(team)}`)

export const getMyVote = (team: string) =>
  get<{ score: number | null }>(`/votes/${encodeURIComponent(team)}/mine`)

export const castVote = (team_name: string, score: number) =>
  post<{ message: string; summary: VoteSummary }>('/votes', { team_name, score })

// ── Community notes ───────────────────────────────────────────────────────────
export const getNotes  = (team: string) =>
  get<CommunityNote[]>(`/notes/${encodeURIComponent(team)}`)

export const addNote   = (team_name: string, content: string) =>
  post<CommunityNote>('/notes', { team_name, content })

export const upvoteNote = (note_id: number) =>
  post<{ ok: boolean }>(`/notes/${note_id}/upvote`, {})

// ── Auth ──────────────────────────────────────────────────────────────────────
export const apiRegister = (username: string, password: string) =>
  post<{ token: string; user: User }>('/auth/register', { username, password })

export const apiLogin = (username: string, password: string) =>
  post<{ token: string; user: User }>('/auth/login', { username, password })

export const getMe = () => get<User>('/auth/me')

// ── Matches ───────────────────────────────────────────────────────────────────
export const logMatch   = (body: MatchBody)  => post<User>('/matches', body)
export const getMatches = ()                  => get<Match[]>('/matches')
export const getMatchStats = ()               => get<{ team_stats: TeamStat[]; performance: unknown }>('/matches/stats')
export const getLeaderboard = ()              => get<unknown[]>('/leaderboard')

export const getFactionLeaderboard = () => get<unknown[]>('/leaderboard/factions')
