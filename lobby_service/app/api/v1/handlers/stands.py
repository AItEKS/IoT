from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1 import schemas
from app.api.deps import get_db, get_current_user
from app.db.models import User, Stand

router = APIRouter()

@router.post("/register-pin", response_model=schemas.StandResponse)
async def register_stand_pin(request: schemas.StandPinRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stand).filter(Stand.id == request.stand_id))
    stand = result.scalars().first()
    
    if not stand:
        stand = Stand(id=request.stand_id, pin_code=request.pin_code)
        db.add(stand)
    else:
        stand.pin_code = request.pin_code
        
    await db.commit()
    await db.refresh(stand)
    return stand

@router.post("/activate", response_model=schemas.StandResponse)
async def activate_stand(
    request: schemas.StandActivateRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Stand).filter(Stand.pin_code == request.pin_code))
    stand = result.scalars().first()
    
    if not stand:
        raise HTTPException(status_code=404, detail="Неверный ПИН-код")
        
    if stand.owner_id is not None:
        raise HTTPException(status_code=400, detail="Стенд уже занят")

    stand.owner_id = current_user.id
    stand.pin_code = None
    
    await db.commit()
    await db.refresh(stand)
    return stand

@router.get("/my", response_model=list[schemas.StandResponse])
async def get_my_stands(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stand).filter(Stand.owner_id == current_user.id))
    return result.scalars().all()