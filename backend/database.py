"""
database.py
-----------
SQLite backend for user accounts, match history, and ELO ratings.

Schema:
  users   — accounts, hashed passwords, ELO
  matches — match results linked to user

ELO:
  Starting rating: 1200
  K-factor: 32
  Unregistered opponents assumed at 1200 baseline
"""

import sqlite3
import bcrypt
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "kt_selector.db")
STARTING_PLAYER_ELO = 1200  # imported from elo.py where needed


# ── Connection ────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


# ── Initialise schema ─────────────────────────────────────────────────────────

def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password        TEXT    NOT NULL,
            player_elo      REAL    NOT NULL DEFAULT 1200,
            wins            INTEGER NOT NULL DEFAULT 0,
            draws           INTEGER NOT NULL DEFAULT 0,
            losses          INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS faction_elo (
            team_name       TEXT    PRIMARY KEY,
            elo             REAL    NOT NULL,
            wins            INTEGER NOT NULL DEFAULT 0,
            draws           INTEGER NOT NULL DEFAULT 0,
            losses          INTEGER NOT NULL DEFAULT 0,
            last_updated    TEXT
        );

        CREATE TABLE IF NOT EXISTS votes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            team_name   TEXT    NOT NULL,
            score       INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
            voted_at    TEXT    NOT NULL,
            updated_at  TEXT,
            UNIQUE(user_id, team_name)
        );

        CREATE TABLE IF NOT EXISTS matches (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id),
            my_team             TEXT    NOT NULL,
            opponent_team       TEXT    NOT NULL,
            my_score            INTEGER NOT NULL,
            opponent_score      INTEGER NOT NULL,
            outcome             TEXT    NOT NULL CHECK(outcome IN ('W','D','L')),
            elo_before          REAL    NOT NULL,
            elo_after           REAL    NOT NULL,
            elo_change          REAL    NOT NULL,
            opponent_name       TEXT,
            notes               TEXT,
            played_at           TEXT    NOT NULL,
            -- Performance breakdown
            ops_lost            INTEGER,   -- how many of your operatives died
            ops_killed          INTEGER,   -- how many enemy operatives you killed
            tac_ops_score       INTEGER,   -- your tac ops points
            crit_ops_score      INTEGER,   -- your crit ops points
            kill_ops_score      INTEGER,   -- your kill ops (kill-based tac ops) points
            opp_tac_ops_score   INTEGER,   -- opponent tac ops points
            opp_crit_ops_score  INTEGER,   -- opponent crit ops points
            opp_kill_ops_score  INTEGER    -- opponent kill ops points
        );
        """)


def _migrate():
    """Add new columns to existing databases without breaking old data."""
    # Votes table (may not exist on old DBs)
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                team_name   TEXT    NOT NULL,
                score       INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
                voted_at    TEXT    NOT NULL,
                updated_at  TEXT,
                UNIQUE(user_id, team_name)
            )
        """)

    new_cols = [
        ("ops_lost",           "INTEGER"),
        ("ops_killed",         "INTEGER"),
        ("tac_ops_score",      "INTEGER"),
        ("crit_ops_score",     "INTEGER"),
        ("kill_ops_score",     "INTEGER"),
        ("opp_tac_ops_score",  "INTEGER"),
        ("opp_crit_ops_score", "INTEGER"),
        ("opp_kill_ops_score", "INTEGER"),
    ]
    with _conn() as con:
        existing = {row[1] for row in con.execute("PRAGMA table_info(matches)").fetchall()}
        for col, ctype in new_cols:
            if col not in existing:
                con.execute(f"ALTER TABLE matches ADD COLUMN {col} {ctype}")


# ── Auth ──────────────────────────────────────────────────────────────────────

def register(username: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO users (username, password, created_at) VALUES (?,?,?)",
                (username.strip(), hashed, datetime.utcnow().isoformat())
            )
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "Username already taken."


def login(username: str, password: str) -> tuple[bool, dict | None]:
    """Verify credentials. Returns (success, user_dict)."""
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()

    if not row:
        return False, None
    if not bcrypt.checkpw(password.encode(), row["password"].encode()):
        return False, None

    return True, dict(row)


def get_user(user_id: int) -> dict | None:
    with _conn() as con:
        row = con.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


# ── Match logging ─────────────────────────────────────────────────────────────

def _get_or_init_faction(con, team_name: str) -> float:
    """Get faction ELO, initialising from baseline if not yet tracked."""
    from elo import faction_baseline
    row = con.execute("SELECT elo FROM faction_elo WHERE team_name=?", (team_name,)).fetchone()
    if row:
        return row["elo"]
    base = faction_baseline(team_name)
    con.execute(
        "INSERT OR IGNORE INTO faction_elo (team_name, elo) VALUES (?,?)",
        (team_name, base)
    )
    return base


def log_match(user_id: int, my_team: str, opponent_team: str,
              my_score: int, opponent_score: int, outcome: str,
              opponent_name: str = None, notes: str = None,
              ops_lost: int = None, ops_killed: int = None,
              tac_ops_score: int = None, crit_ops_score: int = None,
              kill_ops_score: int = None,
              opp_tac_ops_score: int = None, opp_crit_ops_score: int = None,
              opp_kill_ops_score: int = None) -> dict:
    """
    Log a match — updates both player ELO and faction ELO.
    Returns updated user dict.
    """
    from elo import (
        calc_player_elo, calc_faction_elo,
        faction_baseline, STARTING_PLAYER_ELO,
    )

    user = get_user(user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.utcnow().isoformat()

    with _conn() as con:
        # ── Player ELO ────────────────────────────────────────────────────
        player_elo_before = user["player_elo"]

        # Opponent player ELO
        opp_player_elo = STARTING_PLAYER_ELO
        if opponent_name:
            opp_row = con.execute(
                "SELECT player_elo FROM users WHERE username=? COLLATE NOCASE",
                (opponent_name.strip(),)
            ).fetchone()
            if opp_row:
                opp_player_elo = opp_row["player_elo"]

        player_elo_after, player_elo_change = calc_player_elo(
            player_elo_before, opp_player_elo, outcome, my_team
        )

        # ── Faction ELO ───────────────────────────────────────────────────
        my_faction_elo  = _get_or_init_faction(con, my_team)
        opp_faction_elo = _get_or_init_faction(con, opponent_team)

        new_faction_elo, faction_elo_change = calc_faction_elo(
            my_faction_elo, opp_faction_elo, outcome, my_team
        )

        # Opponent faction moves inversely
        opp_outcome = {"W": "L", "L": "W", "D": "D"}[outcome]
        new_opp_faction_elo, _ = calc_faction_elo(
            opp_faction_elo, my_faction_elo, opp_outcome, opponent_team
        )

        # ── Write match ───────────────────────────────────────────────────
        con.execute("""
            INSERT INTO matches
              (user_id, my_team, opponent_team, my_score, opponent_score,
               outcome, elo_before, elo_after, elo_change,
               opponent_name, notes, played_at,
               ops_lost, ops_killed,
               tac_ops_score, crit_ops_score, kill_ops_score,
               opp_tac_ops_score, opp_crit_ops_score, opp_kill_ops_score)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id, my_team, opponent_team, my_score, opponent_score,
            outcome, player_elo_before, player_elo_after, player_elo_change,
            opponent_name or None, notes or None, now,
            ops_lost, ops_killed,
            tac_ops_score, crit_ops_score, kill_ops_score,
            opp_tac_ops_score, opp_crit_ops_score, opp_kill_ops_score
        ))

        # ── Update player ─────────────────────────────────────────────────
        wins   = user["wins"]   + (1 if outcome == "W" else 0)
        draws  = user["draws"]  + (1 if outcome == "D" else 0)
        losses = user["losses"] + (1 if outcome == "L" else 0)

        con.execute(
            "UPDATE users SET player_elo=?, wins=?, draws=?, losses=? WHERE id=?",
            (player_elo_after, wins, draws, losses, user_id)
        )

        # ── Update faction ELOs ───────────────────────────────────────────
        for team, new_elo, w, d, l in [
            (my_team,       new_faction_elo,     1 if outcome=="W" else 0, 1 if outcome=="D" else 0, 1 if outcome=="L" else 0),
            (opponent_team, new_opp_faction_elo, 1 if opp_outcome=="W" else 0, 1 if opp_outcome=="D" else 0, 1 if opp_outcome=="L" else 0),
        ]:
            con.execute("""
                INSERT INTO faction_elo (team_name, elo, wins, draws, losses, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_name) DO UPDATE SET
                    elo=excluded.elo,
                    wins=wins+excluded.wins,
                    draws=draws+excluded.draws,
                    losses=losses+excluded.losses,
                    last_updated=excluded.last_updated
            """, (team, new_elo, w, d, l, now))

    return get_user(user_id)


# ── Queries ───────────────────────────────────────────────────────────────────

def get_match_history(user_id: int, limit: int = 50) -> list[dict]:
    with _conn() as con:
        rows = con.execute("""
            SELECT * FROM matches
            WHERE user_id = ?
            ORDER BY played_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
    return [dict(r) for r in rows]


def get_leaderboard(limit: int = 50) -> list[dict]:
    """Global ELO leaderboard — only shows players with at least 1 match."""
    with _conn() as con:
        rows = con.execute("""
            SELECT username, elo, wins, draws, losses,
                   (wins + draws + losses) AS matches,
                   ROUND(100.0 * wins / MAX(1, wins+draws+losses), 1) AS win_rate
            FROM users
            WHERE (wins + draws + losses) >= 1
            ORDER BY elo DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_team_stats(user_id: int) -> list[dict]:
    """Win/loss/draw breakdown per kill team for a user."""
    with _conn() as con:
        rows = con.execute("""
            SELECT my_team,
                   COUNT(*) as matches,
                   SUM(CASE WHEN outcome='W' THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN outcome='D' THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN outcome='L' THEN 1 ELSE 0 END) as losses,
                   ROUND(AVG(elo_change), 1) as avg_elo_change
            FROM matches WHERE user_id = ?
            GROUP BY my_team ORDER BY matches DESC
        """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def get_performance_stats(user_id: int) -> dict:
    """Aggregate performance breakdown across all matches with data."""
    with _conn() as con:
        row = con.execute("""
            SELECT
                AVG(ops_lost)           as avg_ops_lost,
                AVG(ops_killed)         as avg_ops_killed,
                AVG(tac_ops_score)      as avg_tac,
                AVG(crit_ops_score)     as avg_crit,
                AVG(kill_ops_score)     as avg_kill,
                AVG(opp_tac_ops_score)  as avg_opp_tac,
                AVG(opp_crit_ops_score) as avg_opp_crit,
                AVG(opp_kill_ops_score) as avg_opp_kill,
                COUNT(*)                as total_with_data
            FROM matches
            WHERE user_id = ? AND ops_lost IS NOT NULL
        """, (user_id,)).fetchone()

        # Per-outcome averages
        outcome_rows = con.execute("""
            SELECT outcome,
                   AVG(ops_lost)      as avg_ops_lost,
                   AVG(ops_killed)    as avg_ops_killed,
                   AVG(tac_ops_score) as avg_tac,
                   AVG(crit_ops_score)as avg_crit,
                   COUNT(*)           as matches
            FROM matches
            WHERE user_id = ? AND ops_lost IS NOT NULL
            GROUP BY outcome
        """, (user_id,)).fetchall()

    return {
        "totals": dict(row) if row else {},
        "by_outcome": [dict(r) for r in outcome_rows],
    }


# ── Community voting ─────────────────────────────────────────────────────────

def can_vote(user_id: int) -> tuple[bool, str]:
    """Check if user is eligible to vote (must have at least 1 logged match)."""
    user = get_user(user_id)
    if not user:
        return False, "Not logged in."
    total = user["wins"] + user["draws"] + user["losses"]
    if total < 1:
        return False, "You need to log at least 1 match before voting."
    return True, "OK"


def cast_vote(user_id: int, team_name: str, score: int) -> tuple[bool, str]:
    """
    Cast or update a vote for a kill team.
    Returns (success, message).
    Score must be 1-10.
    """
    if not (1 <= score <= 10):
        return False, "Score must be between 1 and 10."

    ok, msg = can_vote(user_id)
    if not ok:
        return False, msg

    now = datetime.utcnow().isoformat()
    with _conn() as con:
        existing = con.execute(
            "SELECT id FROM votes WHERE user_id=? AND team_name=?",
            (user_id, team_name)
        ).fetchone()

        if existing:
            con.execute(
                "UPDATE votes SET score=?, updated_at=? WHERE user_id=? AND team_name=?",
                (score, now, user_id, team_name)
            )
            return True, f"Vote updated to {score}/10."
        else:
            con.execute(
                "INSERT INTO votes (user_id, team_name, score, voted_at) VALUES (?,?,?,?)",
                (user_id, team_name, score, now)
            )
            return True, f"Vote cast: {score}/10."


def get_user_vote(user_id: int, team_name: str) -> int | None:
    """Get a user's current vote for a team, or None if not voted."""
    with _conn() as con:
        row = con.execute(
            "SELECT score FROM votes WHERE user_id=? AND team_name=?",
            (user_id, team_name)
        ).fetchone()
    return row["score"] if row else None


def get_team_vote_summary(team_name: str) -> dict:
    """Get aggregated community vote data for a team."""
    with _conn() as con:
        row = con.execute("""
            SELECT
                ROUND(AVG(score), 2) as avg_score,
                COUNT(*)             as vote_count,
                MIN(score)           as min_score,
                MAX(score)           as max_score
            FROM votes WHERE team_name = ?
        """, (team_name,)).fetchone()

        dist = con.execute("""
            SELECT score, COUNT(*) as count
            FROM votes WHERE team_name = ?
            GROUP BY score ORDER BY score
        """, (team_name,)).fetchall()

    return {
        "avg_score":   row["avg_score"]  or 0,
        "vote_count":  row["vote_count"] or 0,
        "min_score":   row["min_score"]  or 0,
        "max_score":   row["max_score"]  or 0,
        "distribution": {r["score"]: r["count"] for r in dist},
    }


def get_all_vote_summaries() -> dict[str, dict]:
    """Get vote summaries for all teams in one query — used for rankings page."""
    with _conn() as con:
        rows = con.execute("""
            SELECT
                team_name,
                ROUND(AVG(score), 2) as avg_score,
                COUNT(*)             as vote_count
            FROM votes
            GROUP BY team_name
            ORDER BY avg_score DESC
        """).fetchall()
    return {r["team_name"]: {"avg_score": r["avg_score"], "vote_count": r["vote_count"]} for r in rows}


def username_exists(username: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()
    return row is not None


# ── Community notes ───────────────────────────────────────────────────────────

def _ensure_notes_table():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS community_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            team_name   TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            upvotes     INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS note_upvotes (
            user_id INTEGER NOT NULL,
            note_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, note_id)
        );
        """)

_ensure_notes_table()


def add_community_note(user_id: int, team_name: str, content: str) -> dict:
    now = datetime.utcnow().isoformat()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO community_notes (user_id, team_name, content, created_at) VALUES (?,?,?,?)",
            (user_id, team_name, content.strip(), now)
        )
        row = con.execute(
            """SELECT n.*, u.username FROM community_notes n
               JOIN users u ON u.id = n.user_id WHERE n.id = ?""",
            (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def get_community_notes(team_name: str) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            """SELECT n.*, u.username FROM community_notes n
               JOIN users u ON u.id = n.user_id
               WHERE n.team_name = ?
               ORDER BY n.upvotes DESC, n.created_at DESC""",
            (team_name,)
        ).fetchall()
    return [dict(r) for r in rows]


def upvote_note(note_id: int, user_id: int):
    with _conn() as con:
        try:
            con.execute(
                "INSERT INTO note_upvotes (user_id, note_id) VALUES (?,?)",
                (user_id, note_id)
            )
            con.execute(
                "UPDATE community_notes SET upvotes = upvotes + 1 WHERE id = ?",
                (note_id,)
            )
        except Exception:
            pass  # already upvoted
