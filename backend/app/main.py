
"""FastAPI Main Application with WebSockets."""
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

from .agent.state import AgentSession, Stage
from .agent.orchestrator import handle_user_message_stream

app = FastAPI(title="AI Car Matchmaker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, AgentSession] = {}
chat_histories: dict[str, list[dict]] = {}

class BookingRequest(BaseModel):
    session_id: str
    listing_id: str
    full_name: str
    email: str
    phone: str

@app.websocket("/api/chat/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if session_id not in sessions:
        sessions[session_id] = AgentSession(session_id=session_id)

    session = sessions[session_id]

    try:
        while True:
            user_message = await websocket.receive_text()
            print(f"-> [WebSocket] User message: {user_message}")

            response_text = ""
            # Stream chunks from orchestrator directly
            async for chunk in handle_user_message_stream(session, user_message):
                response_text += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "text": chunk
                })

            # Send final state so frontend updates Live Specs & Matches panel
            await websocket.send_json({
                "type": "state",
                "session": session.model_dump()
            })

    except WebSocketDisconnect:
        print(f"-> [WebSocket] Disconnected: {session_id}")


@app.post("/api/book")
def book_listing(req: BookingRequest):
    """Handles vehicle booking."""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[req.session_id]

    session.selected_listing_id = req.listing_id
    session.stage = Stage.DONE
    return {"status": "success", "session": session.model_dump()}


@app.post("/api/checkout/confirm")
async def process_mock_payment(car_id: str, request: Request, session_id: str | None = None):
    """Mock endpoint to handle the MCP App form submission.

    session_id is optional (added as a query param by trigger_checkout_app
    in mcp_server.py) so this stays backward-compatible if it's ever
    missing - it just won't be able to update agent state in that case.
    """
    form_data = await request.json()

    if session_id and session_id in sessions:
        session = sessions[session_id]
        session.selected_listing_id = car_id
        session.payment_status = "confirmed"
        session.stage = Stage.DONE
        session.log(f"Mock payment confirmed for listing {car_id}. Booking complete.")

    return JSONResponse(content={
        "status": "success",
        "transaction_id": f"txn_{car_id}_84729",
        "message": f"Payment successful! Your vehicle has been secured for {form_data.get('name', 'you')}."
    })