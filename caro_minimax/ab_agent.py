"""Tác nhân MiniMax / Alpha-Beta cho Caro 9x9 (phần B).

- MiniMaxAgent và AlphaBetaAgent dùng CHUNG hàm đánh giá, danh sách ứng viên và thứ tự duyệt,
  chỉ khác nhau ở việc có cắt tỉa hay không -> so sánh số nút / thời gian công bằng.
- Mã giả tương ứng: Thuật toán 2.1, 2.2, 3.1, 3.2 trong báo cáo; bảng điểm: Bảng 3.1.
"""
import math
import time

EMPTY = 0
WIN = 1_000_000
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))

# Bảng 3.1 — (độ dài chuỗi, số đầu mở) -> điểm
RUN_SCORE = {
    (4, 2): 100_000, (4, 1): 10_000,
    (3, 2): 5_000, (3, 1): 500,
    (2, 2): 200, (2, 1): 20,
    (1, 2): 5, (1, 1): 1,
}
# Mẫu có khe (X = quân mình, _ = trống)
GAP_PATTERNS = (("XX_XX", 10_000), ("X_XXX", 10_000), ("XXX_X", 10_000),
                ("_XX_X_", 3_000), ("_X_XX_", 3_000))


def opponent(p):
    return 3 - p


# ======================================================================
# 1. Hàm đánh giá
# ======================================================================
_LINES = {}


def board_lines(n):
    """Mọi đường (ngang, dọc, 2 chéo) dài >= 5 ô, mỗi đường là list các (r, c)."""
    if n not in _LINES:
        lines = []
        for dr, dc in DIRS:
            for r in range(n):
                for c in range(n):
                    pr, pc = r - dr, c - dc
                    if 0 <= pr < n and 0 <= pc < n:
                        continue  # (r, c) không phải ô đầu của đường
                    line, rr, cc = [], r, c
                    while 0 <= rr < n and 0 <= cc < n:
                        line.append((rr, cc))
                        rr += dr
                        cc += dc
                    if len(line) >= 5:
                        lines.append(line)
        _LINES[n] = lines
    return _LINES[n]


def _count_overlapping(s, pat):
    count, i = 0, s.find(pat)
    while i != -1:
        count += 1
        i = s.find(pat, i + 1)
    return count


def score_line(s):
    """s: chuỗi theo góc nhìn một người chơi, đã đệm 'O' hai đầu ('X' mình, 'O' địch/biên, '_' trống)."""
    total, i, n = 0, 0, len(s)
    while i < n:
        if s[i] != "X":
            i += 1
            continue
        j = i
        while s[j] == "X":
            j += 1
        length = j - i
        if length >= 5:
            return WIN
        opens = (s[i - 1] == "_") + (s[j] == "_")
        total += RUN_SCORE.get((length, opens), 0)
        i = j
    for pat, val in GAP_PATTERNS:
        total += val * _count_overlapping(s, pat)
    return total


_TRANS = {
    1: str.maketrans({"1": "X", "2": "O", "0": "_"}),
    2: str.maketrans({"2": "X", "1": "O", "0": "_"}),
}


def player_score(board, p):
    """Score(s, p): tổng điểm các chuỗi quân của người chơi p trên mọi đường."""
    total = 0
    for line in board_lines(len(board)):
        raw = "".join(str(board[r][c]) for r, c in line)
        total += score_line("O" + raw.translate(_TRANS[p]) + "O")
    return total


def evaluate(board, ai, w=1.2):
    """Công thức (3.1): Eval(s) = Score(AI) - w * Score(đối thủ)."""
    return player_score(board, ai) - w * player_score(board, opponent(ai))


# ======================================================================
# 2. Sinh và sắp xếp ứng viên (Thuật toán 3.1)
# ======================================================================
def _local_run(board, r, c, p, dr, dc):
    """Độ dài chuỗi đi qua (r, c) nếu p đặt quân tại đó, và số đầu mở."""
    n, length, opens = len(board), 1, 0
    for s in (1, -1):
        rr, cc = r + s * dr, c + s * dc
        while 0 <= rr < n and 0 <= cc < n and board[rr][cc] == p:
            length += 1
            rr += s * dr
            cc += s * dc
        if 0 <= rr < n and 0 <= cc < n and board[rr][cc] == EMPTY:
            opens += 1
    return length, opens


def makes_five(board, r, c, p):
    return any(_local_run(board, r, c, p, dr, dc)[0] >= 5 for dr, dc in DIRS)


def point_score(board, r, c, p):
    """Điểm mẫu mà p tạo ra nếu đặt quân tại (r, c)."""
    total = 0
    for dr, dc in DIRS:
        length, opens = _local_run(board, r, c, p, dr, dc)
        if length >= 5:
            return WIN
        total += RUN_SCORE.get((length, opens), 0)
    return total


def candidates(state, radius=2, top_k=12):
    board = state.board
    n = len(board)
    me = state.current_player
    opp = opponent(me)
    stones = [(r, c) for r in range(n) for c in range(n) if board[r][c] != EMPTY]
    if not stones:
        return [(n // 2, n // 2)]
    near = set()
    for r, c in stones:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < n and 0 <= cc < n and board[rr][cc] == EMPTY:
                    near.add((rr, cc))
    near = sorted(near)  # cố định thứ tự khi đồng điểm -> kết quả tái lập được
    wins = [m for m in near if makes_five(board, *m, me)]
    if wins:
        return wins
    blocks = [m for m in near if makes_five(board, *m, opp)]
    if blocks:
        return blocks
    near.sort(key=lambda m: -(point_score(board, *m, me) + point_score(board, *m, opp)))
    return near[:top_k]


# ======================================================================
# 3. Lõi tìm kiếm (Thuật toán 2.1, 2.2) — độc lập với trò chơi
# ======================================================================
class Searcher:
    """moves(s) -> list nước; apply(s, m) -> trạng thái con;
    terminal(s, d) -> giá trị nếu s kết thúc, ngược lại None; evaluate(s) -> số."""

    def __init__(self, moves, apply, terminal, evaluate):
        self.moves, self.apply, self.terminal, self.evaluate = moves, apply, terminal, evaluate
        self.reset()

    def reset(self):
        self.nodes = self.leaves = self.cutoffs = 0

    def _leaf(self, s, d):
        t = self.terminal(s, d)
        if t is not None:
            self.leaves += 1
            return t
        if d == 0:
            self.leaves += 1
            return self.evaluate(s)
        return None

    def minimax(self, s, d, is_max):
        self.nodes += 1
        leaf = self._leaf(s, d)
        if leaf is not None:
            return leaf
        if is_max:
            v = -math.inf
            for m in self.moves(s):
                v = max(v, self.minimax(self.apply(s, m), d - 1, False))
        else:
            v = math.inf
            for m in self.moves(s):
                v = min(v, self.minimax(self.apply(s, m), d - 1, True))
        return v

    def alphabeta(self, s, d, alpha, beta, is_max):
        self.nodes += 1
        leaf = self._leaf(s, d)
        if leaf is not None:
            return leaf
        if is_max:
            v = -math.inf
            for m in self.moves(s):
                v = max(v, self.alphabeta(self.apply(s, m), d - 1, alpha, beta, False))
                alpha = max(alpha, v)
                if alpha >= beta:
                    self.cutoffs += 1
                    break  # cắt beta
        else:
            v = math.inf
            for m in self.moves(s):
                v = min(v, self.alphabeta(self.apply(s, m), d - 1, alpha, beta, True))
                beta = min(beta, v)
                if alpha >= beta:
                    self.cutoffs += 1
                    break  # cắt alpha
        return v

    def best_move(self, s, d, pruning=True):
        """Thuật toán 3.2: duyệt các con của gốc (MAX), trả về (nước, giá trị)."""
        self.reset()
        self.nodes += 1
        best, best_v = None, -math.inf
        for m in self.moves(s):
            child = self.apply(s, m)
            if pruning:
                v = self.alphabeta(child, d - 1, best_v, math.inf, False)
            else:
                v = self.minimax(child, d - 1, False)
            if v > best_v or best is None:
                best, best_v = m, v
        return best, best_v


# ======================================================================
# 4. Tác nhân cho Caro
# ======================================================================
class AlphaBetaAgent:
    name = "AlphaBeta"
    pruning = True

    def __init__(self, depth=2, radius=2, top_k=12, defense_weight=1.2):
        if depth < 1:
            raise ValueError("depth phải >= 1")
        self.depth, self.radius, self.top_k, self.w = depth, radius, top_k, defense_weight

    def config(self):
        return {"depth": self.depth, "radius": self.radius, "top_k": self.top_k, "w": self.w}

    def choose_move(self, state):
        """Trả về (nước đi, thống kê). Không sửa `state`."""
        if state.is_terminal():
            raise ValueError("Ván đã kết thúc")
        ai = state.current_player
        opp = opponent(ai)

        def terminal(s, d):
            if not s.is_terminal():
                return None
            if s.winner == ai:
                return WIN + d  # thắng càng sớm (d còn lớn) càng tốt
            if s.winner == opp:
                return -(WIN + d)  # thua càng muộn càng đỡ
            return 0

        searcher = Searcher(
            moves=lambda s: candidates(s, self.radius, self.top_k),
            apply=lambda s, m: s.apply(m),
            terminal=terminal,
            evaluate=lambda s: evaluate(s.board, ai, self.w),
        )
        t0 = time.perf_counter()
        move, value = searcher.best_move(state, self.depth, pruning=self.pruning)
        elapsed = (time.perf_counter() - t0) * 1000
        stats = {
            "agent": self.name, **self.config(),
            "value": value, "nodes": searcher.nodes, "leaves": searcher.leaves,
            "cutoffs": searcher.cutoffs, "time_ms": round(elapsed, 3),
        }
        return move, stats


class MiniMaxAgent(AlphaBetaAgent):
    """MiniMax thường (không cắt tỉa) — dùng để đối chứng."""
    name = "MiniMax"
    pruning = False
