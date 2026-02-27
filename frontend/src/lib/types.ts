export interface KillTeam {
  name: string
  faction: string
  cyrac_rank: number | null
  cyrac_tier: string
  size: string | null
  play: string | null
  tricksy: string | null
}

export interface MetaEntry extends KillTeam {
  faction_elo: number
  faction_games: number
  faction_elo_provisional: boolean
  community_score: number | null
  vote_count: number
}

export interface VoteSummary {
  avg_score: number
  vote_count: number
  min_score: number
  max_score: number
  distribution: Record<number, number>
}

export interface CommunityNote {
  id: number
  user_id: number
  username: string
  team_name: string
  content: string
  upvotes: number
  created_at: string
}

export interface Match {
  id: number
  my_team: string
  opponent_team: string
  my_score: number
  opponent_score: number
  outcome: 'W' | 'D' | 'L'
  elo_before: number
  elo_after: number
  elo_change: number
  opponent_name: string | null
  notes: string | null
  played_at: string
  ops_lost: number | null
  ops_killed: number | null
  tac_ops_score: number | null
  crit_ops_score: number | null
  kill_ops_score: number | null
  opp_tac_ops_score: number | null
  opp_crit_ops_score: number | null
  opp_kill_ops_score: number | null
}

export interface User {
  id: number
  username: string
  player_elo: number
  wins: number
  draws: number
  losses: number
  created_at: string
  provisional: boolean
  provisional_games_needed: number
}

export interface TeamStat {
  my_team: string
  matches: number
  wins: number
  draws: number
  losses: number
  avg_elo_change: number
}

export interface MatchBody {
  my_team: string
  opponent_team: string
  my_score: number
  opponent_score: number
  outcome: 'W' | 'D' | 'L'
  opponent_name?: string
  notes?: string
  ops_lost?: number
  ops_killed?: number
  tac_ops_score?: number
  crit_ops_score?: number
  kill_ops_score?: number
  opp_tac_ops_score?: number
  opp_crit_ops_score?: number
  opp_kill_ops_score?: number
}
