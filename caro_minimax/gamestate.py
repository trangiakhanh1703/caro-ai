"""GameState tạm thời cho Caro 9x9 (để B phát triển/kiểm thử trước khi có bản của A).

Agent chỉ dùng các thuộc tính/phương thức sau — bản GameState của A cần có đúng như vậy
(hoặc viết lớp bọc mỏng):
    state.board            : list[list[int]]  (0 = trống, 1 = X, 2 = O)
    state.current_player   : 1 hoặc 2
    state.winner           : None (chưa xong), 0 (hòa), 1 hoặc 2
    state.is_terminal()    : bool
    state.legal_moves()    : list[(row, col)]
    state.apply(move)      : trả về GameState MỚI, không sửa trạng thái cũ
"""

EMPTY, X, O = 0, 1, 2
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))


class GameState:
    def __init__(self, size=9, board=None, current_player=X, winner=None):
        self.size = size
        self.board = board if board is not None else [[EMPTY] * size for _ in range(size)]
        self.current_player = current_player
        self.winner = winner

    # ---------- truy vấn ----------
    def is_terminal(self):
        return self.winner is not None

    def legal_moves(self):
        if self.is_terminal():
            return []
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == EMPTY]

    # ---------- chuyển trạng thái ----------
    def apply(self, move):
        r, c = move
        if self.is_terminal():
            raise ValueError("Ván đã kết thúc")
        if not (0 <= r < self.size and 0 <= c < self.size) or self.board[r][c] != EMPTY:
            raise ValueError(f"Nước đi không hợp lệ: {move}")
        board = [row[:] for row in self.board]
        p = self.current_player
        board[r][c] = p
        winner = None
        if self._five_through(board, r, c, p):
            winner = p
        elif all(v != EMPTY for row in board for v in row):
            winner = 0
        return GameState(self.size, board, 3 - p, winner)

    def _five_through(self, board, r, c, p):
        n = self.size
        for dr, dc in DIRS:
            count = 1
            for s in (1, -1):
                rr, cc = r + s * dr, c + s * dc
                while 0 <= rr < n and 0 <= cc < n and board[rr][cc] == p:
                    count += 1
                    rr += s * dr
                    cc += s * dc
            if count >= 5:
                return True
        return False

    # ---------- tiện ích cho kiểm thử ----------
    @classmethod
    def from_strings(cls, rows, current_player=X):
        """rows: danh sách chuỗi gồm 'X', 'O', '.'; giả định chưa có ai thắng."""
        m = {"X": X, "O": O, ".": EMPTY}
        board = [[m[ch] for ch in row] for row in rows]
        full = all(v != EMPTY for row in board for v in row)
        return cls(len(board), board, current_player, 0 if full else None)

    def __str__(self):
        sym = {EMPTY: ".", X: "X", O: "O"}
        head = "   " + " ".join(str(c) for c in range(self.size))
        return "\n".join([head] + [f"{r:2} " + " ".join(sym[v] for v in row) for r, row in enumerate(self.board)])
