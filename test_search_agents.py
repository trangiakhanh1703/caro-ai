"""Kiểm thử MiniMax và Alpha-Beta tuần 2 của người B.

Chạy: python -m unittest -v test_search_agents
"""

import unittest
from collections import namedtuple
from random import Random
from unittest.mock import patch

import alpha_beta_agent
import minimax_agent
from game import EMPTY, O, X, GameState, apply_move, get_result, legal_moves, new_game
from minimax_agent import WIN_SCORE, evaluate_state, get_candidate_moves, score_line
from run_game import play_game

AGENTS = {"minimax": minimax_agent, "alpha_beta": alpha_beta_agent}


def state_from_rows(rows: list[str], current_player: int) -> GameState:
    symbols = {"X": X, "O": O, ".": EMPTY}
    return GameState(board=[[symbols[ch] for ch in row] for row in rows], current_player=current_player)


def random_state(rng: Random, num_stones: int) -> GameState:
    """Trạng thái ngẫu nhiên còn đang chơi, X/O đi xen kẽ."""
    while True:
        state = new_game()
        for _ in range(num_stones):
            state = apply_move(state, rng.choice(legal_moves(state)))
            if get_result(state) != "ongoing":
                break
        if get_result(state) == "ongoing":
            return state


class HandTreeTest(unittest.TestCase):
    """Cây ở Hình 2.1 / Bảng 2.1 của báo cáo: gốc MAX, ba nút MIN A, B, C."""

    TREE = {"root": ["A", "B", "C"], "A": [6, 9, 4], "B": [8, 2, 7], "C": [3, 5, 10]}
    Node = namedtuple("Node", "name current_player")

    def run_tree(self, module):
        tree, node_cls = self.TREE, self.Node
        with patch.multiple(
            module,
            get_candidate_moves=lambda s, k: list(range(len(tree[s.name]))),
            apply_move=lambda s, m: node_cls(tree[s.name][m], -s.current_player),
            terminal_score=lambda s, root, d: None,
            evaluate_state=lambda s, root: s.name,
        ):
            return module.choose_move(node_cls("root", X), config={"depth": 2}, rng=Random(0))

    def test_minimax_visits_all_leaves(self) -> None:
        move, stats = self.run_tree(minimax_agent)
        self.assertEqual(move, 0)  # nhánh A
        self.assertEqual(stats["best_score"], 4)
        self.assertEqual(stats["nodes_visited"], 13)  # gốc + 3 nút MIN + 9 lá

    def test_alpha_beta_prunes_three_leaves(self) -> None:
        move, stats = self.run_tree(alpha_beta_agent)
        self.assertEqual(move, 0)
        self.assertEqual(stats["best_score"], 4)
        self.assertEqual(stats["nodes_visited"], 10)  # bỏ lá 7 (B), 5 và 10 (C)


class EvaluationTest(unittest.TestCase):
    def test_pattern_scores(self) -> None:
        self.assertEqual(score_line("O_XXXX_O"), 100_000)
        self.assertEqual(score_line("OOXXXX_O"), 10_000)
        self.assertEqual(score_line("OOXXXXOO"), 0)  # chặn hai đầu, chưa đủ 5
        self.assertEqual(score_line("O_XXX_O"), 5_000)
        self.assertEqual(score_line("OXXXXXO"), WIN_SCORE)  # 5 bị chặn hai đầu vẫn thắng

    def test_sign_follows_root_player(self) -> None:
        state = state_from_rows(
            [".........", ".........", ".........", "...XXX...", ".........",
             ".........", ".........", ".........", "........."], O)
        self.assertGreater(evaluate_state(state, X), 0)
        self.assertLess(evaluate_state(state, O), 0)

    def test_candidates_are_legal_and_limited(self) -> None:
        state = random_state(Random(5), 10)
        moves = get_candidate_moves(state, 8)
        self.assertLessEqual(len(moves), 8)
        self.assertTrue(set(moves) <= set(legal_moves(state)))


class TacticalTest(unittest.TestCase):
    def choose(self, name: str, state: GameState, depth: int = 2, max_candidates: int = 12):
        return AGENTS[name].choose_move(
            state, config={"depth": depth, "max_candidates": max_candidates}, rng=Random(0))

    def test_takes_immediate_win(self) -> None:
        state = state_from_rows(
            [".........", ".........", "OOO......", ".........", "XXXX.....",
             ".........", "O........", ".........", "........."], X)
        for name in AGENTS:
            move, stats = self.choose(name, state)
            self.assertEqual(move, (4, 4), name)
            self.assertGreaterEqual(stats["best_score"], WIN_SCORE)

    def test_blocks_immediate_loss(self) -> None:
        state = state_from_rows(
            [".........", ".........", ".OOOO....", ".........", ".........",
             "......X..", ".......X.", "........X", "........."], X)
        for name in AGENTS:
            move, _ = self.choose(name, state)
            self.assertIn(move, [(2, 0), (2, 5)], name)

    def test_blocks_open_three(self) -> None:
        state = state_from_rows(
            [".........", ".........", ".........", "...OOO...", ".........",
             ".........", "X........", "........X", "........."], X)
        move, _ = self.choose("alpha_beta", state)
        self.assertIn(move, [(3, 1), (3, 2), (3, 6), (3, 7)])

    def test_empty_board_plays_center(self) -> None:
        for name in AGENTS:
            move, _ = self.choose(name, new_game())
            self.assertEqual(move, (4, 4))

    def test_near_full_board(self) -> None:
        # Mẫu không có chuỗi dài hơn 2 theo mọi hướng; chừa 3 ô trống.
        rows = [["X" if ((c // 2) + r) % 2 == 0 else "O" for c in range(9)] for r in range(9)]
        for r, c in [(0, 0), (4, 4), (8, 8)]:
            rows[r][c] = "."
        state = state_from_rows(["".join(row) for row in rows], X)
        self.assertEqual(get_result(state), "ongoing")
        for name in AGENTS:
            move, stats = self.choose(name, state, depth=3)
            self.assertIn(move, legal_moves(state))
            self.assertGreater(stats["nodes_visited"], 1)

    def test_input_state_unchanged(self) -> None:
        state = random_state(Random(1), 12)
        board_before = [row.copy() for row in state.board]
        for name in AGENTS:
            self.choose(name, state)
            self.assertEqual(state.board, board_before)

    def test_rejects_bad_config(self) -> None:
        with self.assertRaises(ValueError):
            self.choose("alpha_beta", new_game(), depth=0)
        with self.assertRaises(ValueError):
            self.choose("alpha_beta", new_game(), max_candidates=0)


class MiniMaxMatchesAlphaBetaTest(unittest.TestCase):
    def check(self, depth: int, max_candidates: int, seeds: range) -> None:
        for seed in seeds:
            state = random_state(Random(seed), 6 + seed % 15)
            config = {"depth": depth, "max_candidates": max_candidates}
            mm_move, mm = minimax_agent.choose_move(state, config=config, rng=Random(0))
            ab_move, ab = alpha_beta_agent.choose_move(state, config=config, rng=Random(0))
            self.assertEqual(mm["best_score"], ab["best_score"], f"seed={seed}")
            self.assertEqual(mm_move, ab_move, f"seed={seed}")
            self.assertLessEqual(ab["nodes_visited"], mm["nodes_visited"], f"seed={seed}")

    def test_depth_2(self) -> None:
        self.check(2, 12, range(15))

    def test_depth_3(self) -> None:
        self.check(3, 6, range(8))


class RunnerIntegrationTest(unittest.TestCase):
    def test_alpha_beta_beats_random_both_sides(self) -> None:
        config = {"depth": 2, "max_candidates": 12}
        for i, (x_agent, o_agent) in enumerate([("alpha_beta", "random"), ("random", "alpha_beta")]):
            summary, moves = play_game(
                x_agent, o_agent, x_config=config if x_agent != "random" else {},
                o_config=config if o_agent != "random" else {},
                x_seed=10 + i, o_seed=20 + i, game_id=f"g{i}", pair_id="p")
            expected = "x_win" if x_agent == "alpha_beta" else "o_win"
            self.assertEqual(summary["result"], expected)
            ab_logs = [m for m in moves if m["agent_name"] == "alpha_beta"]
            self.assertTrue(all(isinstance(m["nodes_visited"], int) for m in ab_logs))
            self.assertTrue(all(m["depth"] == 2 for m in ab_logs))


if __name__ == "__main__":
    unittest.main()
