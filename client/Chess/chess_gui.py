# chess_gui.py
import pygame
import sys
import numpy as np

class ChessRenderer:
    def __init__(self, config):
        pygame.init()
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(f"AR Chess Client - {config.STAND_ID}")
        self.clock = pygame.time.Clock()
        
        fonts = 'segoeuisymbol,dejavusans,freeserif,arial'
        self.font = pygame.font.SysFont(fonts, int(config.SQUARE_SIZE * 0.7))
        
        # Стартовая позиция (стандартная FEN)
        self.update_board_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",'w')
        
        self.pieces_unicode = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }

    def _rotate_board_layout(self, board):
        """
        1. Поворачиваем доску на 90 градусов (белые налево, черные направо).
        2. Отражаем по горизонтали, чтобы инвертировать порядок фигур (Король <-> Ферзь).
        """
        arr = np.array(board)
        
        # 1. Поворот (transpose + flip) для перевода белых влево
        # np.rot90(arr, k=-1) это поворот на 90 град по часовой
        rotated = np.rot90(arr, k=1)
        
        # 2. Отражаем по горизонтали (ось 1), чтобы "зеркально" поменять местами 
        # фигуры, стоящие на линии (включая короля и ферзя)
        mirrored = np.fliplr(rotated)
        
        return mirrored.tolist()

    def update_board_from_fen(self, fen, active_color):
        raw_board = self._fen_to_board(fen)
        self.board_state = self._rotate_board_layout(raw_board)
        self.active_color = active_color # Теперь индикатор будет знать, чей ход

    def _fen_to_board(self, fen):
        """Вспомогательная функция: FEN -> 2D Массив 8x8"""
        board = []
        rows = fen.split(' ')[0].split('/')
        for row in rows:
            board_row = []
            for char in row:
                if char.isdigit():
                    board_row.extend(['.'] * int(char))
                else:
                    board_row.append(char)
            board.append(board_row)
        return board

    def draw_board(self):
        sq_sz = self.config.SQUARE_SIZE
        padding = self.config.CELL_PADDING
        
        # 1. Отрисовка основной доски (8x8)
        for row in range(8):
            for col in range(8):
                # Рисуем черный фон (паддинг)
                rect_x = col * sq_sz
                rect_y = row * sq_sz
                pygame.draw.rect(self.screen, (0, 0, 0), (rect_x, rect_y, sq_sz, sq_sz))
                
                # Рисуем клетку внутри паддинга
                cell_color = (238, 238, 210) if (row + col) % 2 == 0 else (118, 150, 86)
                inner_rect = pygame.Rect(
                    rect_x + padding, 
                    rect_y + padding, 
                    sq_sz - 2 * padding, 
                    sq_sz - 2 * padding
                )
                pygame.draw.rect(self.screen, cell_color, inner_rect)
                
                # Рисуем фигуру
                piece = self.board_state[row][col]
                if piece != '.':
                    char = self.pieces_unicode.get(piece, piece)
                    text_surface = self.font.render(char, True, (0, 0, 0))
                    text_rect = text_surface.get_rect(center=inner_rect.center)
                    self.screen.blit(text_surface, text_rect)

        # 2. Отрисовка индикатора хода справа
        # Предположим, текущий ход приходит в self.active_color ('w' или 'b')
        indicator_x = 8 * sq_sz
        indicator_width = self.config.INDICATOR_WIDTH * sq_sz
        
        color = (255, 255, 255) if getattr(self, 'active_color', 'w') == 'w' else (50, 50, 50)
        pygame.draw.rect(self.screen, color, (indicator_x, 0, indicator_width, self.config.SCREEN_HEIGHT))
        self.draw_pin_code()

    def render_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        self.draw_board()
        pygame.display.flip()
        self.clock.tick(self.config.FPS)

    def draw_pin_code(self):
        # 1. Рендерим текст на обычной поверхности
        # Используем жирный шрифт для красоты
        pin_font = pygame.font.SysFont('arial', int(self.config.SQUARE_SIZE * 0.5), bold=True)
        text_surf = pin_font.render(f"PIN: {self.config.PIN_CODE}", True, (255, 255, 0)) # Желтый цвет
        
        # 2. Поворачиваем поверхность на 90 градусов (против часовой)
        rotated_text = pygame.transform.rotate(text_surf, 90)
        
        # 3. Вычисляем позицию в центре индикатора
        indicator_x = 8 * self.config.SQUARE_SIZE
        indicator_width = self.config.INDICATOR_WIDTH * self.config.SQUARE_SIZE
        indicator_center_x = indicator_x + (indicator_width // 2)
        indicator_center_y = self.config.SCREEN_HEIGHT // 2
        
        # Центрируем повернутый текст
        text_rect = rotated_text.get_rect(center=(indicator_center_x, indicator_center_y))
        
        # 4. Рисуем поверх индикатора
        self.screen.blit(rotated_text, text_rect)
