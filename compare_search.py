"""So sánh MiniMax thường và Alpha-Beta trên CÙNG trạng thái, độ sâu và giới hạn ứng viên.

Ví dụ:
    python compare_search.py
    python compare_search.py --states 30 --depths 2 3 --max-candidates 12 --csv results/search_compare.csv
"""

import argparse
import csv
import statistics
from pathlib import Path
from random import Random
from time import perf_counter

import alpha_beta_agent
import minimax_agent
from game import apply_move, get_result, legal_moves, new_game


def random_state(rng: Random, num_stones: int):
    while True:
        state = new_game()
        for _ in range(num_stones):
            state = apply_move(state, rng.choice(legal_moves(state)))
            if get_result(state) != "ongoing":
                break
        if get_result(state) == "ongoing":
            return state


def timed(module, state, config):
    start = perf_counter()
    move, stats = module.choose_move(state, config=config, rng=Random(0))
    return move, stats, (perf_counter() - start) * 1000.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--states", type=int, default=20)
    parser.add_argument("--depths", type=int, nargs="+", default=[2, 3])
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--csv", type=Path, help="ghi kết quả từng trạng thái ra CSV")
    args = parser.parse_args()

    rng = Random(args.seed)
    states = [random_state(rng, rng.randint(6, 24)) for _ in range(args.states)]
    rows = []
    for depth in args.depths:
        config = {"depth": depth, "max_candidates": args.max_candidates}
        for index, state in enumerate(states):
            mm_move, mm, mm_ms = timed(minimax_agent, state, config)
            ab_move, ab, ab_ms = timed(alpha_beta_agent, state, config)
            rows.append({
                "state_id": index, "depth": depth, "max_candidates": args.max_candidates,
                "minimax_move": mm_move, "alpha_beta_move": ab_move,
                "minimax_score": mm["best_score"], "alpha_beta_score": ab["best_score"],
                "minimax_nodes": mm["nodes_visited"], "alpha_beta_nodes": ab["nodes_visited"],
                "minimax_ms": round(mm_ms, 3), "alpha_beta_ms": round(ab_ms, 3),
            })

    print(f"{args.states} trạng thái, seed={args.seed}, max_candidates={args.max_candidates}\n")
    print("| d | Nút MiniMax (TB) | Nút Alpha-Beta (TB) | Giảm nút | MiniMax (ms) | Alpha-Beta (ms) | Cùng điểm |")
    print("|---|---|---|---|---|---|---|")
    for depth in args.depths:
        part = [r for r in rows if r["depth"] == depth]
        mm_nodes = statistics.mean(r["minimax_nodes"] for r in part)
        ab_nodes = statistics.mean(r["alpha_beta_nodes"] for r in part)
        same = sum(r["minimax_score"] == r["alpha_beta_score"] for r in part)
        print(f"| {depth} | {mm_nodes:,.0f} | {ab_nodes:,.0f} | {100 * (1 - ab_nodes / mm_nodes):.1f}% "
              f"| {statistics.mean(r['minimax_ms'] for r in part):,.1f} "
              f"| {statistics.mean(r['alpha_beta_ms'] for r in part):,.1f} | {same}/{len(part)} |")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nĐã ghi {len(rows)} dòng vào {args.csv}")


if __name__ == "__main__":
    main()
