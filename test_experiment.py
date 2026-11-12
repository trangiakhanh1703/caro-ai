"""Kiểm tra tác nhân Random, bộ chạy ván và xuất dữ liệu CSV (phần D)."""

import csv
import tempfile
import unittest
from pathlib import Path
from random import Random

from experiment import export_csv, run_paired_series
from game import legal_moves, new_game
from random_agent import choose_move
from run_game import GAMES_COLUMNS, MOVES_COLUMNS, play_game


class ExperimentPipelineTest(unittest.TestCase):
    def test_random_agent_legal_and_reproducible(self) -> None:
        state = new_game()
        move_1, stats_1 = choose_move(state, config={}, rng=Random(42))
        move_2, stats_2 = choose_move(state, config={}, rng=Random(42))

        self.assertIn(move_1, legal_moves(state))
        self.assertEqual(move_1, move_2)
        self.assertEqual(stats_1, {})
        self.assertEqual(stats_2, {})

    def test_play_game_logs_and_reproducibility(self) -> None:
        summary_1, moves_1 = play_game(
            "random",
            "random",
            x_config={},
            o_config={},
            x_seed=10,
            o_seed=11,
            game_id="g1",
            pair_id="p1",
        )
        summary_2, moves_2 = play_game(
            "random",
            "random",
            x_config={},
            o_config={},
            x_seed=10,
            o_seed=11,
            game_id="g1",
            pair_id="p1",
        )

        self.assertIn(summary_1["result"], ("x_win", "o_win", "draw"))
        self.assertEqual(summary_1["num_moves"], len(moves_1))
        self.assertEqual(moves_1[0]["turn_number"], 1)
        self.assertEqual(moves_1[0]["player"], "X")
        self.assertEqual(summary_1, summary_2)
        self.assertEqual(
            [(m["row"], m["col"]) for m in moves_1],
            [(m["row"], m["col"]) for m in moves_2],
        )

    def test_run_paired_series_swaps_sides_and_seeds(self) -> None:
        games, _ = run_paired_series(
            series_name="test",
            agent_a="random",
            config_a={},
            agent_b="random",
            config_b={},
            num_pairs=1,
            base_seed=100,
        )
        self.assertEqual(len(games), 2)
        self.assertEqual(games[0]["x_seed"], games[1]["o_seed"])
        self.assertEqual(games[0]["o_seed"], games[1]["x_seed"])

    def test_export_csv_schema(self) -> None:
        games, moves = run_paired_series(
            series_name="csv_test",
            agent_a="random",
            config_a={},
            agent_b="random",
            config_b={},
            num_pairs=1,
            base_seed=200,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_csv(games, moves, output_dir=tmp_dir)
            games_path = Path(tmp_dir) / "games.csv"
            moves_path = Path(tmp_dir) / "moves.csv"

            with games_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, GAMES_COLUMNS)
                self.assertEqual(len(list(reader)), 2)

            with moves_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, MOVES_COLUMNS)
                self.assertEqual(len(list(reader)), len(moves))


if __name__ == "__main__":
    unittest.main()