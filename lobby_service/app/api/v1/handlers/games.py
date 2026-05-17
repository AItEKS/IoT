import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.schemas import GameStartRequest
from app.services.game_orchestrator import orchestrator
from app.api.deps import get_current_user, get_db
from app.db.models import User  

router = APIRouter()

class RealGameStartRequest(BaseModel):
    opponent_username: str
    scenario: str = "normal_game"

@router.post("/start-test")
async def start_test_game(
    request: GameStartRequest, 
    current_user: User = Depends(get_current_user)
):
    game_id = f"game-{uuid.uuid4().hex[:8]}"
    white_stand_id = f"stand-user-{current_user.username}" 
    
    if orchestrator.is_stand_busy(white_stand_id):
        raise HTTPException(status_code=400, detail="Вы уже в игре!")

    orchestrator.start_test_game(
        game_id=game_id,
        white_id=white_stand_id,
        black_id=request.player_black_id,
        scenario=request.scenario
    )
    
    return {"status": "success", "game_id": game_id}

@router.post("/invite")
async def invite_to_game(
    request: RealGameStartRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Асинхронный поиск
    result = await db.execute(select(User).filter(User.username == request.opponent_username))
    opponent = result.scalars().first()
    
    if not opponent:
        raise HTTPException(status_code=404, detail="Противник не найден")

    white_stand_id = f"stand-user-{current_user.username}"
    black_stand_id = f"stand-user-{opponent.username}"
    
    if orchestrator.is_stand_busy(white_stand_id) or orchestrator.is_stand_busy(black_stand_id):
        raise HTTPException(status_code=400, detail="Один из игроков уже занят")

    game_id = f"game-{uuid.uuid4().hex[:8]}"
    
    orchestrator.start_test_game(
        game_id=game_id,
        white_id=white_stand_id,
        black_id=black_stand_id,
        scenario=request.scenario
    )
    
    return {"status": "success", "game_id": game_id}

@router.get("/active")
async def get_active_games():
    active_games = []
    for game_id in orchestrator.active_processes.keys():
        active_games.append({"game_id": game_id, "status": "В процессе"})
    return active_games

@router.post("/{game_id}/surrender")
async def surrender_game(
    game_id: str, 
    current_user: User = Depends(get_current_user)
):
    if game_id not in orchestrator.active_processes:
        raise HTTPException(status_code=404, detail="Игра не найдена")
        
    game_data = orchestrator.active_processes[game_id]
    my_stand_id = f"stand-user-{current_user.username}"
    
    if my_stand_id not in game_data["stands"]:
        raise HTTPException(status_code=403, detail="Это не ваша игра")
        
    orchestrator.stop_game(game_id, reason="aborted")
    return {"status": "success", "message": "Игра завершена"}