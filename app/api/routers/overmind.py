# app/api/routers/overmind.py
"""
Overmind Router (Gateway / BFF).
Delegates all logic to the Orchestrator Microservice.
"""

import asyncio
import logging
from typing import Any

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select

from app.api.routers.ws_auth import extract_websocket_auth
from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.domain.mission import Mission, MissionEvent, MissionEventType, MissionStatus
from app.core.domain.user import User
from app.core.event_bus import get_event_bus
from app.services.auth.token_decoder import decode_user_id
from app.services.overmind.domain.api_schemas import (
    MissionCreate,
    MissionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/overmind",
    tags=["Overmind (Super Agent)"],
)

ORCHESTRATOR_URL = "http://orchestrator-service:8000"


async def _call_orchestrator(method: str, path: str, json_data: dict | None = None) -> dict:
    """Helper to call the orchestrator service."""
    async with httpx.AsyncClient() as client:
        try:
            url = f"{ORCHESTRATOR_URL}{path}"
            if method == "POST":
                resp = await client.post(url, json=json_data, timeout=30.0)
            else:
                resp = await client.get(url, timeout=30.0)

            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Orchestrator Service Error: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="Orchestrator Error")
        except Exception as e:
            logger.error(f"Orchestrator Connection Failed: {e}")
            raise HTTPException(status_code=503, detail="Orchestrator Unavailable")


def _get_mission_status_payload(status: str) -> dict:
    if status == "partial_success":
        return {"status": "success", "outcome": "partial_success"}
    return {"status": status, "outcome": None}


@router.post("/missions", response_model=MissionResponse, summary="Launch Mission")
async def create_mission(
    request: MissionCreate,
    background_tasks: BackgroundTasks,
) -> MissionResponse:
    """
    Delegate mission creation to Orchestrator Service.
    """
    # Forward the request payload directly
    payload = {
        "objective": request.objective,
        "context": request.context,
        "initiator_id": 1  # System/Admin
    }

    data = await _call_orchestrator("POST", "/missions", payload)
    return MissionResponse(**data)


@router.get("/missions/{mission_id}", response_model=MissionResponse, summary="Get Mission")
async def get_mission(mission_id: int) -> MissionResponse:
    """
    Delegate mission retrieval to Orchestrator Service.
    """
    data = await _call_orchestrator("GET", f"/missions/{mission_id}")
    return MissionResponse(**data)


@router.websocket("/missions/{mission_id}/ws")
async def stream_mission_ws(
    websocket: WebSocket,
    mission_id: int,
) -> None:
    """
    WebSocket Streaming BFF.
    Subscribes to internal EventBus (fed by Redis Bridge).
    """
    # 1. Auth & Handshake
    token, selected_protocol = extract_websocket_auth(websocket)
    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = decode_user_id(token, get_settings().SECRET_KEY)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await websocket.accept(subprotocol=selected_protocol)

    # 2. Subscribe to Event Bus (Local Queue fed by Redis)
    event_bus = get_event_bus()
    channel = f"mission:{mission_id}"
    event_queue = event_bus.subscribe_queue(channel)

    last_event_id = 0
    terminal_statuses = {"success", "failed", "canceled", "partial_success"}

    try:
        # 3. Initial State (Snapshot)
        # We fetch current state from Service via HTTP for consistency
        try:
            mission_data = await _call_orchestrator("GET", f"/missions/{mission_id}")
            status = mission_data.get("status", "pending")

            payload = _get_mission_status_payload(status)
            await websocket.send_json({"type": "mission_status", "payload": payload})

            if status in terminal_statuses:
                # Still send events just in case? Usually if terminal, we just close.
                # But let's fetch events anyway to show history.
                pass

            # Fetch Historical Events
            events_data = await _call_orchestrator("GET", f"/missions/{mission_id}/events")
            for evt in events_data:
                evt_id = evt.get("id", 0)
                if evt_id > last_event_id:
                    last_event_id = evt_id

                await websocket.send_json({
                    "type": "mission_event",
                    "payload": {
                        "event_type": evt.get("event_type"),
                        "data": evt.get("payload_json")
                    }
                })

            if status in terminal_statuses:
                await websocket.close()
                return

        except Exception as e:
            logger.error(f"Failed to fetch initial state: {e}")
            await websocket.close(code=404)
            return

        # 4. Event Loop
        while True:
            try:
                # Wait for event from Redis Bridge
                raw_event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            except TimeoutError:
                continue

            # Handle Event
            # Expecting Dict from Redis: {"id": 123, "event_type": "...", "payload_json": {...}}
            if isinstance(raw_event, dict):
                event_id = raw_event.get("id", 0)
                event_type = raw_event.get("event_type")
                event_payload = raw_event.get("payload_json", {})

                # Check ordering
                if event_id <= last_event_id:
                    continue
                last_event_id = event_id

                # Forward to Frontend
                await websocket.send_json(
                    {
                        "type": "mission_event",
                        "payload": {
                            "event_type": event_type,
                            "data": event_payload,
                        },
                    }
                )

                # Check Terminal State
                if event_type in ("mission_completed", "mission_failed"):
                     # Fetch final status
                    try:
                        mission_data = await _call_orchestrator("GET", f"/missions/{mission_id}")
                        status = mission_data.get("status")
                        payload = _get_mission_status_payload(status)
                        await websocket.send_json({"type": "mission_status", "payload": payload})
                    except:
                        pass
                    await websocket.close()
                    return

            # Legacy support (if local events still happen)
            elif hasattr(raw_event, "id"):
                if raw_event.id <= last_event_id:
                    continue
                last_event_id = raw_event.id
                await websocket.send_json(
                    {
                        "type": "mission_event",
                        "payload": {
                            "event_type": raw_event.event_type.value,
                            "data": raw_event.payload_json,
                        },
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WS Disconnected: {mission_id}")
    except Exception as e:
        logger.error(f"WS Error: {e}")
        await websocket.close(code=1011)
    finally:
        event_bus.unsubscribe_queue(channel, event_queue)
