import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from nirv.api.routes import account, agents, analysis, controls, health, journal, market, trades, voice

app = FastAPI(title="Nirv API", version="0.1.0", description="AI-assisted XAUUSD trading orchestration in paper mode.")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
	allow_credentials=False,
	allow_methods=["DELETE", "GET", "POST"],
	allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(trades.router, prefix="/api/v1")
app.include_router(account.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(journal.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(controls.router, prefix="/api/v1")


@app.websocket("/api/v1/agents/stream")
async def agent_stream(websocket: WebSocket) -> None:
	await websocket.accept()
	try:
		while True:
			await websocket.send_json({"event": "HEARTBEAT", "agents": await agents.list_agents()})
			await asyncio.sleep(5)
	except (WebSocketDisconnect, RuntimeError):
		return
