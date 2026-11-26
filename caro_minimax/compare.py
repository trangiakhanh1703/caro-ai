"""So sánh MiniMax thường và Alpha-Beta trên CÙNG trạng thái, độ sâu, ứng viên.

Ví dụ:
    python compare.py                       # mặc định: 20 trạng thái, d = 2 và 3
    python compare.py --states 30 --depths 2 3 4 --top-k 10 --csv ket_qua.csv
"""
import argparse
import csv
import random
import statistics

from ab_agent import AlphaBetaAgent, MiniMaxAgent
from test_ab_agent import random_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=20)
    ap.add_argument("--depths", type=int, nargs="+", default=[2, 3])
    ap.add_argument("--radius", type=int, default=2)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--csv", help="ghi kết quả từng trạng thái ra file CSV")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    states = [random_state(rng, rng.randint(6, 24)) for _ in range(a.states)]
    rows = []
    for d in a.depths:
        for i, s in enumerate(states):
            cfg = dict(depth=d, radius=a.radius, top_k=a.top_k)
            m1, mm = MiniMaxAgent(**cfg).choose_move(s)
            m2, ab = AlphaBetaAgent(**cfg).choose_move(s)
            rows.append({
                "state": i, "depth": d, "radius": a.radius, "top_k": a.top_k,
                "mm_value": mm["value"], "ab_value": ab["value"], "same_value": mm["value"] == ab["value"],
                "mm_move": m1, "ab_move": m2,
                "mm_nodes": mm["nodes"], "ab_nodes": ab["nodes"],
                "mm_time_ms": mm["time_ms"], "ab_time_ms": ab["time_ms"],
            })

    print(f"{a.states} trạng thái, seed={a.seed}, r={a.radius}, K={a.top_k}\n")
    print("| d | Nút MiniMax (TB) | Nút Alpha-Beta (TB) | Giảm nút | Thời gian MM (ms) | Thời gian AB (ms) | Cùng giá trị |")
    print("|---|---|---|---|---|---|---|")
    for d in a.depths:
        rs = [r for r in rows if r["depth"] == d]
        mn = statistics.mean(r["mm_nodes"] for r in rs)
        an = statistics.mean(r["ab_nodes"] for r in rs)
        mt = statistics.mean(r["mm_time_ms"] for r in rs)
        at = statistics.mean(r["ab_time_ms"] for r in rs)
        same = sum(r["same_value"] for r in rs)
        print(f"| {d} | {mn:,.0f} | {an:,.0f} | {100 * (1 - an / mn):.1f}% | {mt:,.1f} | {at:,.1f} | {same}/{len(rs)} |")

    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nĐã ghi {len(rows)} dòng vào {a.csv}")


if __name__ == "__main__":
    main()
