import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.game_orchestrator import orchestrator
from app.api.deps import get_current_user, get_db
from app.db.models import User, Stand

router = APIRouter()

class InviteRequest(BaseModel):
    opponent_username: str
    scenario: str = "normal_game"
    use_mocks: bool = False

@router.post("/invite")
async def invite_to_game(request: InviteRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res_opp = await db.execute(select(User).filter(User.username == request.opponent_username))
    opponent = res_opp.scalars().first()
    if not opponent: raise HTTPException(404, "Opponent not found")

    if request.use_mocks:
        w_id = f"mock-w-{current_user.id}"
        b_id = f"mock-b-{opponent.id}"
    else:
        res_w = await db.execute(select(Stand).filter(Stand.owner_id == current_user.id))
        res_b = await db.execute(select(Stand).filter(Stand.owner_id == opponent.id))
        w_stand, b_stand = res_w.scalars().first(), res_b.scalars().first()
        if not w_stand or not b_stand: raise HTTPException(400, "Stands not linked")
        w_id, b_id = w_stand.id, b_stand.id

    if orchestrator.is_stand_busy(w_id) or orchestrator.is_stand_busy(b_id):
        raise HTTPException(400, "One of the stands is busy")

    game_id = f"game-{uuid.uuid4().hex[:8]}"
    orchestrator.start_game(game_id, w_id, b_id, request.scenario, request.use_mocks)

    from app.services.mqtt_listener import lobby_mqtt
    lobby_mqtt.client.publish(f"notifications/user_{opponent.id}", json.dumps({"action": "game_started", "game_id": game_id}))
    
    return {"status": "success", "game_id": game_id}

@router.get("/active")
async def get_active_games():
    return [{"game_id": k, "status": "Live"} for k in orchestrator.active_processes.keys()]

@router.post("/{game_id}/surrender")
async def surrender_game(game_id: str, current_user: User = Depends(get_current_user)):
    orchestrator.stop_game(game_id, reason="aborted")
    return {"status": "success"}