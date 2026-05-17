from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

from app.api.v1.handlers import games, auth, stands
from app.services.mqtt_listener import lobby_mqtt

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Lobby Service запущен и готов к работе.")
    lobby_mqtt.connect_and_start()

    yield
    
    print("Lobby Service остановлен.")
    lobby_mqtt.stop()

app = FastAPI(title="AR Game Lobby Service", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(stands.router, prefix="/api/v1/stands", tags=["Stands"]) 
app.include_router(games.router, prefix="/api/v1/games", tags=["Games"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    """Простая проверка работоспособности сервиса."""
    return {"status": "ok"}