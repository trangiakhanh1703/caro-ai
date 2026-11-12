"""Tác nhân chọn nước đi hợp lệ ngẫu nhiên (Baseline)."""

from random import Random

from game import GameState, Move, legal_moves


def choose_move(
    state: GameState,
    *,
    config: dict[str, int | float],
    rng: Random,
) -> tuple[Move, dict[str, int | float]]:
    """Chọn ngẫu nhiên một nước hợp lệ bằng bộ sinh số rng được truyền vào."""
    moves = legal_moves(state)
    if not moves:
        raise ValueError("Không còn nước đi hợp lệ để lựa chọn")

    selected_move = rng.choice(moves)
    return selected_move, {}