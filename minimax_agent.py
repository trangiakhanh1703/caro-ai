"""Tác nhân MiniMax (không cắt tỉa) cho Caro 9 x 9 — phần B.

Module này cũng chứa hàm đánh giá và hàm sinh ứng viên dùng CHUNG với alpha_beta_agent,
để hai bản chỉ khác nhau ở việc có cắt tỉa hay không (so sánh số nút/thời gian công bằng).
Mã giả tương ứng trong báo cáo: Thuật toán 2.1, 3.1, 3.2; bảng điểm: Bảng 3.1.
"""

from random import Random

from game import BOARD_SIZE, EMPTY, GameState, Move, apply_move, get_result, legal_moves

WIN_SCORE = 1_000_000.0
DEFENSE_WEIGHT = 1.2  # w trong Eval = Score(gốc) - w * Score(đối thủ)
CANDIDATE_RADIUS = 2  # chỉ xét ô trống cách quân đã có tối đa 2 ô
DEFAULT_DEPTH = 2
DEFAULT_MAX_CANDIDATES = 12

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))

# Bảng 3.1 — (độ dài chuỗi liên tiếp, số đầu mở) -> điểm
RUN_SCORES = {
    (4, 2): 100_000, (4, 1): 10_000,
    (3, 2): 5_000, (3, 1): 500,
    (2, 2): 200, (2, 1): 20,
    (1, 2): 5, (1, 1): 1,
}
# Mẫu có khe: "X" quân mình, "_" ô trống
GAP_PATTERNS = (
    ("XX_XX", 10_000), ("X_XXX", 10_000), ("XXX_X", 10_000),
    ("_XX_X_", 3_000), ("_X_XX_", 3_000),
)


def _build_lines() -> list[list[Move]]:
    """Mọi đường ngang, dọc, chéo có ít nhất 5 ô."""
    lines = []
    for row_step, col_step in DIRECTIONS:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                prev_row, prev_col = row - row_step, col - col_step
                if 0 <= prev_row < BOARD_SIZE and 0 <= prev_col < BOARD_SIZE:
                    continue  # không phải ô đầu của đường
                line = []
                r, c = row, col
                while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    line.append((r, c))
                    r += row_step
                    c += col_step
                if len(line) >= 5:
                    lines.append(line)
    return lines


LINES = _build_lines()


# ======================================================================
# Hàm đánh giá
# ======================================================================
def _count_overlapping(text: str, pattern: str) -> int:
    count, index = 0, text.find(pattern)
    while index != -1:
        count += 1
        index = text.find(pattern, index + 1)
    return count


def score_line(text: str) -> float:
    """Chấm một đường theo góc nhìn một người chơi.

    text đã đệm "O" ở hai đầu: "X" quân mình, "O" quân địch hoặc biên, "_" ô trống.
    """
    total = 0.0
    i, n = 0, len(text)
    while i < n:
        if text[i] != "X":
            i += 1
            continue
        j = i
        while text[j] == "X":
            j += 1
        length = j - i
        if length >= 5:
            return WIN_SCORE
        open_ends = (text[i - 1] == "_") + (text[j] == "_")
        total += RUN_SCORES.get((length, open_ends), 0)
        i = j
    for pattern, value in GAP_PATTERNS:
        total += value * _count_overlapping(text, pattern)
    return total


def player_score(board: list[list[int]], player: int) -> float:
    """Score(s, p): tổng điểm các chuỗi quân của player trên mọi đường."""
    symbol = {player: "X", EMPTY: "_", -player: "O"}
    total = 0.0
    for line in LINES:
        text = "O" + "".join(symbol[board[r][c]] for r, c in line) + "O"
        total += score_line(text)
    return total


def evaluate_state(state: GameState, root_player: int) -> float:
    """Công thức (3.1): Score(gốc) - w * Score(đối thủ). Dương là có lợi cho quân gốc."""
    return (player_score(state.board, root_player)
            - DEFENSE_WEIGHT * player_score(state.board, -root_player))


def terminal_score(state: GameState, root_player: int, depth_remaining: int) -> float | None:
    """Giá trị trạng thái kết thúc, hoặc None nếu ván chưa kết thúc.

    Cộng depth_remaining để ưu tiên thắng sớm và trì hoãn thua.
    """
    result = get_result(state)
    if result == "ongoing":
        return None
    if result == "draw":
        return 0.0
    winner = 1 if result == "x_win" else -1
    bonus = WIN_SCORE + depth_remaining
    return bonus if winner == root_player else -bonus


# ======================================================================
# Sinh và sắp xếp ứng viên (Thuật toán 3.1)
# ======================================================================
def _local_run(board: list[list[int]], row: int, col: int, player: int,
               row_step: int, col_step: int) -> tuple[int, int]:
    """Độ dài chuỗi qua (row, col) nếu player đặt quân ở đó, và số đầu mở."""
    length, open_ends = 1, 0
    for sign in (1, -1):
        r, c = row + sign * row_step, col + sign * col_step
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
            length += 1
            r += sign * row_step
            c += sign * col_step
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY:
            open_ends += 1
    return length, open_ends


def _makes_five(board: list[list[int]], move: Move, player: int) -> bool:
    return any(_local_run(board, *move, player, dr, dc)[0] >= 5 for dr, dc in DIRECTIONS)


def _point_score(board: list[list[int]], move: Move, player: int) -> float:
    total = 0.0
    for dr, dc in DIRECTIONS:
        length, open_ends = _local_run(board, *move, player, dr, dc)
        if length >= 5:
            return WIN_SCORE
        total += RUN_SCORES.get((length, open_ends), 0)
    return total


def get_candidate_moves(state: GameState, max_candidates: int) -> list[Move]:
    """Lọc và sắp xếp ứng viên từ legal_moves(state); dùng chung cho cả hai thuật toán."""
    moves = legal_moves(state)
    if not moves:
        return []
    board = state.board
    me, opponent = state.current_player, -state.current_player
    stones = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != EMPTY]
    if not stones:
        center = (BOARD_SIZE // 2, BOARD_SIZE // 2)
        return [center]

    near = [
        (r, c) for r, c in moves
        if any(abs(r - sr) <= CANDIDATE_RADIUS and abs(c - sc) <= CANDIDATE_RADIUS for sr, sc in stones)
    ]  # giữ thứ tự hàng rồi cột của legal_moves -> phá hòa cố định

    winning = [m for m in near if _makes_five(board, m, me)]
    if winning:
        return winning
    blocking = [m for m in near if _makes_five(board, m, opponent)]
    if blocking:
        return blocking
    near.sort(key=lambda m: -(_point_score(board, m, me) + _point_score(board, m, opponent)))
    return near[:max_candidates]


def read_config(config: dict[str, int | float]) -> tuple[int, int]:
    depth = int(config.get("depth", DEFAULT_DEPTH))
    max_candidates = int(config.get("max_candidates", DEFAULT_MAX_CANDIDATES))
    if depth < 1:
        raise ValueError("depth phải từ 1 trở lên")
    if max_candidates < 1:
        raise ValueError("max_candidates phải dương")
    return depth, max_candidates


# ======================================================================
# MiniMax (Thuật toán 2.1)
# ======================================================================
def minimax(state: GameState, depth_remaining: int, root_player: int, max_candidates: int,
            *, counter: list[int] | None = None) -> float:
    """Trả điểm trạng thái. counter[0] được cộng 1 cho mỗi nút đã vào."""
    if counter is not None:
        counter[0] += 1
    terminal = terminal_score(state, root_player, depth_remaining)
    if terminal is not None:
        return terminal
    if depth_remaining == 0:
        return evaluate_state(state, root_player)

    candidate_moves = get_candidate_moves(state, max_candidates)
    if state.current_player == root_player:  # MAX
        best_score = -float("inf")
        for move in candidate_moves:
            score = minimax(apply_move(state, move), depth_remaining - 1, root_player,
                            max_candidates, counter=counter)
            best_score = max(best_score, score)
    else:  # MIN
        best_score = float("inf")
        for move in candidate_moves:
            score = minimax(apply_move(state, move), depth_remaining - 1, root_player,
                            max_candidates, counter=counter)
            best_score = min(best_score, score)
    return best_score


def choose_move(
    state: GameState,
    *,
    config: dict[str, int | float],
    rng: Random,
) -> tuple[Move, dict[str, int | float]]:
    """Chọn nước theo MiniMax. rng không dùng: hòa điểm phá theo thứ tự ứng viên cố định."""
    depth, max_candidates = read_config(config)
    root_player = state.current_player
    candidate_moves = get_candidate_moves(state, max_candidates)
    if not candidate_moves:
        raise ValueError("Không còn nước đi hợp lệ để lựa chọn")

    counter = [1]  # tính cả nút gốc
    best_move, best_score = candidate_moves[0], -float("inf")
    for move in candidate_moves:
        score = minimax(apply_move(state, move), depth - 1, root_player, max_candidates,
                        counter=counter)
        if score > best_score:
            best_move, best_score = move, score
    return best_move, {"nodes_visited": counter[0], "best_score": best_score}
