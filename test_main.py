"""Kiểm thử phần tích hợp tuần 2 của người A."""

import json
import tempfile
import unittest
from pathlib import Path
from random import Random
from unittest.mock import patch

from game import EMPTY, X, new_game
from main import choose_ai_move, load_state, parse_config


class MainIntegrationTest(unittest.TestCase):
    def test_load_valid_state_copies_board(self) -> None:
        state = new_game()
        data = {"board": state.board, "current_player": X}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = load_state(path)
        self.assertEqual(loaded, state)
        self.assertIsNot(loaded.board, state.board)

    def test_load_rejects_invalid_board(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"board": [], "current_player": 1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_state(path)

    def test_parse_config(self) -> None:
        self.assertEqual(parse_config('{"depth": 2}'), {"depth": 2})

    def test_ai_move_is_legal_and_preserves_state(self) -> None:
        state = new_game()
        move, stats, _ = choose_ai_move(state, "random", {}, Random(42))
        self.assertEqual(state.board[move[0]][move[1]], EMPTY)
        self.assertEqual(stats, {})

    def test_mutating_agent_is_rejected(self) -> None:
        state = new_game()

        def mutating_agent(state, *, config, rng):
            state.board[0][0] = X
            return (0, 1), {}

        with patch("main.get_agent_fn", return_value=mutating_agent):
            with self.assertRaises(RuntimeError):
                choose_ai_move(state, "random", {}, Random(42))


if __name__ == "__main__":
    unittest.main()
