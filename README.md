# Killrate v2

## Setup

### 1. Backend
```
cd backend
pip install -r requirements.txt
python update_data.py          # cache ktdash data locally
uvicorn main:app --reload      # runs on http://localhost:8000
```

### 2. Frontend (new terminal)
```
cd frontend
npm install
npm run dev                    # runs on http://localhost:5173
```

Open http://localhost:5173

---

## Structure
```
backend/
  main.py          FastAPI app
  database.py      SQLite — users, matches, votes, notes
  team_meta.py     CYRAC rankings + team characteristics
  api.py           ktdash.app data fetch
  update_data.py   refresh local killteams.json
  data/            killteams.json + kt_selector.db

frontend/
  src/
    pages/
      Meta.tsx     CYRAC + community rankings table
      TeamRadar.tsx team radar chart + voting + notes
      MyRecord.tsx  game log + ELO chart + matchup tips
      Account.tsx   login / register
```

## Updating data
When GW releases new kill teams:
```
cd backend
python update_data.py
```
