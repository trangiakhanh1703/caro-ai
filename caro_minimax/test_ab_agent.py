"""Kiểm thử phần B. Chạy:  python -m unittest -v test_ab_agent"""
import random
import unittest

from ab_agent import AlphaBetaAgent, MiniMaxAgent, Searcher, candidates, evaluate, score_line, WIN
from gamestate import GameState, X, O, EMPTY


def random_state(rng, n_stones):
    """Trạng thái ngẫu nhiên chưa kết thúc, đi xen kẽ X/O."""
    while True:
        s = GameState()
        for _ in range(n_stones):
            s = s.apply(rng.choice(s.legal_moves()))
            if s.is_terminal():
                break
        if not s.is_terminal():
            return s


class TestHandTree(unittest.TestCase):
    """Cây ví dụ ở Hình 2.1 / Bảng 2.1 của báo cáo."""
    TREE = {"root": ["A", "B", "C"], "A": [6, 9, 4], "B": [8, 2, 7], "C": [3, 5, 10]}

    def make(self):
        return Searcher(
            moves=lambda s: list(range(len(self.TREE[s]))),
            apply=lambda s, m: self.TREE[s][m],
            terminal=lambda s, d: None,
            evaluate=lambda s: s,
        )

    def test_minimax(self):
        sr = self.make()
        move, value = sr.best_move("root", 2, pruning=False)
        self.assertEqual((move, value), (0, 4))  # chọn A, giá trị 4
        self.assertEqual(sr.leaves, 9)
        self.assertEqual(sr.nodes, 13)

    def test_alphabeta(self):
        sr = self.make()
        move, value = sr.best_move("root", 2, pruning=True)
        self.assertEqual((move, value), (0, 4))
        self.assertEqual(sr.leaves, 6)  # cắt lá 7 (B) và 5, 10 (C)
        self.assertEqual(sr.nodes, 10)
        self.assertEqual(sr.cutoffs, 2)


class TestEvaluation(unittest.TestCase):
    def test_pattern_scores(self):
        self.assertEqual(score_line("O_XXXX_O"), 100_000)
        self.assertEqual(score_line("OOXXXX_O"), 10_000)
        self.assertEqual(score_line("OOXXXXOO"), 0)  # chặn hai đầu, < 5
        self.assertEqual(score_line("O_XXX_O"), 5_000)
        self.assertEqual(score_line("OXXXXXO"), WIN)  # 5 bị chặn hai đầu vẫn thắng

    def test_symmetric_sign(self):
        s = GameState.from_strings([
            ".........", ".........", ".........",
            "...XXX...", ".........", ".........",
            ".........", ".........", ".........",
        ], O)
        self.assertGreater(evaluate(s.board, X), 0)
        self.assertLess(evaluate(s.board, O), 0)


class TestTacticalPositions(unittest.TestCase):
    AGENTS = (AlphaBetaAgent, MiniMaxAgent)

    def test_win_immediately(self):
        s = GameState.from_strings([
            ".........", ".........", "OOO......",
            ".........", "XXXX.....", ".........",
            "O........", ".........", ".........",
        ], X)
        for A in self.AGENTS:
            move, st = A(depth=2).choose_move(s)
            self.assertEqual(move, (4, 4), A.name)
            self.assertGreaterEqual(st["value"], WIN)

    def test_block_immediate_loss(self):
        s = GameState.from_strings([
            ".........", ".........", ".OOOO....",
            ".........", ".........", "......X..",
            ".......X.", "........X", ".........",
        ], X)
        for A in self.AGENTS:
            move, _ = A(depth=2).choose_move(s)
            self.assertIn(move, [(2, 0), (2, 5)], A.name)

    def test_block_open_three(self):
        # O có 3 mở hai đầu; X không có đe dọa -> X phải chặn một đầu (hoặc giữa khe)
        s = GameState.from_strings([
            ".........", ".........", ".........",
            "...OOO...", ".........", ".........",
            "X........", "........X", ".........",
        ], X)
        move, _ = AlphaBetaAgent(depth=2).choose_move(s)
        self.assertIn(move, [(3, 2), (3, 6), (3, 1), (3, 7)])

    def test_empty_board_center(self):
        move, _ = AlphaBetaAgent().choose_move(GameState())
        self.assertEqual(move, (4, 4))

    def test_near_full_board(self):
        # Mẫu không có chuỗi > 2 theo mọi hướng, chừa 3 ô trống
        rows = []
        for r in range(9):
            rows.append("".join("X" if ((c // 2) + r) % 2 == 0 else "O" for c in range(9)))
        rows = [list(r) for r in rows]
        for r, c in [(0, 0), (4, 4), (8, 8)]:
            rows[r][c] = "."
        s = GameState.from_strings(["".join(r) for r in rows], X)
        self.assertFalse(s.is_terminal())
        for A in self.AGENTS:
            move, st = A(depth=3).choose_move(s)
            self.assertIn(move, s.legal_moves())
            self.assertGreater(st["nodes"], 1)

    def test_does_not_mutate_state(self):
        rng = random.Random(1)
        s = random_state(rng, 12)
        before = [row[:] for row in s.board]
        AlphaBetaAgent(depth=2).choose_move(s)
        self.assertEqual(s.board, before)


class TestMiniMaxEqualsAlphaBeta(unittest.TestCase):
    def check(self, depth, top_k, seeds):
        for seed in seeds:
            s = random_state(random.Random(seed), 6 + seed % 15)
            m1, a = MiniMaxAgent(depth=depth, top_k=top_k).choose_move(s)
            m2, b = AlphaBetaAgent(depth=depth, top_k=top_k).choose_move(s)
            self.assertEqual(a["value"], b["value"], f"seed={seed}")
            self.assertEqual(m1, m2, f"seed={seed}")  # cùng thứ tự duyệt, phá hòa giống nhau
            self.assertLessEqual(b["nodes"], a["nodes"])

    def test_depth2(self):
        self.check(2, 12, range(15))

    def test_depth3(self):
        self.check(3, 6, range(8))


class TestFullGame(unittest.TestCase):
    def test_alphabeta_beats_random(self):
        for seed, ab_side in [(0, X), (1, O), (2, X), (3, O)]:
            rng = random.Random(seed)
            agent = AlphaBetaAgent(depth=2)
            s = GameState()
            while not s.is_terminal():
                if s.current_player == ab_side:
                    move, _ = agent.choose_move(s)
                else:
                    move = rng.choice(s.legal_moves())
                self.assertEqual(s.board[move[0]][move[1]], EMPTY)
                s = s.apply(move)
            self.assertEqual(s.winner, ab_side, f"seed={seed}")


class TestCandidates(unittest.TestCase):
    def test_limit_and_radius(self):
        s = random_state(random.Random(5), 10)
        c = candidates(s, radius=1, top_k=8)
        self.assertLessEqual(len(c), 8)
        for r, cc in c:
            self.assertEqual(s.board[r][cc], EMPTY)


if __name__ == "__main__":
    unittest.main()
