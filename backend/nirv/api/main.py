from fastapi import FastAPI

from nirv.api.routes import account, agents, analysis, health, journal, market, trades, voice

app = FastAPI(title="Nirv API", version="0.1.0", description="AI-assisted XAUUSD trading orchestration in paper mode.")
app.include_router(health.router)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(trades.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(journal.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
