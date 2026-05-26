 # --- Настройки Сети ---
BROKER_ADDRESS = "localhost"  # IP, где поднят docker-compose
BROKER_PORT = 1883
API_BASE_URL = "http://localhost:8000" # URL FastAPI бэкенда

# --- Идентификация Стенда ---
STAND_ID = "hw_stand_001"
PIN_CODE = "1234"  # Пин-код для привязки в Dashboard лобби

# --- Настройки Pygame ---
FPS = 30
SQUARE_SIZE = 75

CELL_PADDING = 5      # Размер черного отступа вокруг клетки (в пикселях)
INDICATOR_WIDTH = 2   # Ширина индикатора в количестве столбцов
# Пересчитываем ширину экрана: 8 клеток + 2 клетки индикатора
SCREEN_WIDTH = (8 + INDICATOR_WIDTH) * SQUARE_SIZE 
SCREEN_HEIGHT = 8 * SQUARE_SIZE