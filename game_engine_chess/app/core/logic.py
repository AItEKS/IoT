import chess
from typing import Dict, List, Any, Optional, Set

class ChessGame:
    def __init__(self, white_stand_id: str, black_stand_id: str):
        self.board = chess.Board()
        self.white_stand_id = white_stand_id
        self.black_stand_id = black_stand_id
        self.raw_matrices = {self.white_stand_id: [], self.black_stand_id: []}
        self.reported_stands = set()
        self.is_initialized = False
        self.state = "PLAYING"
        self.error_highlights = []
        self.available_moves_highlights = []
        
        self.raw_to_chess = {1: chess.PAWN, 2: chess.KNIGHT, 3: chess.BISHOP, 5: chess.QUEEN, 6: chess.KING, 9: chess.ROOK}
        self.chess_to_raw = {v: k for k, v in self.raw_to_chess.items()}

    def update_stand_state(self, stand_id: str, matrix: List[Dict[str, Any]]) -> bool:
        if stand_id not in [self.white_stand_id, self.black_stand_id]:
            return False
        
        self.raw_matrices[stand_id] = matrix
        self.reported_stands.add(stand_id)
        
        # Флаг принудительного обновления для первого кадра
        is_first_init = False
        if not self.is_initialized:
            if len(self.reported_stands) >= 2:
                self.is_initialized = True
                is_first_init = True
                print(f"[ENGINE] Connection established with {self.white_stand_id} and {self.black_stand_id}")
            else:
                return False

        if self.state == "GAME_OVER": return False

        phys_board = self._get_physical_board()
        missing, extra = self._compare_boards_selective(phys_board)

        # Если ошибок нет
        if not missing and not extra:
            if self.state in ["DESYNC", "PIECE_LIFTED"] or is_first_init:
                self.state = "PLAYING"
                self.error_highlights = []
                self.available_moves_highlights = []
                return True # Триггерим отправку на фронтенд
            return False

        # 1. Ход или взятие
        if (len(missing) in [1, 2]) and len(extra) == 1:
            m_sqs = list(missing.keys())
            to_sq = list(extra.keys())[0]
            from_sq = next((sq for sq in m_sqs if sq != to_sq), m_sqs[0])
            if self._try_apply_move(from_sq, to_sq):
                self.state = "GAME_OVER" if self.board.is_game_over() else "PLAYING"
                self.error_highlights = []
                self.available_moves_highlights = []
                return True

        # 2. Поднята фигура
        if len(missing) == 1 and not extra:
            sq = list(missing.keys())[0]
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn:
                self.state = "PIECE_LIFTED"
                self._generate_available_moves(sq)
                return True

        # 3. Ошибка расстановки
        self.state = "DESYNC"
        self.available_moves_highlights = []
        self._generate_desync_highlights(missing, extra)
        return True

    def _get_physical_board(self):
        phys = {}
        # Белые (только ID < 10)
        for m in self.raw_matrices.get(self.white_stand_id, []):
            coords = m.get('cords')
            mid = m.get('id')
            if coords and len(coords) == 2 and mid < 10:
                pt = self.raw_to_chess.get(mid)
                if pt: phys[chess.square(coords[1], coords[0])] = chess.Piece(pt, chess.WHITE)
        # Черные (только ID >= 11)
        for m in self.raw_matrices.get(self.black_stand_id, []):
            coords = m.get('cords')
            mid = m.get('id')
            if coords and len(coords) == 2 and mid >= 11:
                pt = self.raw_to_chess.get(mid - 10)
                if pt: phys[chess.square(coords[1], coords[0])] = chess.Piece(pt, chess.BLACK)
        return phys

    def _compare_boards_selective(self, phys):
        missing, extra = {}, {}
        for sq in chess.SQUARES:
            v, p = self.board.piece_at(sq), phys.get(sq)
            if v != p:
                if v: missing[sq] = v
                if p: extra[sq] = p
        return missing, extra

    def _try_apply_move(self, f, t):
        move = chess.Move(f, t)
        p = self.board.piece_at(f)
        if p and p.piece_type == chess.PAWN and chess.square_rank(t) in [0, 7]: move.promotion = chess.QUEEN
        if move in self.board.legal_moves:
            self.board.push(move)
            print(f"[ENGINE] MOVE: {move.uci()}")
            return True
        return False

    def get_visual_state(self):
        board_matrix = [[{} for _ in range(8)] for _ in range(8)]
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                r, c = chess.square_rank(square), chess.square_file(square)
                board_matrix[r][c] = {"piece": self.chess_to_raw.get(piece.piece_type), "color": "white" if piece.color == chess.WHITE else "black"}
        res = {"is_white_turn": self.board.turn == chess.WHITE, "fen": self.board.fen(), "engine_state": self.state, "board": board_matrix, 
               "game_status": "mate" if self.board.is_checkmate() else "playing"}
        status = self.error_highlights + (self.available_moves_highlights if self.state == "PIECE_LIFTED" else [])
        if self.board.is_check():
            ksq = self.board.king(self.board.turn)
            status.append({"square": [chess.square_rank(ksq), chess.square_file(ksq)], "description": "check"})
        res["status"] = status
        return res

    def _generate_available_moves(self, sq):
        self.available_moves_highlights = [{"square": [chess.square_rank(m.to_square), chess.square_file(m.to_square)], "description": "availble moves"} for m in self.board.legal_moves if m.from_square == sq]

    def _generate_desync_highlights(self, m, e):
        self.error_highlights = [{"square": [chess.square_rank(s), chess.square_file(s)], "description": "wrongmove"} for s in e] + \
                                [{"square": [chess.square_rank(s), chess.square_file(s)], "description": "missing_piece"} for s in m]