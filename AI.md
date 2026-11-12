# Caro AI 9×9 — Quy ước code chung

Phạm vi: Bài 1 theo bản phân công đầu tiên. Dùng Python 3.11 theo đề xuất của nhóm. Đặt file này ở thư mục gốc repo và dùng các chữ ký dưới đây khi viết hoặc ghép code.

## 1. File và người phụ trách

| File | Người | Trách nhiệm |
|---|---|---|
| `game.py` | A | Trạng thái, luật và kết quả Caro |
| `main.py` | A | Giao diện dòng lệnh, người–máy và máy–máy |
| `minimax_agent.py`, `alpha_beta_agent.py` | B | Hai tác nhân để chơi và đối chứng cắt tỉa |
| `mcts_agent.py` | C | MCTS, UCT và rollout ngẫu nhiên |
| `random_agent.py` | D | Tác nhân chọn nước hợp lệ ngẫu nhiên |
| `run_game.py`, `experiment.py` | D | Chạy ván AI, chạy thí nghiệm và xuất CSV |

Các tác nhân import luật từ `game.py`. Giao diện và bộ chạy gọi tác nhân qua cùng một chữ ký. Đặt tên hàm/biến theo `snake_case`, lớp theo `PascalCase`, hằng số theo `UPPER_CASE`.

## 2. A — Kiểu dữ liệu và luật trong `game.py`

```python
from dataclasses import dataclass
from typing import Literal

BOARD_SIZE = 9
WIN_LENGTH = 5
EMPTY = 0
X = 1
O = -1

Move = tuple[int, int]
GameResult = Literal["ongoing", "x_win", "o_win", "draw"]

@dataclass
class GameState:
    board: list[list[int]]
    current_player: int

def new_game() -> GameState: ...
def get_result(state: GameState) -> GameResult: ...
def legal_moves(state: GameState) -> list[Move]: ...
def apply_move(state: GameState, move: Move) -> GameState: ...
```

| Quy ước | Cách dùng |
|---|---|
| `board[row][col]` | Ma trận 9×9. `0` là ô trống, `1` là X, `-1` là O. |
| `current_player` | Quân sắp đi. `new_game()` tạo bàn trống và đặt X đi trước. |
| `move = (row, col)` | Cả hai chỉ số từ 0 đến 8. Nếu CLI hiển thị 1 đến 9, đổi chỉ số ở lớp giao diện. |
| `get_result(state)` | Có ít nhất 5 quân cùng loại liên tiếp theo hàng, cột hoặc một trong hai đường chéo thì thắng. Không xét chặn hai đầu. Xét thắng trước khi xét hòa do bàn đầy. |
| `legal_moves(state)` | Trả ô trống theo thứ tự hàng rồi cột. Trả `[]` nếu ván đã kết thúc. |
| `apply_move(state, move)` | Trả trạng thái mới, đặt đúng quân rồi đổi lượt. Sao chép từng hàng để giữ nguyên bàn đầu vào. Báo `ValueError` khi ô ngoài bàn, đã có quân hoặc ván đã kết thúc. |

Ví dụ: `next_state = apply_move(state, (4, 4))`. Nếu `state` là bàn mới, `next_state.board[4][4] == X`, `next_state.current_player == O` và `state.board[4][4] == EMPTY`.

## 3. Chữ ký của tất cả tác nhân

Mỗi module tác nhân xuất đúng hàm sau. `GameState` và `Move` lấy từ `game.py`, `Random` lấy từ module `random`.

```python
def choose_move(
    state: GameState,
    *,
    config: dict[str, int | float],
    rng: Random,
) -> tuple[Move, dict[str, int | float]]: ...
```

Bên gọi chỉ truyền trạng thái `"ongoing"`. Hàm trả về `(move, stats)`, giữ nguyên trạng thái đầu vào và chọn một nước từ `legal_moves(state)`. Dùng `rng` cho mọi lựa chọn ngẫu nhiên. B có thể bỏ qua `rng` nếu xử lý hòa điểm theo thứ tự cố định.

| `agent_name` | Module | `config` mẫu | Khóa trong `stats` |
|---|---|---|---|
| `random` | `random_agent` | `{}` | `{}` |
| `minimax` | `minimax_agent` | `{"depth": 2, "max_candidates": 12}` | `nodes_visited` |
| `alpha_beta` | `alpha_beta_agent` | `{"depth": 2, "max_candidates": 12}` | `nodes_visited` |
| `mcts` | `mcts_agent` | `{"iterations": 300, "exploration_c": 1.4}` | `iterations_run`, `selected_move_visits` |

Các khóa trong bảng là đầu vào của tác nhân tương ứng. `12` là giới hạn ứng viên mẫu để chạy thử, B chốt sau khi đo. Cấu hình đề xuất để đối chứng là `depth=2`, `iterations=300`, `exploration_c=1.4`.

## 4. B — MiniMax và Alpha-Beta

| Hàm nội bộ | Vai trò |
|---|---|
| `evaluate_state(state, root_player) -> float` | Điểm dương có lợi cho quân gốc. Điểm thắng/thua phải vượt điểm heuristic của trạng thái chưa kết thúc. |
| `get_candidate_moves(state, max_candidates) -> list[Move]` | Lọc và sắp xếp ứng viên từ `legal_moves(state)`. Dùng chung cho cả hai thuật toán. |
| `minimax(state, depth_remaining, root_player, max_candidates) -> float` | Trả điểm trạng thái. |
| `alpha_beta_search(state, depth_remaining, root_player, max_candidates, alpha, beta) -> float` | Trả điểm tìm kiếm có cắt tỉa. |

`root_player` lấy từ `state.current_player` ở gốc. MAX khi `state.current_player == root_player`, MIN ở lượt đối phương. `depth` là số nước tính từ trạng thái gốc. Dừng tại trạng thái kết thúc hoặc khi `depth_remaining == 0`. Dùng `best_move`, `best_score`, `candidate_moves`, `alpha`, `beta`. Đếm `nodes_visited` cho mọi nút đã vào, kể cả gốc và nút lá. Hai bản dùng cùng quy ước đếm, độ sâu, đánh giá và thứ tự ứng viên.

## 5. C — MCTS và UCT

| Tên | Ý nghĩa |
|---|---|
| `node.state`, `node.parent`, `node.children` | Trạng thái, nút cha và danh sách nút con |
| `node.move` | Nước từ cha tới nút, gốc dùng `None` |
| `node.untried_moves` | Các nước hợp lệ chưa mở rộng |
| `node.player_just_moved` | Quân đã đi để tạo nút. Ở gốc dùng `-state.current_player` làm quy ước lưu điểm. |
| `node.visit_count`, `node.total_reward` | Số lần thăm và tổng thưởng theo góc nhìn `player_just_moved` |

Các tên hàm nội bộ đề xuất là `select_child(node, exploration_c)`, `expand_node(node, rng)`, `rollout(state, rng)`, `backpropagate(node, result)` và `uct_score(child, exploration_c)`. Rollout trả một kết quả kết thúc của `GameResult`. Khi lan truyền, cập nhật thưởng theo quân của từng nút: thắng `1.0`, hòa `0.5`, thua `0.0`. Ở mỗi lượt chọn, quân đã đi của các nút con chính là quân đang đi ở nút cha.

UCT dùng `W/N + c * sqrt(log(N_parent) / N)`. Ưu tiên nút con chưa thăm trước khi tính công thức. Sau `iterations` lượt, trả nước của nút con có `visit_count` lớn nhất và ghi số lượt thăm đó vào `selected_move_visits`.

## 6. D — Chạy ván, tái lập và xuất CSV

```python
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
) -> tuple[dict, list[dict]]: ...
```

`play_game` trả `(game_summary, move_logs)`. Khởi tạo một RNG cho mỗi bên ở đầu ván và dùng lại trong cả ván. Mỗi lượt lấy tác nhân theo `current_player`, đo `choose_move` bằng `perf_counter()`, ghi quân vừa chọn và áp dụng nước. Dừng khi kết quả khác `"ongoing"`. X đi trước, vì vậy ván thứ hai trong cặp đổi tác nhân, cấu hình và seed tương ứng giữa X/O.

| Tệp | Cột |
|---|---|
| `moves.csv` | `game_id, turn_number, player, agent_name, row, col, elapsed_ms, depth, max_candidates, nodes_visited, iterations, exploration_c, iterations_run, selected_move_visits` |
| `games.csv` | `game_id, pair_id, x_agent, o_agent, x_seed, o_seed, result, num_moves` |

`turn_number` bắt đầu từ 1. `player` trong CSV là `"X"` hoặc `"O"`. Cột tham số/thống kê không áp dụng để trống. `elapsed_ms` chỉ đo lời gọi tác nhân. `game_id` là khóa nối hai bảng. Tỷ lệ thắng của tác nhân phải tính từ `result` và bên mà tác nhân đó đảm nhận, vì cùng một tác nhân có thể chơi X hoặc O.

## 7. Ghép thử cuối tuần 1

A đưa `GameState` và bốn hàm luật lên repo. D ghép Random và chạy thử theo khung sau sau khi hai module đã được cài:

```python
from random import Random

from game import O, X, apply_move, get_result, legal_moves, new_game
from random_agent import choose_move

state = new_game()
rng_by_player = {X: Random(42), O: Random(43)}

while get_result(state) == "ongoing":
    move, stats = choose_move(
        state, config={}, rng=rng_by_player[state.current_player]
    )
    assert move in legal_moves(state)
    state = apply_move(state, move)

print(get_result(state))
```

Kiểm tra X/O đổi lượt, không đánh đè ô và ván dừng khi thắng hoặc hòa. Tuần 2, gọi MiniMax, Alpha-Beta và MCTS theo cùng giao diện. Nếu cần đổi tên hàm, kiểu dữ liệu hoặc cột CSV, cập nhật file này và các chỗ gọi trong cùng Pull Request.
