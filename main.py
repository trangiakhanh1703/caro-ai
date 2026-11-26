"""Giao diện dòng lệnh tích hợp cho trò chơi Caro 9 x 9."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from random import Random
from time import perf_counter

from game import BOARD_SIZE, EMPTY, O, X, GameState, Move, apply_move, get_result, legal_moves, new_game
from run_game import AGENT_MODULES, get_agent_fn

PLAYER_NAMES = {X: "X", O: "O"}
RESULT_MESSAGES = {"x_win": "X thắng!", "o_win": "O thắng!", "draw": "Ván cờ hòa."}


def configure_console() -> None:
    """Dùng UTF-8 khi đầu ra Windows đang mặc định ở bảng mã không hỗ trợ tiếng Việt."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def print_board(state: GameState) -> None:
    """In bàn cờ với số hàng, cột từ 1 đến 9."""
    symbols = {EMPTY: ".", X: "X", O: "O"}
    print("  " + " ".join(str(number) for number in range(1, BOARD_SIZE + 1)))
    for row, board_row in enumerate(state.board, start=1):
        print(f"{row} " + " ".join(symbols[cell] for cell in board_row))


def load_state(path: str | Path) -> GameState:
    """Nạp trạng thái JSON gồm board và current_player để demo/kiểm thử."""
    with Path(path).open("r", encoding="utf-8") as state_file:
        data = json.load(state_file)
    if not isinstance(data, dict):
        raise ValueError("Trạng thái phải là một đối tượng JSON")
    board = data.get("board")
    current_player = data.get("current_player")
    if (not isinstance(board, list) or len(board) != BOARD_SIZE or
            any(not isinstance(row, list) or len(row) != BOARD_SIZE for row in board)):
        raise ValueError(f"board phải là ma trận {BOARD_SIZE} x {BOARD_SIZE}")
    if any(cell not in (EMPTY, X, O) for row in board for cell in row):
        raise ValueError("Mỗi ô trong board chỉ được nhận -1, 0 hoặc 1")
    if current_player not in (X, O):
        raise ValueError("current_player phải là 1 (X) hoặc -1 (O)")
    x_count = sum(cell == X for row in board for cell in row)
    o_count = sum(cell == O for row in board for cell in row)
    if not (x_count == o_count or x_count == o_count + 1):
        raise ValueError("Số quân X/O không thể xuất hiện trong một ván hợp lệ")
    expected_player = X if x_count == o_count else O
    state = GameState(board=[row.copy() for row in board], current_player=current_player)
    if get_result(state) == "ongoing" and current_player != expected_player:
        raise ValueError("current_player không khớp với số quân X/O")
    return state


def parse_config(text: str) -> dict[str, int | float]:
    """Đọc cấu hình dạng JSON, ví dụ {\"depth\": 2}."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Cấu hình JSON không hợp lệ: {exc.msg}") from exc
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or type(item) not in (int, float) for key, item in value.items()
    ):
        raise argparse.ArgumentTypeError("Cấu hình phải là đối tượng JSON chỉ chứa số")
    return value


def ask_human_move(state: GameState) -> Move:
    """Nhập hàng và cột theo chỉ số 1..9 cho tới khi nhận được nước hợp lệ."""
    valid_moves = set(legal_moves(state))
    while True:
        raw = input(f"{PLAYER_NAMES[state.current_player]} đi (hàng cột): ").strip()
        try:
            row_text, col_text = raw.replace(",", " ").split()
            move = (int(row_text) - 1, int(col_text) - 1)
        except (ValueError, TypeError):
            print("Hãy nhập hai số, ví dụ: 5 5")
            continue
        if move in valid_moves:
            return move
        print("Nước đi không hợp lệ hoặc ô đã có quân.")


def choose_ai_move(state: GameState, agent_name: str, config: dict[str, int | float],
                   rng: Random) -> tuple[Move, dict[str, int | float], float]:
    """Gọi AI, đo thời gian và bảo vệ trạng thái đầu vào khỏi việc bị sửa."""
    choose_move = get_agent_fn(agent_name)
    board_before = deepcopy(state.board)
    player_before = state.current_player
    start = perf_counter()
    move, stats = choose_move(state, config=config, rng=rng)
    elapsed_ms = (perf_counter() - start) * 1000.0
    if state.board != board_before or state.current_player != player_before:
        raise RuntimeError(f"Tác nhân {agent_name} đã sửa trạng thái đầu vào")
    if move not in legal_moves(state):
        raise ValueError(f"Tác nhân {agent_name} trả về nước không hợp lệ: {move}")
    if not isinstance(stats, dict):
        raise TypeError(f"Tác nhân {agent_name} phải trả thống kê dạng dict")
    return move, stats, elapsed_ms


def play_interactive(*, x_player: str, o_player: str,
                     x_config: dict[str, int | float], o_config: dict[str, int | float],
                     seed: int, initial_state: GameState | None = None) -> str:
    """Chạy người–máy hoặc máy–máy và trả mã kết quả của ván."""
    state = initial_state or new_game()
    players = {
        X: (x_player, x_config, Random(seed)),
        O: (o_player, o_config, Random(seed + 1)),
    }
    print_board(state)
    turn = 0
    while get_result(state) == "ongoing":
        turn += 1
        player = state.current_player
        player_name, config, rng = players[player]
        if player_name == "human":
            move = ask_human_move(state)
        else:
            move, stats, elapsed_ms = choose_ai_move(state, player_name, config, rng)
            details = {"thời_gian_ms": round(elapsed_ms, 3), **stats}
            print(f"Lượt {turn}: {PLAYER_NAMES[player]} ({player_name}) chọn "
                  f"({move[0] + 1}, {move[1] + 1}) | {details}")
        state = apply_move(state, move)
        print_board(state)
    result = get_result(state)
    print(RESULT_MESSAGES[result])
    return result


def build_parser() -> argparse.ArgumentParser:
    choices = ["human", *AGENT_MODULES]
    parser = argparse.ArgumentParser(description="Caro AI 9 x 9")
    parser.add_argument("--x", choices=choices, default="human", help="người chơi X")
    parser.add_argument("--o", choices=choices, default="random", help="người chơi O")
    parser.add_argument("--x-config", type=parse_config, default={}, metavar="JSON")
    parser.add_argument("--o-config", type=parse_config, default={}, metavar="JSON")
    parser.add_argument("--depth", type=int, help="độ sâu cho minimax/alpha_beta")
    parser.add_argument("--max-candidates", type=int, help="số ứng viên tối đa")
    parser.add_argument("--iterations", type=int, help="số iteration cho MCTS")
    parser.add_argument("--exploration-c", type=float, help="hệ số c cho MCTS")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--state", type=Path, help="file trạng thái JSON ban đầu")
    return parser


def _merge_shortcuts(agent: str, config: dict[str, int | float],
                     args: argparse.Namespace) -> dict[str, int | float]:
    merged = config.copy()
    if agent in ("minimax", "alpha_beta"):
        if args.depth is not None:
            merged["depth"] = args.depth
        if args.max_candidates is not None:
            merged["max_candidates"] = args.max_candidates
    if agent == "mcts":
        if args.iterations is not None:
            merged["iterations"] = args.iterations
        if args.exploration_c is not None:
            merged["exploration_c"] = args.exploration_c
    return merged


def main(argv: list[str] | None = None) -> int:
    configure_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.x == args.o == "human":
        parser.error("Tuần 2 yêu cầu người–máy hoặc máy–máy; ít nhất một bên phải là AI")
    if args.depth is not None and args.depth < 2:
        parser.error("depth phải từ 2 trở lên")
    if args.max_candidates is not None and args.max_candidates < 1:
        parser.error("max-candidates phải dương")
    if args.iterations is not None and args.iterations < 1:
        parser.error("iterations phải dương")
    if args.exploration_c is not None and args.exploration_c <= 0:
        parser.error("exploration-c phải lớn hơn 0")
    try:
        state = load_state(args.state) if args.state else new_game()
        play_interactive(
            x_player=args.x, o_player=args.o,
            x_config=_merge_shortcuts(args.x, args.x_config, args),
            o_config=_merge_shortcuts(args.o, args.o_config, args),
            seed=args.seed, initial_state=state,
        )
    except (ImportError, ValueError, RuntimeError, TypeError, OSError) as exc:
        parser.exit(1, f"Lỗi: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
