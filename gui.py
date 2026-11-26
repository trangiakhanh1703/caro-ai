"""Giao diện đồ họa Tkinter cho Caro AI 9 x 9.

GUI không cài lại luật chơi. Mọi kiểm tra và chuyển trạng thái đều đi qua
game.py theo đúng hợp đồng trong AI.md.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from random import Random
from tkinter import filedialog, messagebox, ttk

from game import BOARD_SIZE, EMPTY, O, X, GameState, apply_move, get_result, legal_moves, new_game
from main import RESULT_MESSAGES, choose_ai_move, load_state
from run_game import AGENT_MODULES

PLAYER_LABELS = {X: "X", O: "O"}
SYMBOLS = {EMPTY: "", X: "X", O: "O"}
COLORS = {EMPTY: "#f8fafc", X: "#ef4444", O: "#3b82f6"}
PLAYER_CHOICES = ("human", *AGENT_MODULES)
APP_BG = "#0f172a"
CARD_BG = "#1e293b"
BOARD_BG = "#334155"
CELL_BG = "#f8fafc"
CELL_HOVER = "#dbeafe"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#22c55e"


class CaroGUI:
    """Điều khiển một ván người–máy hoặc máy–máy trên Tkinter."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Caro AI 9 × 9")
        self.root.resizable(False, False)
        self.root.configure(bg=APP_BG)

        self.state: GameState = new_game()
        self.running = False
        self.pending_job: str | None = None
        self.rng_by_player = {X: Random(42), O: Random(43)}
        self.player_vars = {X: tk.StringVar(value="human"), O: tk.StringVar(value="random")}
        self.depth_var = tk.StringVar(value="2")
        self.max_candidates_var = tk.StringVar(value="12")
        self.iterations_var = tk.StringVar(value="300")
        self.exploration_var = tk.StringVar(value="1.4")
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Chọn chế độ rồi nhấn Bắt đầu")
        self.stats_var = tk.StringVar(value="")
        self.buttons: list[list[tk.Button]] = []

        self._build_layout()
        self._render_board()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT, font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", background=APP_BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=CARD_BG, foreground="#86efac", font=("Segoe UI", 12, "bold"))
        style.configure("Card.TLabelframe", background=CARD_BG, foreground=TEXT, bordercolor="#475569")
        style.configure("Card.TLabelframe.Label", background=CARD_BG, foreground=TEXT,
                        font=("Segoe UI", 11, "bold"))
        style.configure("TEntry", fieldbackground="#f8fafc", foreground="#0f172a", padding=6)
        style.configure("TCombobox", fieldbackground="#f8fafc", foreground="#0f172a", padding=5)
        style.configure("Primary.TButton", background=ACCENT, foreground="#052e16",
                        font=("Segoe UI", 10, "bold"), padding=(12, 9), borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#4ade80")])
        style.configure("Secondary.TButton", background="#475569", foreground=TEXT,
                        font=("Segoe UI", 10), padding=(12, 9), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#64748b")])

    def _build_layout(self) -> None:
        self._configure_styles()
        outer = ttk.Frame(self.root, padding=22, style="App.TFrame")
        outer.grid(sticky="nsew")

        header = ttk.Frame(outer, style="App.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        ttk.Label(header, text="CARO AI", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="  9 × 9  •  5 quân liên tiếp để thắng", style="Subtitle.TLabel").pack(
            side="left", pady=(10, 0)
        )
        legend = ttk.Frame(header, style="App.TFrame")
        legend.pack(side="right", pady=(8, 0))
        tk.Label(legend, text="  X  ", bg=COLORS[X], fg="white", font=("Segoe UI", 10, "bold")).pack(
            side="left", padx=4
        )
        tk.Label(legend, text="  O  ", bg=COLORS[O], fg="white", font=("Segoe UI", 10, "bold")).pack(
            side="left"
        )

        board_shell = tk.Frame(outer, bg=BOARD_BG, padx=7, pady=7)
        board_shell.grid(row=1, column=0, rowspan=3, padx=(0, 18), sticky="n")
        board_frame = tk.Frame(board_shell, bg=BOARD_BG)
        board_frame.pack()
        for row in range(BOARD_SIZE):
            button_row = []
            for col in range(BOARD_SIZE):
                button = tk.Button(
                    board_frame,
                    text="",
                    width=3,
                    height=1,
                    font=("Segoe UI", 19, "bold"),
                    relief="flat",
                    borderwidth=0,
                    cursor="hand2",
                    activebackground=CELL_HOVER,
                    command=lambda r=row, c=col: self.on_cell_click(r, c),
                )
                button.grid(row=row, column=col, ipadx=3, ipady=3, padx=1, pady=1)
                button.bind("<Enter>", lambda event, b=button: self._hover_cell(b, True))
                button.bind("<Leave>", lambda event, b=button: self._hover_cell(b, False))
                button_row.append(button)
            self.buttons.append(button_row)

        controls = ttk.LabelFrame(outer, text="  THIẾT LẬP VÁN CHƠI  ", padding=14, style="Card.TLabelframe")
        controls.grid(row=1, column=1, sticky="new")
        self._add_combo(controls, 0, "Người chơi X", self.player_vars[X], PLAYER_CHOICES)
        self._add_combo(controls, 1, "Người chơi O", self.player_vars[O], PLAYER_CHOICES)
        self._add_entry(controls, 2, "Độ sâu d", self.depth_var)
        self._add_entry(controls, 3, "Giới hạn ứng viên", self.max_candidates_var)
        self._add_entry(controls, 4, "MCTS iterations", self.iterations_var)
        self._add_entry(controls, 5, "Hệ số c", self.exploration_var)
        self._add_entry(controls, 6, "Random seed", self.seed_var)

        actions = ttk.Frame(controls, style="Card.TFrame")
        actions.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="ew")
        ttk.Button(actions, text="▶  Bắt đầu", command=self.start_game, style="Primary.TButton").pack(
            side="left", expand=True, fill="x"
        )
        ttk.Button(actions, text="Nạp trạng thái", command=self.open_state, style="Secondary.TButton").pack(
            side="left", expand=True, fill="x", padx=(6, 0)
        )

        info = ttk.LabelFrame(outer, text="  TRẠNG THÁI  ", padding=14, style="Card.TLabelframe")
        info.grid(row=2, column=1, pady=(12, 0), sticky="new")
        ttk.Label(info, textvariable=self.status_var, wraplength=310, style="Status.TLabel").pack(anchor="w")
        ttk.Label(info, textvariable=self.stats_var, wraplength=310, style="Muted.TLabel").pack(
            anchor="w", pady=(8, 0)
        )

        note = (
            "Nước người chơi: bấm vào ô trống. Luật, nước hợp lệ và kết quả "
            "được lấy trực tiếp từ game.py theo AI.md."
        )
        note_card = ttk.Frame(outer, padding=12, style="Card.TFrame")
        note_card.grid(row=3, column=1, pady=(12, 0), sticky="sew")
        ttk.Label(note_card, text="CÁCH CHƠI", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Label(note_card, text=note, wraplength=310, style="Muted.TLabel").pack(
            anchor="w", pady=(5, 0)
        )

    @staticmethod
    def _add_combo(parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar,
                   values: tuple[str, ...]) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=16).grid(
            row=row, column=1, sticky="ew", pady=3
        )

    @staticmethod
    def _add_entry(parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", pady=3)

    def _hover_cell(self, button: tk.Button, entering: bool) -> None:
        if str(button.cget("state")) == "normal" and not button.cget("text"):
            button.configure(bg=CELL_HOVER if entering else CELL_BG)

    def _read_settings(self) -> tuple[dict[str, int | float], int]:
        try:
            depth = int(self.depth_var.get())
            max_candidates = int(self.max_candidates_var.get())
            iterations = int(self.iterations_var.get())
            exploration_c = float(self.exploration_var.get())
            seed = int(self.seed_var.get())
        except ValueError as exc:
            raise ValueError("Các tham số phải là số hợp lệ") from exc
        if depth < 2:
            raise ValueError("Độ sâu d phải từ 2 trở lên")
        if max_candidates < 1 or iterations < 1 or exploration_c <= 0:
            raise ValueError("Ứng viên, iteration và c phải lớn hơn 0")
        return {
            "depth": depth,
            "max_candidates": max_candidates,
            "iterations": iterations,
            "exploration_c": exploration_c,
        }, seed

    @staticmethod
    def _config_for(agent: str, settings: dict[str, int | float]) -> dict[str, int | float]:
        if agent in ("minimax", "alpha_beta"):
            return {"depth": settings["depth"], "max_candidates": settings["max_candidates"]}
        if agent == "mcts":
            return {"iterations": settings["iterations"], "exploration_c": settings["exploration_c"]}
        return {}

    def start_game(self, initial_state: GameState | None = None) -> None:
        if self.player_vars[X].get() == self.player_vars[O].get() == "human":
            messagebox.showerror("Thiết lập không hợp lệ", "Ít nhất một bên phải là AI.")
            return
        try:
            _, seed = self._read_settings()
        except ValueError as exc:
            messagebox.showerror("Tham số không hợp lệ", str(exc))
            return
        self._cancel_pending_job()
        self.state = initial_state or new_game()
        self.rng_by_player = {X: Random(seed), O: Random(seed + 1)}
        self.running = get_result(self.state) == "ongoing"
        self.stats_var.set("")
        self._render_board()
        if self.running:
            self._update_turn_status()
            self._schedule_ai_if_needed()
        else:
            self._finish_game()

    def open_state(self) -> None:
        filename = filedialog.askopenfilename(
            title="Chọn trạng thái Caro", filetypes=(("JSON", "*.json"), ("Tất cả tệp", "*.*"))
        )
        if not filename:
            return
        try:
            state = load_state(Path(filename))
        except (OSError, ValueError) as exc:
            messagebox.showerror("Không thể nạp trạng thái", str(exc))
            return
        self.start_game(state)

    def on_cell_click(self, row: int, col: int) -> None:
        if not self.running:
            return
        player = self.state.current_player
        if self.player_vars[player].get() != "human":
            return
        move = (row, col)
        if move not in legal_moves(self.state):
            self.status_var.set("Ô này không hợp lệ hoặc đã có quân.")
            return
        self._apply_checked_move(move)

    def _schedule_ai_if_needed(self) -> None:
        if not self.running:
            return
        agent = self.player_vars[self.state.current_player].get()
        if agent != "human":
            self.pending_job = self.root.after(120, self._run_ai_turn)

    def _run_ai_turn(self) -> None:
        self.pending_job = None
        if not self.running:
            return
        player = self.state.current_player
        agent = self.player_vars[player].get()
        try:
            settings, _ = self._read_settings()
            config = self._config_for(agent, settings)
            move, stats, elapsed_ms = choose_ai_move(
                self.state, agent, config, self.rng_by_player[player]
            )
        except (ImportError, ValueError, RuntimeError, TypeError) as exc:
            self.running = False
            self._render_board()
            messagebox.showerror("Lỗi tác nhân AI", str(exc))
            self.status_var.set("Ván đã dừng do lỗi tác nhân.")
            return
        details = ", ".join(f"{key}={value}" for key, value in stats.items()) or "không có thống kê phụ"
        self.stats_var.set(
            f"{PLAYER_LABELS[player]} ({agent}) đi ({move[0] + 1}, {move[1] + 1}); "
            f"{elapsed_ms:.3f} ms; {details}"
        )
        self._apply_checked_move(move)

    def _apply_checked_move(self, move: tuple[int, int]) -> None:
        # Kiểm tra lại ngay trước apply_move để GUI không bao giờ bỏ qua hợp đồng AI.md.
        if move not in legal_moves(self.state):
            raise ValueError(f"Nước đi không hợp lệ: {move}")
        self.state = apply_move(self.state, move)
        self._render_board()
        if get_result(self.state) != "ongoing":
            self._finish_game()
            return
        self._update_turn_status()
        self._schedule_ai_if_needed()

    def _update_turn_status(self) -> None:
        player = self.state.current_player
        controller = self.player_vars[player].get()
        self.status_var.set(f"Đến lượt {PLAYER_LABELS[player]} ({controller})")

    def _finish_game(self) -> None:
        self.running = False
        self._cancel_pending_job()
        result = get_result(self.state)
        message = RESULT_MESSAGES[result]
        self.status_var.set(message)
        self._render_board()
        messagebox.showinfo("Kết thúc ván", message)

    def _render_board(self) -> None:
        valid_moves = set(legal_moves(self.state)) if self.running else set()
        human_turn = self.running and self.player_vars[self.state.current_player].get() == "human"
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                cell = self.state.board[row][col]
                self.buttons[row][col].configure(
                    text=SYMBOLS[cell],
                    fg=COLORS[cell],
                    bg=CELL_BG,
                    activebackground=CELL_HOVER,
                    state="normal" if human_turn and (row, col) in valid_moves else "disabled",
                    disabledforeground=COLORS[cell],
                )

    def _cancel_pending_job(self) -> None:
        if self.pending_job is not None:
            self.root.after_cancel(self.pending_job)
            self.pending_job = None


def main() -> None:
    root = tk.Tk()
    CaroGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
