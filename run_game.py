"""Bộ điều phối trận đấu tự động, đo thời gian và ghi log từng nước đi."""

from collections.abc import Callable
from importlib import import_module
from random import Random
from time import perf_counter

from game import GameState, Move, O, X, apply_move, get_result, legal_moves, new_game

GAMES_COLUMNS = [
    "game_id",
    "pair_id",
    "x_agent",
    "o_agent",
    "x_seed",
    "o_seed",
    "result",
    "num_moves",
]

MOVES_COLUMNS = [
    "game_id",
    "turn_number",
    "player",
    "agent_name",
    "row",
    "col",
    "elapsed_ms",
    "depth",
    "max_candidates",
    "nodes_visited",
    "iterations",
    "exploration_c",
    "iterations_run",
    "selected_move_visits",
]

AGENT_MODULES = {
    "random": "random_agent",
    "minimax": "minimax_agent",
    "alpha_beta": "alpha_beta_agent",
    "mcts": "mcts_agent",
}

AgentFunc = Callable[..., tuple[Move, dict[str, int | float]]]


def get_agent_fn(agent_name: str) -> AgentFunc:
    """Nạp động hàm choose_move theo tên tác nhân trong AI.md."""
    if agent_name not in AGENT_MODULES:
        raise ValueError(f"Tên tác nhân không hợp lệ: {agent_name}")
    module = import_module(AGENT_MODULES[agent_name])
    return module.choose_move


def play_game(
    x_agent: str,
    o_agent: str,
    *,
    x_config: dict[str, int | float],
    o_config: dict[str, int | float],
    x_seed: int,
    o_seed: int,
    game_id: str,
    pair_id: str,
) -> tuple[dict, list[dict]]:
    """Chạy trọn vẹn một ván Caro và trả về (game_summary, move_logs)."""
    choose_x = get_agent_fn(x_agent)
    choose_o = get_agent_fn(o_agent)

    agents_by_player = {
        X: (x_agent, choose_x, x_config, Random(x_seed)),
        O: (o_agent, choose_o, o_config, Random(o_seed)),
    }

    state: GameState = new_game()
    move_logs: list[dict] = []
    turn_number = 0

    while get_result(state) == "ongoing":
        turn_number += 1
        current_player = state.current_player
        player_label = "X" if current_player == X else "O"
        agent_name, choose_fn, config, rng = agents_by_player[current_player]

        start_time = perf_counter()
        move, stats = choose_fn(state, config=config, rng=rng)
        elapsed_ms = round((perf_counter() - start_time) * 1000.0, 4)

        if move not in legal_moves(state):
            raise ValueError(f"Tác nhân {agent_name} trả về nước không hợp lệ: {move}")

        state = apply_move(state, move)

        move_logs.append(
            {
                "game_id": game_id,
                "turn_number": turn_number,
                "player": player_label,
                "agent_name": agent_name,
                "row": move[0],
                "col": move[1],
                "elapsed_ms": elapsed_ms,
                "depth": config.get("depth", ""),
                "max_candidates": config.get("max_candidates", ""),
                "nodes_visited": stats.get("nodes_visited", ""),
                "iterations": config.get("iterations", ""),
                "exploration_c": config.get("exploration_c", ""),
                "iterations_run": stats.get("iterations_run", ""),
                "selected_move_visits": stats.get("selected_move_visits", ""),
            }
        )

    game_summary = {
        "game_id": game_id,
        "pair_id": pair_id,
        "x_agent": x_agent,
        "o_agent": o_agent,
        "x_seed": x_seed,
        "o_seed": o_seed,
        "result": get_result(state),
        "num_moves": turn_number,
    }
    return game_summary, move_logs