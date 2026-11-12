"""Khung chạy thực nghiệm, ghép cặp hoán đổi X/O và xuất dữ liệu CSV."""

import csv
from pathlib import Path

from run_game import GAMES_COLUMNS, MOVES_COLUMNS, play_game


def run_paired_series(
    *,
    series_name: str,
    agent_a: str,
    config_a: dict[str, int | float],
    agent_b: str,
    config_b: dict[str, int | float],
    num_pairs: int = 10,
    base_seed: int = 1000,
) -> tuple[list[dict], list[dict]]:
    """Chạy num_pairs cặp ván đấu (mỗi cặp 2 ván hoán đổi quân đi trước X/O)."""
    all_games: list[dict] = []
    all_moves: list[dict] = []

    for pair_idx in range(1, num_pairs + 1):
        pair_id = f"{series_name}_p{pair_idx:02d}"
        seed_a = base_seed + pair_idx * 2
        seed_b = base_seed + pair_idx * 2 + 1

        # Ván 1: A cầm X (đi trước), B cầm O
        g1_summary, g1_moves = play_game(
            x_agent=agent_a,
            o_agent=agent_b,
            x_config=config_a,
            o_config=config_b,
            x_seed=seed_a,
            o_seed=seed_b,
            game_id=f"{pair_id}_g1",
            pair_id=pair_id,
        )
        all_games.append(g1_summary)
        all_moves.extend(g1_moves)

        # Ván 2: Hoán đổi — B cầm X (đi trước), A cầm O
        g2_summary, g2_moves = play_game(
            x_agent=agent_b,
            o_agent=agent_a,
            x_config=config_b,
            o_config=config_a,
            x_seed=seed_b,
            o_seed=seed_a,
            game_id=f"{pair_id}_g2",
            pair_id=pair_id,
        )
        all_games.append(g2_summary)
        all_moves.extend(g2_moves)

    return all_games, all_moves


def export_csv(
    games: list[dict],
    moves: list[dict],
    output_dir: str | Path = "results",
) -> None:
    """Xuất danh sách kết quả ván đấu và nước đi ra games.csv và moves.csv."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    games_file = out_path / "games.csv"
    moves_file = out_path / "moves.csv"

    with games_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GAMES_COLUMNS)
        writer.writeheader()
        writer.writerows(games)

    with moves_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MOVES_COLUMNS)
        writer.writeheader()
        writer.writerows(moves)

    print(f"Exported {len(games)} games to {games_file}")
    print(f"Exported {len(moves)} moves to {moves_file}")


if __name__ == "__main__":
    # Chạy thử 10 cặp (20 ván) Random vs Random để kiểm tra khung chạy & tạo mẫu CSV Tuần 1
    sample_games, sample_moves = run_paired_series(
        series_name="week1_random_check",
        agent_a="random",
        config_a={},
        agent_b="random",
        config_b={},
        num_pairs=10,
        base_seed=42,
    )
    export_csv(sample_games, sample_moves, output_dir="results")