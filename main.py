"""Minh họa cách in bàn cờ Caro."""

from game import EMPTY, O, X, GameState, apply_move, new_game


def print_board(state: GameState) -> None:
    """In bàn cờ với số hàng, cột từ 1 đến 9."""
    symbols = {EMPTY: ".", X: "X", O: "O"}
    print("  " + " ".join(str(number) for number in range(1, 10)))
    for row, board_row in enumerate(state.board, start=1):
        print(f"{row} " + " ".join(symbols[cell] for cell in board_row))


if __name__ == "__main__":
    state = new_game()
    state = apply_move(state, (4, 4))
    state = apply_move(state, (3, 4))
    print_board(state)
