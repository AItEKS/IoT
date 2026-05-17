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
        self.lifted_square = None

    def update_stand_state(self, stand_id: str, matrix: List[Dict[str, Any]]) -> bool:
        self.raw_matrices[stand_id] = matrix
        self.reported_stands.add(stand_id)
        
        if not self.is_initialized:
            if len(self.reported_stands) >= 2:
                self.is_initialized = True
                print("[ENGINE] Все стенды на связи. Начинаем мониторинг игры.")
            else:
                return False

        if self.state == "GAME_OVER":
            return False

        phys_board = self._get_physical_board()
        missing, extra = self._compare_boards(phys_board)

        if self.state == "DESYNC":
            if not missing and not extra:
                print("[ENGINE] Рассинхрон устранен. Возврат к игре.")
                self.state = "PLAYING"
                self.error_highlights = []
                return True
            return self._generate_desync_highlights(missing, extra)

        if not missing and not extra:
            if self.state == "PIECE_LIFTED":
                print("[ENGINE] Отмена выбора фигуры.")
                self.state = "PLAYING"
                self._clear_lifted_state()
                return True
            return False

        # 1. Сделан ход или взятие
        # missing может быть 1 (простой ход) или 2 (взятие). extra всегда 1 (фигура на новой клетке)
        if (len(missing) in [1, 2]) and len(extra) == 1:
            to_sq = list(extra.keys())[0]
            # Ищем откуда пошли: это та пропавшая клетка, которая НЕ совпадает с целевой
            from_sq = next((sq for sq in missing.keys() if sq != to_sq), None)
            
            if from_sq and self._try_apply_move(from_sq, to_sq):
                if self.board.is_game_over():
                    print("[ENGINE] ФИНАЛ ИГРЫ! Шах и мат или ничья.")
                    self.state = "GAME_OVER"
                else:
                    self.state = "PLAYING"
                self._clear_lifted_state()
                return True

        # 2. Поднята фигура (1 пропала, нигде не появилась)
        if len(missing) == 1 and not extra:
            sq = list(missing.keys())[0]
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn:
                if self.state != "PIECE_LIFTED":
                    print(f"[ENGINE] Поднята фигура: {chess.square_name(sq)}")
                self.state = "PIECE_LIFTED"
                self.lifted_square = sq
                self._generate_available_moves(sq)
                return True

        # 3. Рассинхрон (каша на доске)
        if len(missing) > 0 or len(extra) > 0:
            print(f"[ENGINE] ОШИБКА РАССТАНОВКИ. Пропало: {len(missing)}, Лишних: {len(extra)}")
            self.state = "DESYNC"
            return self._generate_desync_highlights(missing, extra)

        return False

    def _get_physical_board(self):
        phys = {}
        order = [self.black_stand_id, self.white_stand_id] if self.board.turn == chess.WHITE else [self.white_stand_id, self.black_stand_id]
        for s_id in order:
            for m in self.raw_matrices.get(s_id, []):
                r, c = m.get('cords', [-1, -1])
                mid = m.get('id', 0)
                if 0 <= r <= 7 and 0 <= c <= 7:
                    sq = chess.square(c, r)
                    phys[sq] = chess.Piece(mid if mid <= 10 else mid-10, chess.WHITE if mid <= 10 else chess.BLACK)
        return phys

    def _compare_boards(self, phys):
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
        if p and p.piece_type == chess.PAWN and chess.square_rank(t) in [0, 7]:
            move.promotion = chess.QUEEN
            
        if move in self.board.legal_moves:
            self.board.push(move)
            print(f"[ENGINE] Легальный ход: {move.uci()}")
            return True
        else:
            print(f"[ENGINE] Нелегальный ход: {move.uci()}")
            return False

    def get_visual_state(self):
        res = {"is_white_turn": self.board.turn == chess.WHITE, "fen": self.board.fen(), "engine_state": self.state}
        res["game_status"] = "mate" if self.board.is_checkmate() else "stalemate" if self.board.is_game_over() else "playing"
        
        status = list(self.error_highlights) + self.available_moves_highlights
        if self.board.is_check():
            ksq = self.board.king(self.board.turn)
            status.append({"square": [chess.square_rank(ksq), chess.square_file(ksq)], "description": "check"})
        res["status"] = status
        return res

    def _generate_available_moves(self, sq):
        self.available_moves_highlights = [{"square": [chess.square_rank(m.to_square), chess.square_file(m.to_square)], "description": "availble moves"} for m in self.board.legal_moves if m.from_square == sq]

    def _clear_lifted_state(self):
        self.lifted_square = None
        self.available_moves_highlights = []

    def _generate_desync_highlights(self, m, e):
        self.error_highlights = [{"square": [chess.square_rank(s), chess.square_file(s)], "description": "wrongmove"} for s in e] + \
                                [{"square": [chess.square_rank(s), chess.square_file(s)], "description": "missing_piece"} for s in m]
        return True