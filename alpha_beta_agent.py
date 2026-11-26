"""Tác nhân Alpha-Beta cho Caro 9 x 9 — phần B.

Dùng chung evaluate_state, get_candidate_moves và thứ tự duyệt với minimax_agent,
nên luôn cho cùng điểm (và cùng nước đi) với MiniMax nhưng duyệt ít nút hơn.
Mã giả tương ứng trong báo cáo: Thuật toán 2.2 và 3.2.
"""

from random import Random

from game import GameState, Move, apply_move
from minimax_agent import evaluate_state, get_candidate_moves, read_config, terminal_score


def alpha_beta_search(state: GameState, depth_remaining: int, root_player: int,
                      max_candidates: int, alpha: float, beta: float,
                      *, counter: list[int] | None = None) -> float:
    """Trả điểm tìm kiếm có cắt tỉa. counter[0] được cộng 1 cho mỗi nút đã vào."""
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
            score = alpha_beta_search(apply_move(state, move), depth_remaining - 1, root_player,
                                      max_candidates, alpha, beta, counter=counter)
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break  # cắt beta
    else:  # MIN
        best_score = float("inf")
        for move in candidate_moves:
            score = alpha_beta_search(apply_move(state, move), depth_remaining - 1, root_player,
                                      max_candidates, alpha, beta, counter=counter)
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if alpha >= beta:
                break  # cắt alpha
    return best_score


def choose_move(
    state: GameState,
    *,
    config: dict[str, int | float],
    rng: Random,
) -> tuple[Move, dict[str, int | float]]:
    """Chọn nước theo Alpha-Beta. rng không dùng: hòa điểm phá theo thứ tự ứng viên cố định."""
    depth, max_candidates = read_config(config)
    root_player = state.current_player
    candidate_moves = get_candidate_moves(state, max_candidates)
    if not candidate_moves:
        raise ValueError("Không còn nước đi hợp lệ để lựa chọn")

    counter = [1]  # tính cả nút gốc
    best_move, best_score = candidate_moves[0], -float("inf")
    for move in candidate_moves:
        # alpha ở gốc = điểm tốt nhất đã có; nút con chỉ cần chứng minh "không tốt hơn"
        score = alpha_beta_search(apply_move(state, move), depth - 1, root_player, max_candidates,
                                  best_score, float("inf"), counter=counter)
        if score > best_score:
            best_move, best_score = move, score
    return best_move, {"nodes_visited": counter[0], "best_score": best_score}
