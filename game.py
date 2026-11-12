"""Trạng thái và bộ luật Caro 9 x 9."""

from dataclasses import dataclass
from typing import Literal

BOARD_SIZE = 9
WIN_LENGTH = 5
EMPTY = 0
X = 1
O = -1

Move = tuple[int, int]
GameResult = Literal["ongoing", "x_win", "o_win", "draw"]


@dataclass
class GameState:
    board: list[list[int]]
    current_player: int


def new_game() -> GameState:
    """Tạo bàn cờ trống 9 x 9 và cho X đi trước."""
    # Tạo từng hàng riêng để sửa một hàng không làm thay đổi các hàng còn lại.
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    return GameState(board=board, current_player=X)


def get_result(state: GameState) -> GameResult:
    """Trả kết quả hiện tại sau khi kiểm tra thắng và hòa."""
    # Bốn hướng đủ bao phủ ngang, dọc và hai đường chéo.
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            player = state.board[row][col]
            if player == EMPTY:
                continue

            for row_step, col_step in directions:
                end_row = row + (WIN_LENGTH - 1) * row_step
                end_col = col + (WIN_LENGTH - 1) * col_step
                if not (0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE):
                    continue

                if all(
                    state.board[row + offset * row_step][col + offset * col_step]
                    == player
                    for offset in range(WIN_LENGTH)
                ):
                    return "x_win" if player == X else "o_win"

    # Phải xét thắng trước: bàn đầy vẫn có thể chứa một chuỗi thắng.
    if all(cell != EMPTY for board_row in state.board for cell in board_row):
        return "draw"
    return "ongoing"


def legal_moves(state: GameState) -> list[Move]:
    """Trả các ô trống theo thứ tự hàng rồi cột nếu ván còn tiếp diễn."""
    if get_result(state) != "ongoing":
        return []

    return [
        (row, col)
        for row in range(BOARD_SIZE)
        for col in range(BOARD_SIZE)
        if state.board[row][col] == EMPTY
    ]


def apply_move(state: GameState, move: Move) -> GameState:
    """Áp dụng một nước hợp lệ và trả trạng thái mới với lượt đã đổi."""
    row, col = move
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        raise ValueError("Tọa độ nằm ngoài bàn cờ")
    if get_result(state) != "ongoing":
        raise ValueError("Ván chơi đã kết thúc")
    if state.board[row][col] != EMPTY:
        raise ValueError("Ô đã có quân")

    # Sao chép từng hàng để bàn trong state ban đầu không bị thay đổi.
    board = [board_row.copy() for board_row in state.board]
    board[row][col] = state.current_player
    next_state = GameState(board=board, current_player=-state.current_player)
    return next_state
