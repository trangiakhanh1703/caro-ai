"""Kiểm tra bộ luật Caro của phần A tuần 1."""

import io
import unittest
from contextlib import redirect_stdout

from game import (
    BOARD_SIZE,
    EMPTY,
    O,
    X,
    GameState,
    apply_move,
    get_result,
    legal_moves,
    new_game,
)
from main import print_board


def state_with_stones(stones: list[tuple[int, int, int]], current_player: int = X) -> GameState:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for row, col, player in stones:
        board[row][col] = player
    return GameState(board=board, current_player=current_player)


class GameRulesTest(unittest.TestCase):
    def test_new_game_and_turns(self) -> None:
        state = new_game()
        self.assertEqual(state.current_player, X)
        self.assertEqual(len(legal_moves(state)), 81)
        self.assertEqual(len({id(row) for row in state.board}), BOARD_SIZE)

        next_state = apply_move(state, (4, 4))
        final_state = apply_move(next_state, (3, 4))
        self.assertEqual(next_state.current_player, O)
        self.assertEqual(final_state.current_player, X)
        self.assertEqual(next_state.board[4][4], X)
        self.assertEqual(final_state.board[3][4], O)

    def test_apply_move_does_not_change_original_board(self) -> None:
        state = new_game()
        next_state = apply_move(state, (4, 4))
        self.assertEqual(state.board[4][4], EMPTY)
        self.assertIsNot(state.board, next_state.board)
        for old_row, new_row in zip(state.board, next_state.board):
            self.assertIsNot(old_row, new_row)

    def test_invalid_moves(self) -> None:
        state = new_game()
        for move in ((-1, 0), (0, -1), (9, 0), (0, 9)):
            with self.subTest(move=move), self.assertRaises(ValueError):
                apply_move(state, move)

        occupied = apply_move(state, (0, 0))
        with self.assertRaises(ValueError):
            apply_move(occupied, (0, 0))

        won = state_with_stones([(0, col, X) for col in range(5)])
        with self.assertRaises(ValueError):
            apply_move(won, (1, 0))

    def test_wins_in_four_directions(self) -> None:
        cases = {
            "horizontal": [(4, col, X) for col in range(2, 7)],
            "vertical": [(row, 4, O) for row in range(2, 7)],
            "main_diagonal": [(row, row, X) for row in range(1, 6)],
            "other_diagonal": [(row, 7 - row, O) for row in range(1, 6)],
        }
        for name, stones in cases.items():
            with self.subTest(name=name):
                expected = "x_win" if stones[0][2] == X else "o_win"
                self.assertEqual(get_result(state_with_stones(stones)), expected)

    def test_long_and_blocked_sequences_still_win(self) -> None:
        long_line = state_with_stones([(4, col, X) for col in range(1, 7)])
        blocked_line = state_with_stones(
            [(4, col, X) for col in range(2, 7)] + [(4, 1, O), (4, 7, O)]
        )
        self.assertEqual(get_result(long_line), "x_win")
        self.assertEqual(get_result(blocked_line), "x_win")

    def test_full_board_draw_and_full_board_win(self) -> None:
        draw_board = [
            [X if (row + 2 * col) % 4 < 2 else O for col in range(BOARD_SIZE)]
            for row in range(BOARD_SIZE)
        ]
        draw_state = GameState(board=draw_board, current_player=X)
        self.assertEqual(get_result(draw_state), "draw")

        win_board = [row.copy() for row in draw_board]
        win_board[0] = [X] * BOARD_SIZE
        win_state = GameState(board=win_board, current_player=O)
        self.assertEqual(get_result(win_state), "x_win")

    def test_legal_moves_empty_after_game_ends(self) -> None:
        won = state_with_stones([(0, col, X) for col in range(5)])
        self.assertEqual(legal_moves(won), [])

    def test_print_board(self) -> None:
        state = apply_move(apply_move(new_game(), (0, 0)), (0, 1))
        output = io.StringIO()
        with redirect_stdout(output):
            print_board(state)
        lines = output.getvalue().splitlines()
        self.assertEqual(lines[0], "  1 2 3 4 5 6 7 8 9")
        self.assertEqual(lines[1], "1 X O . . . . . . .")


if __name__ == "__main__":
    unittest.main()
