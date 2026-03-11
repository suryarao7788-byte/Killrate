"""
database.py — PostgreSQL (production) + SQLite (local dev)
Set DATABASE_URL env var for PostgreSQL. Falls back to SQLite if not set.
"""

import os, bcrypt
from datetime import datetime, timezone

DATABASE_URL        = os.getenv("DATABASE_URL")
STARTING_PLAYER_ELO = 1200
_PG                 = bool(DATABASE_URL)
_DB_PATH            = os.path.join(os.path.dirname(__file__), "data", "dataslate.db")

def _conn():
    if _PG:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    import sqlite3
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    con = sqlite3.connect(_DB_PATH, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=5000")
    return con

def _p(): return "%s" if _PG else "?"

def _one(cur):
    row = cur.fetchone()
    if row is None: return None
    if _PG:
        return dict(zip([d[0] for d in cur.description], row))
    return dict(row)

def _all(cur):
    rows = cur.fetchall()
    if _PG:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    return [dict(r) for r in rows]

def _exec(cur, sql, params=()):
    cur.execute(sql, params)


# ── Schema ─────────────────────────────────────────────────────────────────────

def init_db():
    con = _conn()
    cur = con.cursor()
    try:
        if _PG:
            stmts = [
                """CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL, player_elo REAL NOT NULL DEFAULT 1200,
                    wins INT NOT NULL DEFAULT 0, draws INT NOT NULL DEFAULT 0,
                    losses INT NOT NULL DEFAULT 0, created_at TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS faction_elo (
                    team_name TEXT PRIMARY KEY, elo REAL NOT NULL,
                    wins INT NOT NULL DEFAULT 0, draws INT NOT NULL DEFAULT 0,
                    losses INT NOT NULL DEFAULT 0, last_updated TEXT)""",
                """CREATE TABLE IF NOT EXISTS votes (
                    id SERIAL PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id),
                    team_name TEXT NOT NULL, score INT NOT NULL CHECK(score BETWEEN 1 AND 10),
                    voted_at TEXT NOT NULL, updated_at TEXT, UNIQUE(user_id, team_name))""",
                """CREATE TABLE IF NOT EXISTS matches (
                    id SERIAL PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id),
                    my_team TEXT NOT NULL, opponent_team TEXT NOT NULL,
                    my_score INT NOT NULL, opponent_score INT NOT NULL,
                    outcome TEXT NOT NULL CHECK(outcome IN ('W','D','L')),
                    elo_before REAL NOT NULL, elo_after REAL NOT NULL, elo_change REAL NOT NULL,
                    opponent_name TEXT, notes TEXT, played_at TEXT NOT NULL,
                    ops_lost INT, ops_killed INT, tac_ops_score INT, crit_ops_score INT,
                    kill_ops_score INT, opp_tac_ops_score INT, opp_crit_ops_score INT,
                    opp_kill_ops_score INT)""",
                """CREATE TABLE IF NOT EXISTS community_notes (
                    id SERIAL PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id),
                    team_name TEXT NOT NULL, content TEXT NOT NULL,
                    upvotes INT NOT NULL DEFAULT 0, created_at TEXT NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS note_upvotes (
                    user_id INT NOT NULL, note_id INT NOT NULL,
                    PRIMARY KEY (user_id, note_id))""",
            ]
            for s in stmts: cur.execute(s)
        else:
            cur.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password TEXT NOT NULL, player_elo REAL NOT NULL DEFAULT 1200,
                wins INTEGER NOT NULL DEFAULT 0, draws INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS faction_elo (
                team_name TEXT PRIMARY KEY, elo REAL NOT NULL,
                wins INTEGER NOT NULL DEFAULT 0, draws INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0, last_updated TEXT);
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
                team_name TEXT NOT NULL, score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
                voted_at TEXT NOT NULL, updated_at TEXT, UNIQUE(user_id, team_name));
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
                my_team TEXT NOT NULL, opponent_team TEXT NOT NULL,
                my_score INTEGER NOT NULL, opponent_score INTEGER NOT NULL,
                outcome TEXT NOT NULL CHECK(outcome IN ('W','D','L')),
                elo_before REAL NOT NULL, elo_after REAL NOT NULL, elo_change REAL NOT NULL,
                opponent_name TEXT, notes TEXT, played_at TEXT NOT NULL,
                ops_lost INTEGER, ops_killed INTEGER, tac_ops_score INTEGER,
                crit_ops_score INTEGER, kill_ops_score INTEGER,
                opp_tac_ops_score INTEGER, opp_crit_ops_score INTEGER, opp_kill_ops_score INTEGER);
            CREATE TABLE IF NOT EXISTS community_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
                team_name TEXT NOT NULL, content TEXT NOT NULL,
                upvotes INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS note_upvotes (
                user_id INTEGER NOT NULL, note_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, note_id));
            """)
        con.commit()
    finally:
        con.close()


# ── Auth ───────────────────────────────────────────────────────────────────────

def register(username: str, password: str) -> tuple[bool, str]:
    if len(username.strip()) < 3: return False, "Username must be at least 3 characters."
    if len(password) < 6:         return False, "Password must be at least 6 characters."
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    p = _p(); con = _conn()
    try:
        cur = con.cursor()
        cur.execute(f"INSERT INTO users (username, password, created_at) VALUES ({p},{p},{p})",
                    (username.strip(), hashed, datetime.now(timezone.utc).isoformat()))
        con.commit(); return True, "Account created."
    except Exception as e:
        con.rollback()
        return (False, "Username already taken.") if "unique" in str(e).lower() else (False, str(e))
    finally: con.close()


def login(username: str, password: str) -> tuple[bool, dict | None]:
    p = _p(); con = _conn()
    try:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM users WHERE LOWER(username)=LOWER({p})", (username.strip(),))
        row = _one(cur)
    finally: con.close()
    if not row: return False, None
    if not bcrypt.checkpw(password.encode(), row["password"].encode()): return False, None
    return True, row


def get_user(user_id: int) -> dict | None:
    p = _p(); con = _conn()
    try:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM users WHERE id={p}", (user_id,))
        return _one(cur)
    finally: con.close()


# ── Match logging ──────────────────────────────────────────────────────────────

def _get_or_init_faction(cur, team_name: str) -> float:
    from elo import faction_baseline
    p = _p()
    cur.execute(f"SELECT elo FROM faction_elo WHERE team_name={p}", (team_name,))
    row = cur.fetchone()
    if row: return row[0]
    base = faction_baseline(team_name)
    if _PG:
        cur.execute(f"INSERT INTO faction_elo (team_name,elo) VALUES ({p},{p}) ON CONFLICT DO NOTHING", (team_name, base))
    else:
        cur.execute(f"INSERT OR IGNORE INTO faction_elo (team_name,elo) VALUES ({p},{p})", (team_name, base))
    return base


def log_match(user_id, my_team, opponent_team, my_score, opponent_score, outcome,
              opponent_name=None, notes=None, ops_lost=None, ops_killed=None,
              tac_ops_score=None, crit_ops_score=None, kill_ops_score=None,
              opp_tac_ops_score=None, opp_crit_ops_score=None, opp_kill_ops_score=None):
    from elo import calc_player_elo, calc_faction_elo, STARTING_PLAYER_ELO
    user = get_user(user_id)
    if not user: raise ValueError("User not found")
    now = datetime.now(timezone.utc).isoformat()
    p = _p(); con = _conn()
    try:
        cur = con.cursor()
        # Player ELO
        pb = user["player_elo"]; opp_elo = STARTING_PLAYER_ELO
        if opponent_name:
            cur.execute(f"SELECT player_elo FROM users WHERE LOWER(username)=LOWER({p})", (opponent_name.strip(),))
            r = cur.fetchone()
            if r: opp_elo = r[0]
        pa, pc = calc_player_elo(pb, opp_elo, outcome, my_team)
        # Faction ELO
        mfe = _get_or_init_faction(cur, my_team)
        ofe = _get_or_init_faction(cur, opponent_team)
        new_mfe, _ = calc_faction_elo(mfe, ofe, outcome, my_team)
        oo = {"W":"L","L":"W","D":"D"}[outcome]
        new_ofe, _ = calc_faction_elo(ofe, mfe, oo, opponent_team)
        # Insert match
        cur.execute(f"""
            INSERT INTO matches (user_id,my_team,opponent_team,my_score,opponent_score,
              outcome,elo_before,elo_after,elo_change,opponent_name,notes,played_at,
              ops_lost,ops_killed,tac_ops_score,crit_ops_score,kill_ops_score,
              opp_tac_ops_score,opp_crit_ops_score,opp_kill_ops_score)
            VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
        """, (user_id,my_team,opponent_team,my_score,opponent_score,outcome,pb,pa,pc,
              opponent_name,notes,now,ops_lost,ops_killed,tac_ops_score,crit_ops_score,
              kill_ops_score,opp_tac_ops_score,opp_crit_ops_score,opp_kill_ops_score))
        # Update player
        w=user["wins"]+(1 if outcome=="W" else 0)
        d=user["draws"]+(1 if outcome=="D" else 0)
        l=user["losses"]+(1 if outcome=="L" else 0)
        cur.execute(f"UPDATE users SET player_elo={p},wins={p},draws={p},losses={p} WHERE id={p}", (pa,w,d,l,user_id))
        # Update faction ELOs
        for tn, ne, fw, fd, fl in [
            (my_team, new_mfe, 1 if outcome=="W" else 0, 1 if outcome=="D" else 0, 1 if outcome=="L" else 0),
            (opponent_team, new_ofe, 1 if oo=="W" else 0, 1 if oo=="D" else 0, 1 if oo=="L" else 0),
        ]:
            if _PG:
                cur.execute(f"""INSERT INTO faction_elo (team_name,elo,wins,draws,losses,last_updated)
                    VALUES ({p},{p},{p},{p},{p},{p}) ON CONFLICT (team_name) DO UPDATE SET
                    elo=EXCLUDED.elo, wins=faction_elo.wins+EXCLUDED.wins,
                    draws=faction_elo.draws+EXCLUDED.draws, losses=faction_elo.losses+EXCLUDED.losses,
                    last_updated=EXCLUDED.last_updated""", (tn,ne,fw,fd,fl,now))
            else:
                cur.execute(f"""INSERT INTO faction_elo (team_name,elo,wins,draws,losses,last_updated)
                    VALUES ({p},{p},{p},{p},{p},{p}) ON CONFLICT(team_name) DO UPDATE SET
                    elo=excluded.elo, wins=wins+excluded.wins, draws=draws+excluded.draws,
                    losses=losses+excluded.losses, last_updated=excluded.last_updated""", (tn,ne,fw,fd,fl,now))
        con.commit()
    except:
        con.rollback(); raise
    finally: con.close()
    return get_user(user_id)


def get_match_history(user_id):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"SELECT * FROM matches WHERE user_id={p} ORDER BY played_at DESC",(user_id,))
        return _all(cur)
    finally: con.close()


def get_leaderboard():
    con=_conn()
    try:
        cur=con.cursor()
        cur.execute("SELECT id,username,player_elo,wins,draws,losses,(wins+draws+losses) as games FROM users WHERE (wins+draws+losses)>=3 ORDER BY player_elo DESC LIMIT 50")
        return _all(cur)
    finally: con.close()


def get_team_stats(user_id):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"""SELECT my_team, COUNT(*) as matches,
            SUM(CASE WHEN outcome='W' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome='D' THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN outcome='L' THEN 1 ELSE 0 END) as losses,
            ROUND(AVG(elo_change)::numeric,1) as avg_elo_change
            FROM matches WHERE user_id={p} GROUP BY my_team ORDER BY matches DESC
        """ if _PG else f"""SELECT my_team, COUNT(*) as matches,
            SUM(CASE WHEN outcome='W' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome='D' THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN outcome='L' THEN 1 ELSE 0 END) as losses,
            ROUND(AVG(elo_change),1) as avg_elo_change
            FROM matches WHERE user_id={p} GROUP BY my_team ORDER BY matches DESC""", (user_id,))
        return _all(cur)
    finally: con.close()


def get_performance_stats(user_id):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"""SELECT AVG(ops_lost) as avg_ops_lost, AVG(ops_killed) as avg_ops_killed,
            AVG(tac_ops_score) as avg_tac, AVG(crit_ops_score) as avg_crit,
            AVG(kill_ops_score) as avg_kill, AVG(opp_tac_ops_score) as avg_opp_tac,
            AVG(opp_crit_ops_score) as avg_opp_crit, AVG(opp_kill_ops_score) as avg_opp_kill,
            COUNT(*) as total_with_data FROM matches WHERE user_id={p} AND ops_lost IS NOT NULL""", (user_id,))
        totals = _one(cur)
        cur.execute(f"""SELECT outcome, AVG(ops_lost) as avg_ops_lost, AVG(ops_killed) as avg_ops_killed,
            AVG(tac_ops_score) as avg_tac, AVG(crit_ops_score) as avg_crit, COUNT(*) as matches
            FROM matches WHERE user_id={p} AND ops_lost IS NOT NULL GROUP BY outcome""", (user_id,))
        return {"totals": totals or {}, "by_outcome": _all(cur)}
    finally: con.close()


# ── Voting ─────────────────────────────────────────────────────────────────────

def can_vote(user_id):
    user = get_user(user_id)
    if not user: return False, "Not logged in."
    if (user["wins"]+user["draws"]+user["losses"]) < 1: return False, "Log at least 1 match before voting."
    return True, "OK"


def cast_vote(user_id, team_name, score):
    if not (1 <= score <= 10): return False, "Score must be 1–10."
    ok, msg = can_vote(user_id)
    if not ok: return False, msg
    p=_p(); now=datetime.now(timezone.utc).isoformat(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"SELECT id FROM votes WHERE user_id={p} AND team_name={p}", (user_id, team_name))
        if cur.fetchone():
            cur.execute(f"UPDATE votes SET score={p},updated_at={p} WHERE user_id={p} AND team_name={p}", (score,now,user_id,team_name))
            msg=f"Vote updated to {score}/10."
        else:
            cur.execute(f"INSERT INTO votes (user_id,team_name,score,voted_at) VALUES ({p},{p},{p},{p})", (user_id,team_name,score,now))
            msg=f"Vote cast: {score}/10."
        con.commit(); return True, msg
    except Exception as e:
        con.rollback(); return False, str(e)
    finally: con.close()


def get_user_vote(user_id, team_name):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"SELECT score FROM votes WHERE user_id={p} AND team_name={p}", (user_id,team_name))
        row=cur.fetchone(); return row[0] if row else None
    finally: con.close()


def get_team_vote_summary(team_name):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        agg = "ROUND(AVG(score)::numeric,2)" if _PG else "ROUND(AVG(score),2)"
        cur.execute(f"SELECT {agg} as avg_score, COUNT(*) as vote_count, MIN(score) as min_score, MAX(score) as max_score FROM votes WHERE team_name={p}", (team_name,))
        row=_one(cur)
        cur.execute(f"SELECT score, COUNT(*) as count FROM votes WHERE team_name={p} GROUP BY score ORDER BY score", (team_name,))
        dist=_all(cur)
        return {"avg_score": row["avg_score"] or 0, "vote_count": row["vote_count"] or 0,
                "min_score": row["min_score"] or 0, "max_score": row["max_score"] or 0,
                "distribution": {r["score"]: r["count"] for r in dist}}
    finally: con.close()


def get_all_vote_summaries():
    con=_conn()
    try:
        cur=con.cursor()
        agg = "ROUND(AVG(score)::numeric,2)" if _PG else "ROUND(AVG(score),2)"
        cur.execute(f"SELECT team_name, {agg} as avg_score, COUNT(*) as vote_count FROM votes GROUP BY team_name ORDER BY avg_score DESC")
        return {r["team_name"]: {"avg_score": r["avg_score"], "vote_count": r["vote_count"]} for r in _all(cur)}
    finally: con.close()


# ── Community notes ────────────────────────────────────────────────────────────

def add_community_note(user_id, team_name, content):
    p=_p(); now=datetime.now(timezone.utc).isoformat(); con=_conn()
    try:
        cur=con.cursor()
        if _PG:
            cur.execute(f"INSERT INTO community_notes (user_id,team_name,content,created_at) VALUES ({p},{p},{p},{p}) RETURNING id", (user_id,team_name,content.strip(),now))
            note_id=cur.fetchone()[0]
        else:
            cur.execute(f"INSERT INTO community_notes (user_id,team_name,content,created_at) VALUES ({p},{p},{p},{p})", (user_id,team_name,content.strip(),now))
            note_id=cur.lastrowid
        cur.execute(f"SELECT n.*,u.username FROM community_notes n JOIN users u ON u.id=n.user_id WHERE n.id={p}", (note_id,))
        row=_one(cur); con.commit(); return row
    except:
        con.rollback(); raise
    finally: con.close()


def get_community_notes(team_name):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        cur.execute(f"SELECT n.*,u.username FROM community_notes n JOIN users u ON u.id=n.user_id WHERE n.team_name={p} ORDER BY n.upvotes DESC, n.created_at DESC", (team_name,))
        return _all(cur)
    finally: con.close()


def upvote_note(note_id, user_id):
    p=_p(); con=_conn()
    try:
        cur=con.cursor()
        try:
            cur.execute(f"INSERT INTO note_upvotes (user_id,note_id) VALUES ({p},{p})", (user_id,note_id))
            cur.execute(f"UPDATE community_notes SET upvotes=upvotes+1 WHERE id={p}", (note_id,))
            con.commit()
        except: con.rollback()
    finally: con.close()
