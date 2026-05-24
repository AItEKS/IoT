from pydantic import BaseModel

class GameStartRequest(BaseModel):
    player_black_id: str = "stand-black-mock"
    scenario: str = "realistic_mate"

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True
        from_attributes = True 

class Token(BaseModel):
    access_token: str
    token_type: str

class StandPinRequest(BaseModel):
    stand_id: str
    pin_code: str

class StandActivateRequest(BaseModel):
    pin_code: str

class StandResponse(BaseModel):
    id: str
    owner_id: int | None
    
    class Config:
        from_attributes = True
    
class GameInfoResponse(BaseModel):
    game_id: str
    white_id: str
    black_id: str
    status: str