"""
main.py — FastAPI backend for KT Selector
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import json, os, jwt, datetime

from api import fetch_all_killteams
from database import (
    init_db, register, login, get_user, log_match,
    get_match_history, get_leaderboard, get_team_stats,
    get_performance_stats, cast_vote, get_user_vote,
    get_team_vote_summary, get_all_vote_summaries, can_vote,
    add_community_note, get_community_notes, upvote_note,
)
from elo import faction_baseline, is_provisional, PROVISIONAL_GAMES
from team_meta import (
    CYRAC_RANK, get_cyrac_tier, get_meta, TEAM_META
)

app = FastAPI(title="Dataslate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "kt-selector-dev-secret")
security   = HTTPBearer(auto_error=False)

init_db()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def make_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return get_user(payload["sub"])
    except Exception:
        return None


def require_user(user=Depends(current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ── Models ────────────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    username: str
    password: str

class LoginBody(BaseModel):
    username: str
    password: str

class MatchBody(BaseModel):
    my_team:            str
    opponent_team:      str
    my_score:           int
    opponent_score:     int
    outcome:            str
    opponent_name:      Optional[str] = None
    notes:              Optional[str] = None
    ops_lost:           Optional[int] = None
    ops_killed:         Optional[int] = None
    tac_ops_score:      Optional[int] = None
    crit_ops_score:     Optional[int] = None
    kill_ops_score:     Optional[int] = None
    opp_tac_ops_score:  Optional[int] = None
    opp_crit_ops_score: Optional[int] = None
    opp_kill_ops_score: Optional[int] = None

class VoteBody(BaseModel):
    team_name: str
    score:     int

class NoteBody(BaseModel):
    team_name: str
    content:   str


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def api_register(body: RegisterBody):
    ok, msg = register(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    _, user = login(body.username, body.password)
    return {"token": make_token(user["id"]), "user": _safe_user(user)}


@app.post("/api/auth/login")
def api_login(body: LoginBody):
    ok, user = login(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": make_token(user["id"]), "user": _safe_user(user)}


@app.get("/api/auth/me")
def api_me(user=Depends(require_user)):
    return _safe_user(get_user(user["id"]))


def _safe_user(u: dict) -> dict:
    d = {k: v for k, v in u.items() if k != "password"}
    games = d.get("wins", 0) + d.get("draws", 0) + d.get("losses", 0)
    d["provisional"]     = is_provisional(games)
    d["provisional_games_needed"] = max(0, PROVISIONAL_GAMES - games)
    return d


# ── Kill team data ────────────────────────────────────────────────────────────

@app.get("/api/killteams")
def api_killteams():
    data = fetch_all_killteams()
    result = []
    for kt in data:
        name = kt.get("killteamName", "")
        meta = get_meta(name)
        result.append({
            "name":       name,
            "faction":    kt.get("factionName", ""),
            "cyrac_rank": CYRAC_RANK.get(name),
            "cyrac_tier": get_cyrac_tier(name),
            "size":       meta.get("size"),
            "play":       meta.get("play"),
            "tricksy":    meta.get("tricksy"),
        })
    return sorted(result, key=lambda x: x["name"])


@app.get("/api/killteams/{team_name}/operatives")
def api_operatives(team_name: str):
    data = fetch_all_killteams()
    for kt in data:
        if kt.get("killteamName") == team_name:
            ops = []
            for op in kt.get("opTypes", []):
                weapons = []
                for w in op.get("weapons", []):
                    for p in w.get("profiles", []):
                        weapons.append({
                            "name":    w.get("wepName",""),
                            "type":    "ranged" if w.get("wepType") in ("R","P") else "melee",
                            "attacks": p.get("ATK", 0),
                            "hit":     p.get("HIT", "4+"),
                            "damage":  p.get("DMG", "3/4"),
                            "rules":   p.get("WR", ""),
                        })
                ops.append({
                    "name":     op.get("opTypeName", op.get("opName", "")),
                    "move":     op.get("MOVE", 6),
                    "apl":      op.get("APL", 2),
                    "save":     op.get("SAVE", "5+"),
                    "wounds":   op.get("WOUNDS", 8),
                    "keywords": op.get("keywords", ""),
                    "weapons":  weapons,
                })
            return ops
    raise HTTPException(status_code=404, detail="Team not found")


@app.get("/api/killteams/{team_name}/ploys")
def api_ploys(team_name: str):
    data = fetch_all_killteams()
    for kt in data:
        if kt.get("killteamName") == team_name:
            return kt.get("ploys", [])
    raise HTTPException(status_code=404, detail="Team not found")


# ── Meta / rankings ───────────────────────────────────────────────────────────

@app.get("/api/meta")
def api_meta():
    from database import _conn
    vote_summaries = get_all_vote_summaries()

    # Load all faction ELOs in one query
    with _conn() as con:
        faction_rows = con.execute(
            "SELECT team_name, elo, wins, draws, losses FROM faction_elo"
        ).fetchall()
    faction_elos = {r["team_name"]: dict(r) for r in faction_rows}

    result = []
    for name, meta in TEAM_META.items():
        votes   = vote_summaries.get(name, {"avg_score": None, "vote_count": 0})
        faction = faction_elos.get(name)
        games   = (faction["wins"] + faction["draws"] + faction["losses"]) if faction else 0
        result.append({
            "name":            name,
            "cyrac_rank":      CYRAC_RANK.get(name),
            "cyrac_tier":      get_cyrac_tier(name),
            "community_score": votes["avg_score"],
            "vote_count":      votes["vote_count"],
            "size":            meta.get("size"),
            "play":            meta.get("play"),
            "tricksy":         meta.get("tricksy"),
            "faction_elo":     faction["elo"] if faction else faction_baseline(name),
            "faction_games":   games,
            "faction_elo_provisional": games < 10,
        })
    return sorted(result, key=lambda x: x["cyrac_rank"] or 999)


# ── Voting ────────────────────────────────────────────────────────────────────

@app.get("/api/votes/{team_name}")
def api_vote_summary(team_name: str):
    return get_team_vote_summary(team_name)


@app.get("/api/votes/{team_name}/mine")
def api_my_vote(team_name: str, user=Depends(require_user)):
    return {"score": get_user_vote(user["id"], team_name)}


@app.post("/api/votes")
def api_cast_vote(body: VoteBody, user=Depends(require_user)):
    ok, msg = cast_vote(user["id"], body.team_name, body.score)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "summary": get_team_vote_summary(body.team_name)}


# ── Community notes ───────────────────────────────────────────────────────────

@app.get("/api/notes/{team_name}")
def api_get_notes(team_name: str):
    return get_community_notes(team_name)


@app.post("/api/notes")
def api_add_note(body: NoteBody, user=Depends(require_user)):
    note = add_community_note(user["id"], body.team_name, body.content)
    return note


@app.post("/api/notes/{note_id}/upvote")
def api_upvote_note(note_id: int, user=Depends(require_user)):
    upvote_note(note_id, user["id"])
    return {"ok": True}


# ── Matches ───────────────────────────────────────────────────────────────────

@app.post("/api/matches")
def api_log_match(body: MatchBody, user=Depends(require_user)):
    updated = log_match(
        user["id"], body.my_team, body.opponent_team,
        body.my_score, body.opponent_score, body.outcome,
        body.opponent_name, body.notes,
        body.ops_lost, body.ops_killed,
        body.tac_ops_score, body.crit_ops_score, body.kill_ops_score,
        body.opp_tac_ops_score, body.opp_crit_ops_score, body.opp_kill_ops_score,
    )
    return _safe_user(updated)


@app.get("/api/matches")
def api_get_matches(user=Depends(require_user)):
    return get_match_history(user["id"])


@app.get("/api/matches/stats")
def api_match_stats(user=Depends(require_user)):
    return {
        "team_stats":   get_team_stats(user["id"]),
        "performance":  get_performance_stats(user["id"]),
    }


@app.get("/api/leaderboard")
def api_leaderboard():
    return get_leaderboard()


@app.get("/api/leaderboard/factions")
def api_faction_leaderboard():
    from database import _conn
    with _conn() as con:
        rows = con.execute("""
            SELECT team_name, elo,
                   wins, draws, losses,
                   (wins+draws+losses) as games,
                   ROUND(100.0*wins/MAX(1,wins+draws+losses),1) as win_rate
            FROM faction_elo
            WHERE (wins+draws+losses) >= 1
            ORDER BY elo DESC
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/meta/cyrac-info")
def api_cyrac_info():
    """Returns info about the current CYRAC data — when it was scraped and from where."""
    from team_meta import CYRAC_SCRAPED_AT, CYRAC_SOURCE_URL, CYRAC_TOTAL
    return {
        "scraped_at":  CYRAC_SCRAPED_AT,
        "source_url":  CYRAC_SOURCE_URL,
        "total_teams": CYRAC_TOTAL,
        "using_live_data": CYRAC_SCRAPED_AT is not None,
    }
