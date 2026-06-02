import random
import time
import tkinter as tk
from tkinter import ttk


COLS = 10
ROWS = 20
BLOCK = 30
BOARD_WIDTH = COLS * BLOCK
BOARD_HEIGHT = ROWS * BLOCK
NEXT_SIZE = 120


COLORS = {
    "I": "#22d3ee",
    "O": "#facc15",
    "T": "#a78bfa",
    "S": "#34d399",
    "Z": "#fb7185",
    "J": "#60a5fa",
    "L": "#fb923c",
}

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}


class TetrisApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Python Tetris")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.main = ttk.Frame(self.root, padding=12)
        self.main.grid(row=0, column=0)

        self.board_canvas = tk.Canvas(
            self.main,
            width=BOARD_WIDTH,
            height=BOARD_HEIGHT,
            bg="#0b1220",
            highlightthickness=2,
            highlightbackground="#334155",
        )
        self.board_canvas.grid(row=0, column=0, rowspan=8, padx=(0, 12))

        self.title_label = ttk.Label(self.main, text="Python Tetris", font=("Segoe UI", 16, "bold"))
        self.title_label.grid(row=0, column=1, sticky="w")

        self.score_var = tk.StringVar(value="0")
        self.lines_var = tk.StringVar(value="0")
        self.level_var = tk.StringVar(value="1")

        self._make_stat("Score", self.score_var, 1)
        self._make_stat("Lines", self.lines_var, 2)
        self._make_stat("Level", self.level_var, 3)

        ttk.Label(self.main, text="Next").grid(row=4, column=1, sticky="w", pady=(8, 4))
        self.next_canvas = tk.Canvas(
            self.main,
            width=NEXT_SIZE,
            height=NEXT_SIZE,
            bg="#0b1220",
            highlightthickness=1,
            highlightbackground="#334155",
        )
        self.next_canvas.grid(row=5, column=1, sticky="w")

        controls = (
            "Left/Right : Move\n"
            "Down : Soft drop\n"
            "Up or X : Rotate CW\n"
            "Z : Rotate CCW\n"
            "Space : Hard drop\n"
            "P : Pause"
        )
        ttk.Label(self.main, text=controls, foreground="#475569", justify="left").grid(
            row=6, column=1, sticky="w", pady=(8, 8)
        )

        btn_row = ttk.Frame(self.main)
        btn_row.grid(row=7, column=1, sticky="ew")
        ttk.Button(btn_row, text="Start / Restart", command=self.start).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btn_row, text="Pause", command=self.toggle_pause).grid(row=0, column=1)

        touch = ttk.Frame(self.main)
        touch.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(touch, text="<-", width=8, command=lambda: self.move(-1)).grid(row=0, column=0, padx=3)
        ttk.Button(touch, text="->", width=8, command=lambda: self.move(1)).grid(row=0, column=1, padx=3)
        ttk.Button(touch, text="Down", width=8, command=self.soft_drop).grid(row=0, column=2, padx=3)
        ttk.Button(touch, text="Rotate", width=8, command=lambda: self.rotate(1)).grid(row=0, column=3, padx=3)

        self.board = self.create_board()
        self.current = None
        self.next_piece = None

        self.score = 0
        self.lines = 0
        self.level = 1
        self.drop_counter = 0.0
        self.drop_interval = 800

        self.started = False
        self.paused = False
        self.game_over = False

        self.last_time = time.perf_counter()

        self.root.bind("<KeyPress>", self.handle_key)
        self.show_overlay("Tetris", "Press Start or Enter")
        self.loop()

    def _make_stat(self, name: str, var: tk.StringVar, row: int) -> None:
        frame = ttk.Frame(self.main)
        frame.grid(row=row, column=1, sticky="w", pady=2)
        ttk.Label(frame, text=f"{name}: ", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=var).grid(row=0, column=1, sticky="w")

    def create_board(self):
        return [[0 for _ in range(COLS)] for _ in range(ROWS)]

    def random_piece(self):
        kind = random.choice(list(SHAPES.keys()))
        return {
            "type": kind,
            "matrix": [row[:] for row in SHAPES[kind]],
            "x": COLS // 2 - 1,
            "y": 0,
        }

    def center_current_piece(self):
        self.current["x"] = (COLS - len(self.current["matrix"][0])) // 2

    def reset_game(self):
        self.board = self.create_board()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.drop_interval = 800
        self.drop_counter = 0

        self.started = True
        self.paused = False
        self.game_over = False

        self.current = self.random_piece()
        self.next_piece = self.random_piece()
        self.center_current_piece()

        self.update_stats()
        self.clear_overlay()

    def start(self):
        self.reset_game()

    def collide(self, piece, offset_x=0, offset_y=0, matrix=None):
        matrix = matrix if matrix is not None else piece["matrix"]
        for y, row in enumerate(matrix):
            for x, value in enumerate(row):
                if not value:
                    continue
                nx = piece["x"] + x + offset_x
                ny = piece["y"] + y + offset_y
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return True
                if ny >= 0 and self.board[ny][nx]:
                    return True
        return False

    def merge(self, piece):
        for y, row in enumerate(piece["matrix"]):
            for x, value in enumerate(row):
                if value and piece["y"] + y >= 0:
                    self.board[piece["y"] + y][piece["x"] + x] = piece["type"]

    def clear_lines(self):
        cleared = 0
        y = ROWS - 1
        while y >= 0:
            if all(self.board[y][x] != 0 for x in range(COLS)):
                self.board.pop(y)
                self.board.insert(0, [0 for _ in range(COLS)])
                cleared += 1
            else:
                y -= 1

        if cleared > 0:
            table = [0, 100, 300, 500, 800]
            self.score += table[cleared] * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
            self.drop_interval = max(120, 800 - (self.level - 1) * 60)
            self.update_stats()

    def spawn(self):
        self.current = self.next_piece
        self.next_piece = self.random_piece()
        self.current["y"] = 0
        self.center_current_piece()

        if self.collide(self.current):
            self.game_over = True
            self.started = False
            self.show_overlay("Game Over", "Press Start or Enter")

    def rotate_matrix(self, matrix, direction):
        transposed = [list(r) for r in zip(*matrix)]
        if direction > 0:
            return [list(reversed(r)) for r in transposed]
        return list(reversed(transposed))

    def rotate(self, direction):
        if not self.started or self.paused or self.game_over:
            return

        rotated = self.rotate_matrix(self.current["matrix"], direction)
        old_x = self.current["x"]
        offset = 1

        while self.collide(self.current, 0, 0, rotated):
            self.current["x"] += offset
            offset = -(offset + (1 if offset > 0 else -1))
            if abs(offset) > len(self.current["matrix"][0]) + 1:
                self.current["x"] = old_x
                return

        self.current["matrix"] = rotated

    def move(self, direction):
        if not self.started or self.paused or self.game_over:
            return
        if not self.collide(self.current, direction, 0):
            self.current["x"] += direction

    def soft_drop(self):
        if not self.started or self.paused or self.game_over:
            return

        if not self.collide(self.current, 0, 1):
            self.current["y"] += 1
            self.score += 1
            self.update_stats()
        else:
            self.lock_piece()
        self.drop_counter = 0

    def hard_drop(self):
        if not self.started or self.paused or self.game_over:
            return

        while not self.collide(self.current, 0, 1):
            self.current["y"] += 1
            self.score += 2
        self.lock_piece()
        self.update_stats()

    def lock_piece(self):
        self.merge(self.current)
        self.clear_lines()
        self.spawn()

    def update_stats(self):
        self.score_var.set(str(self.score))
        self.lines_var.set(str(self.lines))
        self.level_var.set(str(self.level))

    def toggle_pause(self):
        if not self.started or self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self.show_overlay("Paused", "Press P or Pause")
        else:
            self.clear_overlay()

    def show_overlay(self, title: str, subtitle: str):
        self.clear_overlay()
        pad = 30
        self.overlay_rect = self.board_canvas.create_rectangle(
            pad,
            BOARD_HEIGHT // 2 - 65,
            BOARD_WIDTH - pad,
            BOARD_HEIGHT // 2 + 65,
            fill="#020617",
            outline="#475569",
            width=2,
        )
        self.overlay_title = self.board_canvas.create_text(
            BOARD_WIDTH // 2,
            BOARD_HEIGHT // 2 - 18,
            text=title,
            fill="#fef3c7",
            font=("Segoe UI", 20, "bold"),
        )
        self.overlay_sub = self.board_canvas.create_text(
            BOARD_WIDTH // 2,
            BOARD_HEIGHT // 2 + 18,
            text=subtitle,
            fill="#94a3b8",
            font=("Segoe UI", 11),
        )

    def clear_overlay(self):
        for item_name in ("overlay_rect", "overlay_title", "overlay_sub"):
            item_id = getattr(self, item_name, None)
            if item_id:
                self.board_canvas.delete(item_id)
                setattr(self, item_name, None)

    def draw_cell(self, canvas, x, y, color, size):
        px = x * size
        py = y * size
        canvas.create_rectangle(px, py, px + size, py + size, fill=color, outline="#0f172a")
        canvas.create_rectangle(
            px + 2,
            py + 2,
            px + size - 2,
            py + max(3, int(size * 0.16)),
            fill="#ffffff",
            outline="",
            stipple="gray50",
        )

    def draw_board(self):
        self.board_canvas.delete("board")

        for y in range(ROWS):
            for x in range(COLS):
                cell = self.board[y][x]
                if cell:
                    self._draw_cell_tagged(self.board_canvas, x, y, COLORS[cell], BLOCK, "board")

        for y in range(ROWS):
            for x in range(COLS):
                self.board_canvas.create_rectangle(
                    x * BLOCK,
                    y * BLOCK,
                    x * BLOCK + BLOCK,
                    y * BLOCK + BLOCK,
                    outline="#1e293b",
                    width=1,
                    tags="board",
                )

        if self.current:
            for y, row in enumerate(self.current["matrix"]):
                for x, value in enumerate(row):
                    if value:
                        self._draw_cell_tagged(
                            self.board_canvas,
                            self.current["x"] + x,
                            self.current["y"] + y,
                            COLORS[self.current["type"]],
                            BLOCK,
                            "board",
                        )

    def _draw_cell_tagged(self, canvas, x, y, color, size, tag):
        px = x * size
        py = y * size
        canvas.create_rectangle(px, py, px + size, py + size, fill=color, outline="#0f172a", tags=tag)
        canvas.create_rectangle(
            px + 2,
            py + 2,
            px + size - 2,
            py + max(3, int(size * 0.16)),
            fill="#ffffff",
            outline="",
            stipple="gray50",
            tags=tag,
        )

    def draw_next(self):
        self.next_canvas.delete("all")
        if not self.next_piece:
            return

        matrix = self.next_piece["matrix"]
        size = NEXT_SIZE // 5
        offset_x = (5 - len(matrix[0])) // 2
        offset_y = (5 - len(matrix)) // 2

        for y, row in enumerate(matrix):
            for x, value in enumerate(row):
                if value:
                    self.draw_cell(self.next_canvas, x + offset_x, y + offset_y, COLORS[self.next_piece["type"]], size)

    def handle_key(self, event):
        if event.keysym == "Return" and not self.started:
            self.start()
            return

        if event.keysym in ("p", "P"):
            self.toggle_pause()
            return

        if not self.started or self.paused or self.game_over:
            return

        if event.keysym == "Left":
            self.move(-1)
        elif event.keysym == "Right":
            self.move(1)
        elif event.keysym == "Down":
            self.soft_drop()
        elif event.keysym in ("Up", "x", "X"):
            self.rotate(1)
        elif event.keysym in ("z", "Z"):
            self.rotate(-1)
        elif event.keysym == "space":
            self.hard_drop()

    def loop(self):
        now = time.perf_counter()
        delta_ms = (now - self.last_time) * 1000
        self.last_time = now

        if self.started and not self.paused and not self.game_over:
            self.drop_counter += delta_ms
            if self.drop_counter > self.drop_interval:
                if not self.collide(self.current, 0, 1):
                    self.current["y"] += 1
                    self.score += 1
                else:
                    self.lock_piece()
                self.drop_counter = 0
                self.update_stats()

        self.draw_board()
        self.draw_next()
        self.root.after(16, self.loop)


if __name__ == "__main__":
    root = tk.Tk()
    app = TetrisApp(root)
    root.mainloop()
