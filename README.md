# 🏰 RUNCONQUER
[Live Demo](#-live-demo)
<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Run to conquer the map. Every kilometre you run expands your kingdom.**
**Skip a day and it decays. Outrun your rivals to conquer their territory.**

 •[Features](#-features) • [How It Works](#-how-it-works) • [Tech Stack](#-tech-stack) • [Quick Start](#-quick-start) • [API Docs](#-api-reference) • [Roadmap](#-roadmap)

</div>

---

## 📖 About The Project

 RunConquer is a **fitness gamification backend** that turns your real-world running activity into a competitive territory game on a shared world map.

Most people don't exercise because there's no immediate, visible reward. FitKingdom changes that — every run you do physically grows a kingdom on a map that other players can see and attack. Your territory is always at risk. Someone nearby is running more than you right now. That urgency is the motivation.

The backend is built with **Python FastAPI**, uses **PostgreSQL with the PostGIS geospatial extension** for territory overlap detection, and runs a **nightly background scheduler** that decays inactive kingdoms automatically. It exposes a clean **REST API** that a mobile app or web frontend can consume.

This project was built as a college placement portfolio piece to demonstrate:
- Real-world API design and development
- Geospatial data modeling and queries
- Game mechanics implementation
- Background job scheduling
- JWT-based authentication
- Clean project architecture

---

## 🎬 Live Demo

🚀 **API Live URL:**  
**https://runconquer-gamified-gps-territory.onrender.com/**

📖 **Interactive Swagger Docs (try every endpoint in your browser):**  
**https://runconquer-gamified-gps-territory.onrender.com/docs**

> No setup needed — open the Swagger UI, click **Register**, log a run, and watch your territory expand on the leaderboard instantly.

---

## ✨ Features

### 🗺️ Territory System
Every run you log expands your kingdom's circular territory on a real world map. The radius grows proportionally to your distance — run 5 km and your radius grows by 5 km. Your territory is stored as a PostGIS geometry point with a radius, enabling efficient spatial overlap detection across all players.

### ⚔️ Conquest Mechanic
If your territory overlaps another player's by more than 30% AND your radius is larger, you absorb their overlap zone. Their kingdom shrinks, yours grows. This creates a competitive dynamic where players in nearby cities are natural rivals. The system checks for conquest automatically every time a run is logged.

### 📉 Daily Decay
Miss a day of running and your territory shrinks by 10%. This is processed every night at midnight by a background scheduler. It prevents inactive players from holding territory forever and forces consistent activity — which is the whole point.

### 🔥 Streak Bonus
Maintain a 7-day consecutive running streak and all your territory gains are multiplied by 1.5×. This rewards consistency and makes streaks genuinely valuable. The streak resets if you miss any single day.

### 👑 Kingdom Levels
As your territory area grows you unlock new kingdom titles — from humble Village all the way to a continent-spanning Empire. Level is automatically calculated from area and updates in real-time.

### 🏆 Leaderboard
A global leaderboard ranked by total territory area controlled. Updated live as runs are logged and decay is applied. Shows kingdom name, level, area, and current streak for every active player.

### 🔐 Secure Authentication
Registration and login with **bcrypt password hashing** and **JWT tokens**. Tokens expire after 7 days. All protected routes validate the token and load the current user automatically via a FastAPI dependency.

### 📊 Run Analytics
Every run stores distance, duration, pace, speed, GPS coordinates, and source (manual or Strava). Personal stats endpoint aggregates lifetime totals, averages, and personal bests.

---

## 🎮 How It Works

```
Player registers and names their kingdom
         │
         ▼
Player logs a run (distance + GPS location)
         │
         ├──► Territory radius grows by distance_km × multiplier
         │
         ├──► Streak checked → 7+ days = 1.5× bonus applied
         │
         ├──► Conquest check → overlapping smaller kingdoms are absorbed
         │
         └──► Response includes new territory, streak, level, and any conquests

Every night at midnight (automatic)
         │
         └──► Players who didn't run today: territory shrinks 10%, streak resets
```

### Territory Radius Formula

```
gain = distance_km × KM_PER_TERRITORY_RADIUS × streak_multiplier

where:
  KM_PER_TERRITORY_RADIUS = 1.0  (configurable)
  streak_multiplier       = 1.5 if streak >= 7 days, else 1.0
  max radius              = 50 km (configurable)
```

### Conquest Condition

```
Two territories A and B:
  distance_between_centers < (radius_A + radius_B)   →  they overlap
  overlap_ratio > 0.30                                →  conquest triggers
  radius_A > radius_B                                 →  A conquers B

Result: B loses (overlap_ratio × radius_B) km from its radius
```

### Decay Formula

```
Every day a player does NOT run:
  new_radius = current_radius × (1 - DAILY_DECAY_PERCENT / 100)
             = current_radius × 0.90   (10% decay by default)
```

### Kingdom Level Thresholds

| Level | Title | Territory Area | What it means |
|-------|-------|---------------|---------------|
| 1 | 🏘️ Village | < 50 km² | You just started — keep running |
| 2 | 🏙️ Town | 50 – 300 km² | ~4 km daily runs consistently |
| 3 | 🌆 City | 300 – 1,000 km² | Serious runner, multiple conquests |
| 4 | 🏰 Kingdom | 1,000 – 5,000 km² | Regional dominant — hard to beat |
| 5 | 👑 Empire | > 5,000 km² | Top 1% — a running machine |

---

## 🧱 Tech Stack

### Backend
| Technology | Version | Why We Use It |
|-----------|---------|--------------|
| **Python** | 3.11+ | Primary language — clean syntax, huge ecosystem |
| **FastAPI** | 0.111 | Modern async Python framework, automatic Swagger docs, excellent performance |
| **SQLAlchemy** | 2.0 | Python ORM — maps Python classes to database tables |
| **Pydantic v2** | 2.7 | Request/response validation, type safety, auto-documentation |
| **Uvicorn** | 0.29 | ASGI server — runs the FastAPI app in production |

### Database
| Technology | Version | Why We Use It |
|-----------|---------|--------------|
| **PostgreSQL** | 16 | Industry-standard relational database, robust and battle-tested |
| **PostGIS** | 3.4 | Geospatial extension for PostgreSQL — enables location-based queries |
| **GeoAlchemy2** | 0.15 | SQLAlchemy extension for PostGIS geometry columns |
| **Redis** | 7.0 | In-memory cache for leaderboard and live session state |

### Auth & Security
| Technology | Purpose |
|-----------|---------|
| **python-jose** | JWT token encoding and decoding |
| **passlib + bcrypt** | Secure password hashing |
| **OAuth2PasswordBearer** | FastAPI built-in token extraction from request headers |

### Geospatial & Math
| Technology | Purpose |
|-----------|---------|
| **Shapely** | Geometric operations on territory shapes |
| **Geopy** | Geospatial utilities and coordinate helpers |
| **Haversine formula** | Real-world distance calculation between GPS coordinates |

### Background Jobs
| Technology | Purpose |
|-----------|---------|
| **APScheduler** | Runs the nightly decay job at midnight every day |

### Testing
| Technology | Purpose |
|-----------|---------|
| **Pytest** | Unit tests for game logic and API routes |

---

## 📁 Project Structure

```
fitkingdom/
│
├── app/                            # Main application package
│   │
│   ├── main.py                     # FastAPI app creation, CORS middleware, route
│   │                               # registration, and startup/shutdown lifecycle.
│   │                               # On startup: creates DB tables + starts scheduler.
│   │
│   ├── core/                       # Foundation layer — config, DB, security
│   │   ├── config.py               # Reads all .env variables using pydantic-settings.
│   │   │                           # All game balance settings live here so you can
│   │   │                           # tune the game without touching code.
│   │   │                           # Uses @lru_cache so .env is only read once.
│   │   │
│   │   ├── database.py             # SQLAlchemy engine + SessionLocal factory.
│   │   │                           # get_db() is a FastAPI dependency that opens
│   │   │                           # and closes a DB session per HTTP request.
│   │   │
│   │   └── security.py             # create_access_token() builds signed JWT tokens.
│   │                               # verify_token() decodes and validates them.
│   │                               # get_current_user() is used in all protected
│   │                               # routes to auto-load the logged-in user.
│   │
│   ├── models/                     # SQLAlchemy ORM models (database tables)
│   │   │
│   │   ├── user.py                 # User table. Stores: username, email,
│   │   │                           # hashed_password, kingdom_name, total_km_run,
│   │   │                           # current_streak, longest_streak, kingdom_level,
│   │   │                           # last_run_at (used to detect decay eligibility).
│   │   │
│   │   └── territory.py            # Three tables in one file:
│   │                               #
│   │                               # Territory — one per player. Stores center_point
│   │                               # as a PostGIS POINT geometry, radius_km, area_km2,
│   │                               # and color_hex for map rendering.
│   │                               #
│   │                               # Run — one record per logged run. Stores distance,
│   │                               # duration, pace, GPS start coordinates, and an
│   │                               # optional full GPS path as PostGIS LINESTRING.
│   │                               #
│   │                               # ConquestEvent — permanent log of every conquest.
│   │                               # Stores attacker_id, defender_id, km_conquered.
│   │
│   ├── schemas/                    # Pydantic models for API input/output validation
│   │   └── schemas.py              # UserRegister — validates signup data.
│   │                               # UserPublic — safe user response (no password).
│   │                               # RunCreate — validates a new run submission.
│   │                               # TerritoryPublic — territory response shape.
│   │                               # MapEntry — compact entry for the world map.
│   │                               # LeaderboardEntry — ranked player data.
│   │
│   ├── services/                   # Business logic — separated from HTTP layer
│   │   │
│   │   ├── territory_engine.py     # THE CORE OF THE GAME. Contains:
│   │   │                           #
│   │   │                           # haversine_distance_km() — calculates real-world
│   │   │                           # distance between two GPS coordinates using the
│   │   │                           # Haversine formula (accounts for Earth's curvature).
│   │   │                           #
│   │   │                           # territories_overlap() — checks if two circular
│   │   │                           # territories intersect and returns overlap ratio.
│   │   │                           #
│   │   │                           # calculate_territory_gain() — applies streak
│   │   │                           # multiplier to raw km distance.
│   │   │                           #
│   │   │                           # expand_territory() — called after every run.
│   │   │                           # Creates or expands territory, nudges center toward
│   │   │                           # new run location, updates all player stats.
│   │   │                           #
│   │   │                           # apply_daily_decay() — called by the nightly job.
│   │   │                           # Loops all territories and shrinks those whose
│   │   │                           # owner did not run that day.
│   │   │                           #
│   │   │                           # check_and_apply_conquest() — scans all territories
│   │   │                           # for overlap with the attacker after a run, applies
│   │   │                           # conquest if conditions are met, logs ConquestEvents.
│   │   │
│   │   └── scheduler.py            # APScheduler setup. Registers nightly_decay_job
│   │                               # to fire at midnight every day via CronTrigger.
│   │                               # start_scheduler() and stop_scheduler() are called
│   │                               # by the FastAPI lifespan context in main.py.
│   │
│   └── api/routes/                 # HTTP route handlers (thin layer, calls services)
│       │
│       ├── auth.py                 # POST /api/auth/register — creates User + empty
│       │                           # Territory record, hashes password with bcrypt,
│       │                           # returns JWT so user is immediately logged in.
│       │                           # POST /api/auth/login — verifies bcrypt password,
│       │                           # returns JWT token on success.
│       │
│       ├── runs.py                 # POST /api/runs/ — saves Run record, calls
│       │                           # expand_territory(), calls check_and_apply_conquest(),
│       │                           # returns full game state update in one response.
│       │                           # GET /api/runs/ — paginated run history.
│       │                           # GET /api/runs/stats — aggregated personal stats.
│       │
│       ├── map.py                  # GET /api/map/territories — all active territories
│       │                           # for rendering the world map. Supports lat/lng/radius
│       │                           # filter so mobile apps load only nearby kingdoms.
│       │                           # GET /api/map/leaderboard — top N players by area.
│       │                           # GET /api/map/my-territory — current user's territory.
│       │
│       └── users.py                # GET /api/users/me — full profile with territory.
│                                   # GET /api/users/{username} — any player's public profile.
│
├── tests/
│   └── test_territory_engine.py    # Unit tests for all core game logic.
│                                   # Covers: circle area, Haversine distance, overlap
│                                   # detection, territory gain calc, streak bonus,
│                                   # kingdom level thresholds, color generation.
│
├── scripts/
│   ├── seed.py                     # Populates DB with 5 sample players spread across
│   │                               # Indian cities (Delhi, Mumbai, Bangalore, Hyderabad,
│   │                               # Chennai) with pre-built territories.
│   │
│   └── migrations_guide.py         # Instructions for setting up Alembic migrations
│                                   # for managing future database schema changes.
│
├── requirements.txt                # All Python dependencies with pinned versions
├── .env.example                    # Template showing every environment variable
├── .gitignore                      # Excludes venv/, .env, __pycache__, etc.
├── LICENSE                         # MIT License
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** → https://python.org/downloads
- **PostgreSQL 15+** with **PostGIS** → https://postgresql.org/download
- **Redis** → https://redis.io/download
- **Git** → https://git-scm.com/downloads

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/fitkingdom.git
cd fitkingdom
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

```sql
CREATE DATABASE fitkingdom;
\c fitkingdom
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 5. Configure environment

```bash
cp .env.example .env   # then open .env and fill in your values
```

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/fitkingdom
SECRET_KEY=any-long-random-string-you-choose
REDIS_URL=redis://localhost:6379/0
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

### 7. Open API docs

**http://localhost:8000/docs**

### 8. Load sample data (optional)

```bash
python scripts/seed.py
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🔌 API Reference

All protected endpoints `🔒` require: `Authorization: Bearer <token>`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | ❌ | Create account, returns JWT token |
| `POST` | `/api/auth/login` | ❌ | Login, returns JWT token |
| `POST` | `/api/runs/` | 🔒 | Log a run → expand territory + conquest check |
| `GET` | `/api/runs/` | 🔒 | Your run history (paginated) |
| `GET` | `/api/runs/stats` | 🔒 | Personal stats (km, streak, best run) |
| `GET` | `/api/map/territories` | ❌ | All territories for world map rendering |
| `GET` | `/api/map/leaderboard` | ❌ | Top players ranked by territory area |
| `GET` | `/api/map/my-territory` | 🔒 | Your current territory details |
| `GET` | `/api/users/me` | 🔒 | Your full profile |
| `GET` | `/api/users/{username}` | ❌ | Any player's public profile |

Full interactive documentation available at `/docs` (Swagger UI) and `/redoc`.

---

## ⚙️ Configuration

All game balance is tunable via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `KM_PER_TERRITORY_RADIUS` | `1.0` | Territory radius gain per km run |
| `DAILY_DECAY_PERCENT` | `10` | % territory lost per inactive day |
| `MAX_TERRITORY_RADIUS_KM` | `50` | Maximum allowed territory radius |
| `STREAK_BONUS_MULTIPLIER` | `1.5` | Territory gain multiplier at 7-day streak |
| `CONQUEST_OVERLAP_THRESHOLD` | `0.3` | Overlap fraction needed to trigger conquest |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | JWT validity period (7 days) |

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| `venv\Scripts\activate` fails | Run PowerShell as admin: `Set-ExecutionPolicy RemoteSigned` |
| `psycopg2` install error | Use `pip install psycopg2-binary` instead |
| `Database connection refused` | Start the PostgreSQL service in Windows Services |
| `Redis connection refused` | Start the Redis service in Windows Services |
| `Port 8000 already in use` | Run with `--port 8001` flag |
| `ModuleNotFoundError` | Make sure `(venv)` is showing in your terminal |

---

## 🗺️ Roadmap

### ✅ Completed
- [x] Core territory engine (expand, decay, conquer)
- [x] JWT authentication (register + login)
- [x] Geospatial territory overlap detection using Haversine formula
- [x] Daily decay background scheduler (midnight cron)
- [x] Streak bonus system (7-day = 1.5× multiplier)
- [x] Kingdom level progression (Village → Empire)
- [x] Global leaderboard ranked by area
- [x] World map API with location-based filtering
- [x] Personal run analytics and stats
- [x] Unit tests for all game logic
- [x] Database seed script with sample players

### 🔜 Coming Soon
- [ ] **Strava OAuth** — import real GPS runs automatically
- [ ] **WebSocket live map** — see territory changes in real time
- [ ] **Alliance system** — team territories with shared defense
- [ ] **Weekly Battle Royale** — 2× decay for 24 hours
- [ ] **Push notifications** — Firebase FCM alerts on conquest
- [ ] **Raid mechanic** — target a specific player's territory
- [ ] **React + Mapbox GL JS frontend** — visual map UI
- [ ] **Docker + docker-compose** — one-command startup
- [ ] **Cloud deployment** — Railway / Render hosting

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/alliance-system`
3. Commit your changes: `git commit -m "feat: add alliance system"`
4. Push to the branch: `git push origin feature/alliance-system`
5. Open a Pull Request

Please ensure `pytest tests/ -v` passes before submitting.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)

---

<div align="center">
Built with ❤️ and a lot of running 🏃
<br><br>
If this project helped you, please give it a ⭐ on GitHub!
</div>
