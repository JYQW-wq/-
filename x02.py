import tkinter as tk
from tkinter import font as tkfont
import random, json, os, sys

LIGHT = dict(bg="#F5F5F7", card="#FFFFFF", card2="#FAFAFB", text="#1E1E1E",
             muted="#8A8A8E", accent="#0D99FF", accent_hover="#0B7FD6",
             x="#0D99FF", o="#FF5C5C", hover="#EDEDF0", border="#E4E4E7",
             win_x="#E3F2FD", win_o="#FFEBEE", win_draw="#F0F0F3",
             btn_bg="#FFFFFF", btn_text="#1E1E1E")
DARK  = dict(bg="#18181B", card="#232327", card2="#2A2A2F", text="#F4F4F5",
             muted="#9A9AA0", accent="#0D99FF", accent_hover="#3BAEFF",
             x="#4DB8FF", o="#FF6B6B", hover="#33333A", border="#3A3A40",
             win_x="#1E3A52", win_o="#4A2024", win_draw="#33333A",
             btn_bg="#2A2A2F", btn_text="#F4F4F5")

LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def score_file():
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False)
                           else os.path.abspath(__file__))
    return os.path.join(base, "score.json")

def load_score():
    try:
        return {k: json.load(open(score_file(), encoding="utf-8")).get(k, 0)
                for k in ("X", "O", "D")}
    except Exception:
        return {"X": 0, "O": 0, "D": 0}

def save_score(s):
    try:
        json.dump(s, open(score_file(), "w", encoding="utf-8"))
    except Exception:
        pass

def beep(kind="click"):
    try:
        import winsound
        seq = {"click": [(880, 40)], "win": [(1200, 80), (1500, 100)],
               "draw": [(600, 120)]}[kind]
        for f, d in seq: winsound.Beep(f, d)
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        root.title("Крестики нолики")
        root.minsize(760, 760)
        self.T, self.theme_name = LIGHT, "light"
        self.board, self.current = [""] * 9, "X"
        self.over, self.history = False, []
        self.score = load_score()
        self.mode, self.diff = "pvp", "medium"
        self.fs = False

        # шрифты
        self.f = {k: tkfont.Font(family="Segoe UI", size=s, weight=w)
                  for k, (s, w) in {
                      "title": (34, "bold"), "h2": (18, "bold"), "sub": (12, "normal"),
                      "cell": (76, "bold"), "btn": (12, "bold"),
                      "big": (14, "bold"), "status": (16, "bold"),
                      "small": (10, "normal"), "score": (18, "bold")}.items()}

        self.container = tk.Frame(root, bg=self.T["bg"])
        self.container.pack(fill="both", expand=True)
        self.page_menu = tk.Frame(self.container, bg=self.T["bg"])
        self.page_game = tk.Frame(self.container, bg=self.T["bg"])

        self._build_menu()
        self._build_game()
        self.apply_theme()
        self.show_menu()

        root.bind("<Key>", self._on_key)
        root.bind("<F11>", lambda e: self.toggle_fs())

    # ---------- helpers ----------
    def mkbtn(self, parent, text, cmd, font="btn", pad=(14, 8), **kw):
        return tk.Button(parent, text=text, font=self.f[font], command=cmd,
                         bd=0, relief="flat", cursor="hand2",
                         padx=pad[0], pady=pad[1], **kw)

    def mkcard(self, parent, title):
        card = tk.Frame(parent, bg=self.T["card"], highlightthickness=1,
                        highlightbackground=self.T["border"], padx=22, pady=18)
        card.pack(fill="x", pady=(0, 14))
        tk.Label(card, text=title, font=self.f["h2"],
                 bg=self.T["card"], fg=self.T["text"]).pack(anchor="w", pady=(0, 12))
        return card

    def _center_wrap(self, page):
        wrap = tk.Frame(page, bg=self.T["bg"])
        wrap.place(relx=.5, rely=.5, anchor="center")
        outer = tk.Frame(wrap, bg=self.T["bg"], padx=24, pady=8)
        outer.pack()
        return outer

    # ---------- menu ----------
    def _build_menu(self):
        outer = self._center_wrap(self.page_menu)

        top = tk.Frame(outer, bg=self.T["bg"])
        top.pack(fill="x")
        tbox = tk.Frame(top, bg=self.T["bg"])
        tbox.pack(side="left", anchor="w")
        self.m_title = tk.Label(tbox, text="Крестики нолики", font=self.f["title"],
                                bg=self.T["bg"], fg=self.T["text"])
        self.m_title.pack(anchor="w")
        self.m_sub = tk.Label(tbox, text="Выберите режим и нажмите «Играть»",
                              font=self.f["sub"], bg=self.T["bg"], fg=self.T["muted"])
        self.m_sub.pack(anchor="w", pady=(0, 18))
        self.fs_menu = self.mkbtn(top, "⛶", self.toggle_fs, pad=(10, 4))
        self.fs_menu.pack(side="right", anchor="n")

        mc = self.mkcard(outer, "Режим игры")
        self.mode_btn = {}
        for k, txt in [("pvp", "👥   2 игрока"), ("pvc", "🤖   Против компьютера")]:
            b = self.mkbtn(mc, txt, lambda k=k: self.set_mode(k), font="big",
                           pad=(18, 14), anchor="w")
            b.pack(fill="x", pady=5)
            self.mode_btn[k] = b

        dc = self.mkcard(outer, "Сложность (для ПК)")
        row = tk.Frame(dc, bg=self.T["card"])
        row.pack(fill="x")
        self.diff_btn = {}
        for k, txt in [("easy", "Легко"), ("medium", "Средне"), ("hard", "Сложно")]:
            b = self.mkbtn(row, txt, lambda k=k: self.set_diff(k), pad=(12, 12))
            b.pack(side="left", expand=True, fill="x", padx=4)
            self.diff_btn[k] = b

        tc = self.mkcard(outer, "Оформление")
        self.theme_btn_m = self.mkbtn(tc, "🌙 Тёмная тема", self.toggle_theme, pad=(18, 10))
        self.theme_btn_m.pack(anchor="w")

        self.play_btn = self.mkbtn(outer, "▶   Играть", self.show_game, font="big", pad=(24, 18))
        self.play_btn.pack(fill="x")

        self.m_score = tk.Label(outer, text="", font=self.f["small"],
                                bg=self.T["bg"], fg=self.T["muted"])
        self.m_score.pack(pady=(14, 0))

    # ---------- game ----------
    def _build_game(self):
        outer = self._center_wrap(self.page_game)

        top = tk.Frame(outer, bg=self.T["bg"])
        top.pack(fill="x")
        lbox = tk.Frame(top, bg=self.T["bg"])
        lbox.pack(side="left", anchor="w")
        self.g_title = tk.Label(lbox, text="Игра", font=self.f["h2"],
                                bg=self.T["bg"], fg=self.T["text"])
        self.g_title.pack(anchor="w")
        self.g_sub = tk.Label(lbox, text="", font=self.f["small"],
                              bg=self.T["bg"], fg=self.T["muted"])
        self.g_sub.pack(anchor="w")

        self.fs_game = self.mkbtn(top, "⛶", self.toggle_fs, pad=(10, 4))
        self.fs_game.pack(side="right", anchor="n", padx=(6, 0))
        self.back_btn = self.mkbtn(top, "← В меню", self.show_menu, pad=(14, 8))
        self.back_btn.pack(side="right", anchor="n")

        self.score_frame = tk.Frame(outer, bg=self.T["card"],
                                    highlightthickness=1,
                                    highlightbackground=self.T["border"])
        self.score_frame.pack(fill="x", pady=(16, 14), ipady=12)
        self.lbl_sx = tk.Label(self.score_frame, text="X 0", font=self.f["score"],
                               bg=self.T["card"], fg=self.T["x"])
        self.lbl_sx.pack(side="left", expand=True)
        self.lbl_sd = tk.Label(self.score_frame, text="Ничьи 0", font=self.f["score"],
                               bg=self.T["card"], fg=self.T["muted"])
        self.lbl_sd.pack(side="left", expand=True)
        self.lbl_so = tk.Label(self.score_frame, text="O 0", font=self.f["score"],
                               bg=self.T["card"], fg=self.T["o"])
        self.lbl_so.pack(side="left", expand=True)

        self.card = tk.Frame(outer, bg=self.T["card"], highlightthickness=1,
                             highlightbackground=self.T["border"], padx=16, pady=16)
        self.card.pack()
        self.cells = []
        for i in range(9):
            b = tk.Button(self.card, text="", font=self.f["cell"], width=2,
                          height=1, bd=0, relief="flat", cursor="hand2",
                          command=lambda i=i: self.click(i))
            b.grid(row=i // 3, column=i % 3, padx=6, pady=6, ipadx=14, ipady=8)
            b.bind("<Enter>", lambda e, b=b: self._hover(b, True))
            b.bind("<Leave>", lambda e, b=b: self._hover(b, False))
            self.cells.append(b)

        self.status = tk.Label(outer, text="", font=self.f["status"],
                               bg=self.T["bg"], fg=self.T["text"])
        self.status.pack(pady=(16, 10))

        bar = tk.Frame(outer, bg=self.T["bg"])
        bar.pack()
        self.undo_btn = self.mkbtn(bar, "↩  Отменить", self.undo, pad=(16, 10))
        self.undo_btn.pack(side="left", padx=5)
        self.new_btn = self.mkbtn(bar, "🔄  Новая игра", self.reset, pad=(18, 10))
        self.new_btn.pack(side="left", padx=5)
        self.rst_btn = self.mkbtn(bar, "🗑  Счёт", self.reset_score, pad=(14, 10))
        self.rst_btn.pack(side="left", padx=5)

        self.hint = tk.Label(outer,
                             text="1–9 — ход · R — рестарт · U — отмена · Esc — меню · F11 — полный экран",
                             font=self.f["small"], bg=self.T["bg"], fg=self.T["muted"])
        self.hint.pack(pady=(12, 0))

    # ---------- theme ----------
    def apply_theme(self):
        T = self.T
        self.root.configure(bg=T["bg"])
        for w in (self.container, self.page_menu, self.page_game):
            w.configure(bg=T["bg"])
        self.m_title.configure(bg=T["bg"], fg=T["text"])
        self.m_sub.configure(bg=T["bg"], fg=T["muted"])
        self.m_score.configure(bg=T["bg"], fg=T["muted"])

        for card in (self.page_menu.winfo_children()[0].winfo_children()[0]
                     .winfo_children(), ):
            pass

        for card in self._all_cards():
            card.configure(bg=T["card"], highlightbackground=T["border"])
            for ch in card.winfo_children():
                if isinstance(ch, tk.Label):
                    ch.configure(bg=T["card"], fg=T["text"])
                elif isinstance(ch, tk.Frame):
                    ch.configure(bg=T["card"])

        self.theme_btn_m.configure(
            text="☀ Светлая тема" if self.theme_name == "dark" else "🌙 Тёмная тема",
            bg=T["card2"], fg=T["text"], activebackground=T["hover"],
            activeforeground=T["text"])
        for b in (self.play_btn, self.new_btn):
            b.configure(bg=T["accent"], fg="white",
                        activebackground=T["accent_hover"], activeforeground="white")
        for b in (self.fs_menu, self.fs_game, self.back_btn, self.undo_btn, self.rst_btn):
            b.configure(bg=T["btn_bg"], fg=T["btn_text"],
                        activebackground=T["hover"], activeforeground=T["btn_text"])

        self.g_title.configure(bg=T["bg"], fg=T["text"])
        self.g_sub.configure(bg=T["bg"], fg=T["muted"])
        self.status.configure(bg=T["bg"], fg=T["text"])
        self.hint.configure(bg=T["bg"], fg=T["muted"])

        self.score_frame.configure(bg=T["card"], highlightbackground=T["border"])
        self.lbl_sx.configure(bg=T["card"], fg=T["x"])
        self.lbl_so.configure(bg=T["card"], fg=T["o"])
        self.lbl_sd.configure(bg=T["card"], fg=T["muted"])
        self.card.configure(bg=T["card"], highlightbackground=T["border"])

        for i, b in enumerate(self.cells):
            color = T[self.board[i].lower()] if self.board[i] else T["text"]
            b.configure(bg=T["bg"], fg=color)

        self._highlight_mode_ui()
        w = self._winner()
        if w: self._paint_win(w)

    def _all_cards(self):
        return [w for w in self.page_menu.winfo_children()[0].winfo_children()[0].winfo_children()
                if isinstance(w, tk.Frame) and w.cget("bg") == self.T["card"]
                and w not in (self.mode_btn["pvp"].master,)] + \
               [self.mode_btn["pvp"].master, self.diff_btn["medium"].master,
                self.theme_btn_m.master]

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.T = DARK if self.theme_name == "dark" else LIGHT
        self.apply_theme(); self._score_ui()

    # ---------- mode ----------
    def set_mode(self, m):
        self.mode = m; self._highlight_mode_ui()
    def set_diff(self, d):
        self.diff = d; self._highlight_mode_ui()

    def _highlight_mode_ui(self):
        T = self.T
        for k, b in self.mode_btn.items():
            on = (self.mode == k)
            b.configure(bg=T["accent"] if on else T["card2"],
                        fg="white" if on else T["text"],
                        activebackground=T["accent_hover"] if on else T["hover"],
                        activeforeground="white" if on else T["text"])
        for k, b in self.diff_btn.items():
            on = (self.diff == k)
            b.configure(bg=T["accent"] if on else T["card2"],
                        fg="white" if on else T["text"],
                        state="normal" if self.mode == "pvc" else "disabled")

    # ---------- pages ----------
    def show_menu(self):
        self.page_game.pack_forget()
        self.page_menu.pack(fill="both", expand=True)
        s = self.score
        self.m_score.configure(text=f"Счёт:   X {s['X']}   ·   Ничьи {s['D']}   ·   O {s['O']}")

    def show_game(self):
        self.page_menu.pack_forget()
        self.page_game.pack(fill="both", expand=True)
        self.reset()
        names = {"easy": "Легко", "medium": "Средне", "hard": "Сложно"}
        self.g_sub.configure(text="Режим: 2 игрока" if self.mode == "pvp"
                             else f"Режим: против ПК · {names[self.diff]}")

    def toggle_fs(self):
        self.fs = not self.fs
        self.root.attributes("-fullscreen", self.fs)

    # ---------- game logic ----------
    def _hover(self, b, enter):
        if self.over or b["text"] or self._pc_turn(): return
        b.configure(bg=self.T["hover"] if enter else self.T["bg"])

    def _pc_turn(self):
        return self.mode == "pvc" and self.current == "O" and not self.over

    def click(self, i):
        if self.over or self.board[i] or self._pc_turn(): return
        self._move(i)
        if self.mode == "pvc" and not self.over and self.current == "O":
            self.root.after(300, self._pc_move)

    def _move(self, i):
        p = self.current
        self.board[i] = p
        self.cells[i].configure(text=p, state="disabled", bg=self.T["bg"],
                                fg=self.T[p.lower()],
                                disabledforeground=self.T[p.lower()])
        self.history.append(i); beep()
        w = self._winner()
        if w:
            self.over = True
            self.status.configure(text=f"🏆 Победили {w}!")
            self._paint_win(w)
            self.score[w] += 1; save_score(self.score); self._score_ui(); beep("win")
            return
        if "" not in self.board:
            self.over = True
            self.status.configure(text="🤝 Ничья")
            self.score["D"] += 1; save_score(self.score); self._score_ui()
            for b in self.cells: b.configure(bg=self.T["win_draw"])
            beep("draw"); return
        self.current = "O" if p == "X" else "X"
        self._status()

    def _pc_move(self):
        empty = [i for i, v in enumerate(self.board) if v == ""]
        if not empty or self.over: return
        if self.diff == "easy":
            i = random.choice(empty)
        elif self.diff == "medium" and random.random() < .5:
            i = self._best() or random.choice(empty)
        elif self.diff == "medium":
            i = random.choice(empty)
        else:
            i = self._best() or random.choice(empty)
        self._move(i)

    def _best(self):
        best, bi = -999, None
        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "O"
                v = self._mini(False)
                self.board[i] = ""
                if v > best: best, bi = v, i
        return bi

    def _mini(self, mx):
        w = self._winner()
        if w == "O": return 10
        if w == "X": return -10
        if "" not in self.board: return 0
        vals = []
        for i in range(9):
            if self.board[i] == "":
                self.board[i] = "O" if mx else "X"
                vals.append(self._mini(not mx))
                self.board[i] = ""
        return max(vals) if mx else min(vals)

    def undo(self):
        if self.over or not self.history: return
        for _ in range(2 if self.mode == "pvc" else 1):
            if not self.history: break
            i = self.history.pop()
            self.board[i] = ""
            self.cells[i].configure(text="", state="normal",
                                    bg=self.T["bg"], fg=self.T["text"])
            self.current = "O" if self.current == "X" else "X"
        if self.mode == "pvc" and self.current == "O":
            self.current = "X"
        self._status()

    def reset(self):
        self.board, self.current, self.over = [""] * 9, "X", False
        self.history.clear()
        for b in self.cells:
            b.configure(text="", state="normal", bg=self.T["bg"], fg=self.T["text"])
        self._score_ui(); self._status()

    def reset_score(self):
        self.score = {"X": 0, "O": 0, "D": 0}; save_score(self.score); self._score_ui()

    # ---------- utils ----------
    def _winner(self):
        for a, b, c in LINES:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def _paint_win(self, w):
        color = self.T["win_x"] if w == "X" else self.T["win_o"]
        for a, b, c in LINES:
            if self.board[a] == self.board[b] == self.board[c] == w:
                for i in (a, b, c):
                    self.cells[i].configure(bg=color)

    def _status(self):
        if self.over: return
        self.status.configure(text="🤖 Ход компьютера…" if self._pc_turn()
                              else f"Сейчас ходят: {self.current}")

    def _score_ui(self):
        self.lbl_sx.configure(text=f"X  {self.score['X']}")
        self.lbl_so.configure(text=f"O  {self.score['O']}")
        self.lbl_sd.configure(text=f"Ничьи  {self.score['D']}")

    def _on_key(self, e):
        k = e.keysym.lower()
        if k == "f11": self.toggle_fs(); return
        if k == "escape":
            if self.fs: self.toggle_fs()
            else: self.show_menu()
            return
        if self.page_game.winfo_ismapped():
            if k in ("r", "к"): self.reset()
            elif k in ("u", "г"): self.undo()
            elif e.char in "123456789": self.click(int(e.char) - 1)


if __name__ == "__main__":
    root = tk.Tk()
    root.update_idletasks()
    w, h = 1000, 1000
    x = max(0, (root.winfo_screenwidth() - w) // 2)
    y = max(0, (root.winfo_screenheight() - h) // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")
    App(root)
    root.mainloop()
