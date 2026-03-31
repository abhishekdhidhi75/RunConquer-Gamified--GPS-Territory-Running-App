"""
RunConquer — FastAPI Backend Entry Point
Gamified territory running app.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import init_db
from app.routers import auth, runs, territories, leaderboard
from app.routers import analytics

# Initialize FastAPI
app = FastAPI(
    title="RunConquer API",
    description="Gamified territory running — conquer the world one run at a time",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(territories.router, prefix="/api/territories", tags=["Territories"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics (ML)"])


@app.on_event("startup")
async def startup():
    init_db()
    print("🏃 RunConquer API is ready!")


# Serve frontend pages
@app.get("/", include_in_schema=False)
async def serve_landing():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "index.html"))


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "dashboard.html"))


@app.get("/map", include_in_schema=False)
async def serve_map():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "map.html"))


@app.get("/leaderboard", include_in_schema=False)
async def serve_leaderboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "leaderboard.html"))


@app.get("/login", include_in_schema=False)
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "login.html"))


@app.get("/register", include_in_schema=False)
async def serve_register():
    return FileResponse(os.path.join(FRONTEND_DIR, "templates", "register.html"))
