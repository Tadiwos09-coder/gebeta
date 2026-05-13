import tkinter as tk
import os
import random
import copy
import math
from PIL import Image, ImageTk, ImageDraw, ImageFilter

# ================= BACKGROUNDS =================
base_path = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()

def scale_cover_pil(img, target_w, target_h):
    img_w, img_h = img.size
    if img_w == 0 or img_h == 0: raise ValueError("Image has invalid size")
    fill_scale = max(target_w / img_w, target_h / img_h)
    new_w = max(int(img_w * fill_scale), target_w)
    new_h = max(int(img_h * fill_scale), target_h)
    img = img.resize((new_w, new_h), Image.NEAREST)
    crop_x = max((new_w - target_w) // 2, 0)
    crop_y = max((new_h - target_h) // 2, 0)
    return img.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))

def ensure_placeholder(path, color, size=(800, 600)):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img = Image.new("RGB", size, color)
        draw = ImageDraw.Draw(img)
        draw.text((size[0]//2 - 50, size[1]//2), os.path.basename(path), fill="white")
        img.save(path)

menu_bg_raw = None
game_bg_raw = None

menu_bg_path = os.path.join(base_path, "assets", "home.png")
game_bg_path = os.path.join(base_path, "assets", "bg.png")

ensure_placeholder(menu_bg_path, (62, 39, 35))
ensure_placeholder(game_bg_path, (45, 30, 25))

if os.path.exists(menu_bg_path):
    try: menu_bg_raw = Image.open(menu_bg_path).convert("RGB")
    except Exception: pass

if os.path.exists(game_bg_path):
    try: game_bg_raw = Image.open(game_bg_path).convert("RGB")
    except Exception: pass

# ================= PROCEDURAL WOOD TEXTURE =================
def create_wood_texture(w, h):
    img = Image.new('RGB', (w, h), (101, 67, 33))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        for x in range(w):
            wave = math.sin(y / 15 + math.sin(x / 80) * 3) * 5
            dist_to_center = abs(wave - (x - w/2) % 60)
            if dist_to_center < 1.5:
                draw.point((x, y), fill=(70, 42, 18))
            elif random.random() < 0.05:
                draw.point((x, y), fill=(110, 72, 35))
    return img.filter(ImageFilter.GaussianBlur(1))

wood_texture_raw = create_wood_texture(800, 400)

# ================= UI HELPERS =================
def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

# ----------------- Gebeta Game Logic -----------------
class GebetaGame:
    def __init__(self): self.reset_board()
    def reset_board(self):
        self.board = [4] * 12; self.owners = [1] * 6 + [2] * 6
        self.scores = {1: 0, 2: 0}; self.current_player = 1; self.game_over = False

    def get_valid_moves(self, player):
        return [i for i in range(12) if self.owners[i] == player and self.board[i] > 0]

    def make_move(self, start_index):
        if self.board[start_index] == 0 or self.owners[start_index] != self.current_player:
            return False, False, False
        stones = self.board[start_index]; self.board[start_index] = 0; current_index = start_index
        captured = False
        while stones > 0:
            current_index = (current_index + 1) % 12; self.board[current_index] += 1; stones -= 1
            if stones == 0:
                count = self.board[current_index]
                if count == 4:
                    self.scores[self.current_player] += 4; self.board[current_index] = 0
                    self.owners[current_index] = self.current_player; captured = True; break
                if count > 1: stones = self.board[current_index]; self.board[current_index] = 0
        self.current_player = 2 if self.current_player == 1 else 1
        return self.check_game_over(), True, captured

    def check_game_over(self):
        if not self.get_valid_moves(self.current_player):
            self.game_over = True
            for i in range(12): self.scores[self.owners[i]] += self.board[i]; self.board[i] = 0
            return True
        return False


# ----------------- AI Engine -----------------
class GebetaAI:
    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty
        self.base_depth = {'easy': 1, 'medium': 3, 'hard': 4}.get(difficulty, 3)

    def get_best_move(self, game_state):
        valid_moves = game_state.get_valid_moves(2)
        if not valid_moves: return None
        total_stones = sum(game_state.board); depth = self.base_depth
        if total_stones > 15: depth = 2
        elif total_stones > 25: depth = 1
        random.shuffle(valid_moves); best_move = valid_moves[0]; best_score = -float('inf')
        for move in valid_moves:
            temp_game = copy.deepcopy(game_state)
            temp_game.make_move(move)
            score = self._minimax(temp_game, depth - 1, -float('inf'), float('inf'), temp_game.current_player == 2)
            if score > best_score: best_score = score; best_move = move
        return best_move

    def _minimax(self, game_state, depth, alpha, beta, maximizing):
        if depth == 0 or game_state.game_over: return self._evaluate(game_state)
        moves = game_state.get_valid_moves(game_state.current_player)
        if not moves: return self._evaluate(game_state)
        if maximizing:
            value = -float('inf')
            for move in moves:
                temp = copy.deepcopy(game_state); temp.make_move(move)
                value = max(value, self._minimax(temp, depth - 1, alpha, beta, temp.current_player == 2))
                alpha = max(alpha, value)
                if beta <= alpha: break
            return value
        else:
            value = float('inf')
            for move in moves:
                temp = copy.deepcopy(game_state); temp.make_move(move)
                value = min(value, self._minimax(temp, depth - 1, alpha, beta, temp.current_player == 2))
                beta = min(beta, value)
                if beta <= alpha: break
            return value

    def _evaluate(self, game_state):
        my_score = game_state.scores[2]; opp_score = game_state.scores[1]
        board_value = sum(game_state.board[i] * 0.1 * (1 if game_state.owners[i] == 2 else -1) for i in range(12))
        return (my_score - opp_score) * 10 + board_value


# ----------------- Custom UI Components -----------------
class HoverButton(tk.Canvas):
    def __init__(self, parent, text, command, bg_color, fg_color="#F5E6CC", width=180, height=45,
                 radius=0, font_size=12, bold=True, outline_color=""):
        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'), highlightthickness=0)
        self.command = command; self.bg_color = bg_color; self.fg_color = fg_color; self.text = text
        self.w = width; self.h = height; self.r = radius; self.font_size = font_size
        self.bold = bold; self.outline_color = outline_color
        self.bind("<Enter>", lambda e: self.draw(hover=True))
        self.bind("<Leave>", lambda e: self.draw(hover=False))
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)
        self.draw()

    def draw(self, hover=False):
        self.delete("all")
        col = self._shift_color(self.bg_color, 15) if hover else self.bg_color
        out_col = self.outline_color if self.outline_color else ""
        if self.r > 0:
            rounded_rect(self, 1, 1, self.w-1, self.h-1, self.r, fill=col, outline=out_col)
        else:
            self.create_rectangle(0, 0, self.w, self.h, fill=col, outline=out_col)
            if hover: self.create_rectangle(0, self.h - 3, self.w, self.h, fill="#D4AF37", outline="")
            
        font_weight = "bold" if self.bold else "normal"
        y_adj = (self.h - 3) / 2 if self.r == 0 and hover else self.h / 2
        self.create_text(self.w / 2, y_adj, text=self.text, font=("Segoe UI", self.font_size, font_weight), fill=self.fg_color)

    def _shift_color(self, hex_color, amount):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        return f'#{min(255, r + amount):02x}{min(255, g + amount):02x}{min(255, b + amount):02x}'


# ----------------- Main App -----------------
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gebeta - The Traditional Ethiopian Game")
        self.root.geometry("1050x750")
        self.root.minsize(900, 650)

        self.c = {
            "bg": "#3E2723", "surface": "#5D4037", "card": "#111111", "border": "#8D6E63",
            "text": "#FFFFFF", "sub": "#AAAAAA", "accent": "#D4AF37", "p1": "#6D4C41", "p2": "#8D6E63", 
            "wood": "#795548", "pit": "#3E2723", "terracotta": "#E64A19", "green_accent": "#558B2F",
            "red_off": "#B71C1C", "black": "#1F1F1F", "glass": "#0A0A0A",
            "btn_idle": "#1A1A1A", "btn_hover": "#2D2D2D",
            "p1_color": "#689F38", "p2_color": "#D84315" # Distinct colors for ownership
        }

        self.sfx_on = True; self.music_on = True; self.amharic_on = False
        self.ai_delay = 500

        self.main_frame = tk.Frame(root, bg=self.c["bg"])
        self.main_frame.pack(expand=True, fill="both")
        
        self.container = tk.Frame(self.main_frame, bg=self.c["bg"])
        self.container.pack(expand=True, fill="both")

        self.gebeta_game = GebetaGame()
        self.gebeta_ai = None; self.is_vs_ai_gebeta = True
        self.hover_idx = -1; self.pit_coords = []; self.ai_thinking = False

        self._menu_bg_photo = None; self._game_bg_photo = None; self._wood_photo = None

        self.show_menu()

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def _draw_menu_bg(self, canvas, w, h):
        if menu_bg_raw is not None and w > 1 and h > 1:
            try:
                scaled = scale_cover_pil(menu_bg_raw, w, h)
                self._menu_bg_photo = ImageTk.PhotoImage(scaled)
                canvas.create_image(0, 0, image=self._menu_bg_photo, anchor="nw", tags="bg_img")
            except Exception: pass

    def _draw_game_bg(self, canvas, w, h):
        if game_bg_raw is not None and w > 1 and h > 1:
            try:
                scaled = scale_cover_pil(game_bg_raw, w, h)
                self._game_bg_photo = ImageTk.PhotoImage(scaled)
                canvas.create_image(0, 0, image=self._game_bg_photo, anchor="nw", tags="bg_img")
            except Exception: pass

    # ----------------- MAIN MENU -----------------
    def show_menu(self):
        if hasattr(self, 'header') and self.header.winfo_exists(): self.header.destroy()
        self.clear_container()
        self.container.pack_forget()
        self.container.pack(expand=True, fill="both")

        bg_canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        bg_canvas.pack(expand=True, fill="both")

        menu_bar = tk.Frame(bg_canvas, bg=self.c["black"], height=50)
        self.menu_window = bg_canvas.create_window(0, 0, window=menu_bar, anchor="nw")

        def draw_bg(event=None):
            w = bg_canvas.winfo_width(); h = bg_canvas.winfo_height()
            bg_canvas.coords(self.menu_window, 0, 0)
            menu_bar.config(width=w)
            self._draw_menu_bg(bg_canvas, w, h)

        bg_canvas.bind("<Configure>", draw_bg)

        HoverButton(menu_bar, "PLAY", self.show_mode_screen, self.c["black"], 
                    width=120, height=50, font_size=14, fg_color="white", outline_color="").pack(side="left", padx=(10, 0))
        HoverButton(menu_bar, "LEARN TO PLAY", self.show_rules, self.c["black"], 
                    width=160, height=50, font_size=14, fg_color="#AAAAAA", outline_color="").pack(side="left")
        HoverButton(menu_bar, "OUR STORY", self.show_history, self.c["black"], 
                    width=130, height=50, font_size=14, fg_color="#AAAAAA", outline_color="").pack(side="left")
        HoverButton(menu_bar, "SETTINGS", self.show_settings, self.c["black"], 
                    width=110, height=50, font_size=14, fg_color="#AAAAAA", outline_color="").pack(side="left")

    # ----------------- Info Screens -----------------
    def _show_text_screen(self, title, content_text):
        self.clear_container()
        bg_canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        bg_canvas.pack(expand=True, fill="both")

        def draw_bg(event=None):
            w = bg_canvas.winfo_width(); h = bg_canvas.winfo_height()
            self._draw_game_bg(bg_canvas, w, h)
            bg_canvas.delete("text_content")
            bg_canvas.create_text(w / 2, 80, text=title, font=("Segoe UI", 36, "bold"), fill="white", tags="text_content")
            bg_canvas.create_text(w / 2, h / 2, text=content_text, font=("Segoe UI", 14), fill="white", width=700, justify="left", tags="text_content")
            btn_x, btn_y = w / 2, h - 80
            rounded_rect(bg_canvas, btn_x-100, btn_y-20, btn_x+100, btn_y+20, 10, fill=self.c["black"], outline=self.c["border"], tags="text_content")
            bg_canvas.create_text(btn_x, btn_y, text="< BACK TO MENU", font=("Segoe UI", 14, "bold"), fill="white", tags="text_content")
            bg_canvas.tag_bind("text_content", "<Button-1>", lambda e: self.show_menu())

        bg_canvas.bind("<Configure>", draw_bg)

    def show_rules(self):
        rules_text = """OBJECTIVE:\nCapture more stones than your opponent.\n\nGAMEPLAY:\n1. Click a pit on your side to pick up stones.\n2. Sow them COUNTER-CLOCKWISE.\n3. If the last stone lands in a pit with stones, pick them up and continue (Relay Sowing).\n\nCAPTURE:\nIf your last stone lands in ANY pit and it contains EXACTLY 4 stones, you capture them.\n\nWINNING:\nThe game ends when a player cannot move. Remaining stones go to the pit owner's store. Highest score wins!"""
        self._show_text_screen("HOW TO PLAY", rules_text)

    def show_history(self):
        story_text = """Gebeta is a traditional Ethiopian board game played for generations. It belongs to the mancala family but features unique local rules.\n\nThe game is commonly played in homes, schools, and social gatherings. Players use stones, seeds, or small objects and a wooden board with carved holes.\n\nBeyond entertainment, Gebeta helps develop strategic thinking, planning, and decision-making skills. In Ethiopian culture, it is a social activity that brings people together and passes traditions from one generation to the next."""
        self._show_text_screen("OUR STORY", story_text)

    def show_settings(self):
        self.clear_container()
        bg_canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        bg_canvas.pack(expand=True, fill="both")

        overlay_frame = tk.Frame(bg_canvas, bg=self.c["black"], highlightthickness=0)
        window_id = bg_canvas.create_window(0, 0, window=overlay_frame, anchor="center")

        def draw_bg(event=None):
            w = bg_canvas.winfo_width(); h = bg_canvas.winfo_height()
            bg_canvas.coords(window_id, w / 2, h / 2)
            self._draw_game_bg(bg_canvas, w, h)

        bg_canvas.bind("<Configure>", draw_bg)

        tk.Label(overlay_frame, text="SETTINGS", font=("Segoe UI", 36, "bold"), bg=self.c["black"], fg="white").pack(pady=(0, 30))
        
        def create_toggle(parent, text, state_var, on_cmd):
            f = tk.Frame(parent, bg=self.c["black"])
            f.pack(fill="x", pady=10, padx=50)
            tk.Label(f, text=text, font=("Segoe UI", 14), bg=self.c["black"], fg="white").pack(side="left")
            current_col = self.c["green_accent"] if state_var else self.c["red_off"]
            current_txt = "ON" if state_var else "OFF"
            btn = HoverButton(f, current_txt, on_cmd, current_col, width=50, height=25, font_size=10, outline_color="", radius=6)
            btn.pack(side="right")

        def toggle_sfx(): self.sfx_on = not self.sfx_on; self.show_settings()
        def toggle_music(): self.music_on = not self.music_on; self.show_settings()
        def toggle_lang(): self.amharic_on = not self.amharic_on; self.show_settings()

        create_toggle(overlay_frame, "Sound Effects", self.sfx_on, toggle_sfx)
        create_toggle(overlay_frame, "Music", self.music_on, toggle_music)
        create_toggle(overlay_frame, "Amharic Language", self.amharic_on, toggle_lang)
        
        tk.Label(overlay_frame, text="AI Thinking Speed", font=("Segoe UI", 14), bg=self.c["black"], fg="white").pack(pady=(20, 5))
        speed_frame = tk.Frame(overlay_frame, bg=self.c["black"])
        speed_frame.pack()
        def set_speed(val): self.ai_delay = int(val)
        tk.Scale(speed_frame, from_=100, to=1500, orient=tk.HORIZONTAL, length=200, 
                  bg=self.c["black"], fg="white", highlightthickness=0, 
                  troughcolor="#333333", command=set_speed).set(self.ai_delay)

        HoverButton(overlay_frame, "< BACK TO MENU", self.show_menu, self.c["surface"],
                    width=200, height=45, font_size=14, fg_color="white", outline_color="", radius=8).pack(pady=(30, 0))

    # ----------------- Mode & Difficulty -----------------
    def show_mode_screen(self):
        self.clear_container()
        bg_canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        bg_canvas.pack(expand=True, fill="both")

        def update_center(event=None):
            w = bg_canvas.winfo_width(); h = bg_canvas.winfo_height()
            self._draw_game_bg(bg_canvas, w, h)
            bg_canvas.delete("ui_elements")
            bg_canvas.create_text(w / 2, h / 2 - 120, text="SELECT MODE", font=("Segoe UI", 42, "bold"), fill="white", tags="ui_elements")
            btn_y = h / 2; btn1_x = w / 2 - 130; btn2_x = w / 2 + 130
            rounded_rect(bg_canvas, btn1_x-110, btn_y-40, btn1_x+110, btn_y+40, 15, fill=self.c["btn_idle"], outline=self.c["border"], tags="ui_elements")
            bg_canvas.create_text(btn1_x, btn_y, text="VS  AI", font=("Segoe UI", 24, "bold"), fill="#CCCCCC", tags="ui_elements")
            rounded_rect(bg_canvas, btn2_x-110, btn_y-40, btn2_x+110, btn_y+40, 15, fill=self.c["btn_idle"], outline=self.c["border"], tags="ui_elements")
            bg_canvas.create_text(btn2_x, btn_y, text="PVP", font=("Segoe UI", 24, "bold"), fill="#CCCCCC", tags="ui_elements")
            back_y = h - 60
            rounded_rect(bg_canvas, w/2-100, back_y-20, w/2+100, back_y+20, 10, fill="#1A1A1A", outline="#333333", tags="ui_elements")
            bg_canvas.create_text(w/2, back_y, text="< BACK TO MENU", font=("Segoe UI", 14, "bold"), fill="white", tags="ui_elements")
            def check_click(e):
                if abs(e.x - btn1_x) < 110 and abs(e.y - btn_y) < 40: self.show_gebeta_diff_screen()
                elif abs(e.x - btn2_x) < 110 and abs(e.y - btn_y) < 40: self.start_gebeta(vs_ai=False, diff='medium')
                elif abs(e.x - w/2) < 100 and abs(e.y - back_y) < 20: self.show_menu()
            bg_canvas.unbind("<Button-1>")
            bg_canvas.bind("<Button-1>", check_click)
        bg_canvas.bind("<Configure>", update_center)

    def show_gebeta_diff_screen(self):
        self.clear_container()
        bg_canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        bg_canvas.pack(expand=True, fill="both")

        def update_center(event=None):
            w = bg_canvas.winfo_width(); h = bg_canvas.winfo_height()
            self._draw_game_bg(bg_canvas, w, h)
            bg_canvas.delete("ui_elements")
            bg_canvas.create_text(w / 2, h / 2 - 130, text="SELECT DIFFICULTY", font=("Segoe UI", 42, "bold"), fill="white", tags="ui_elements")
            btn_y = h / 2; btn1_x = w / 2 - 220; btn2_x = w / 2; btn3_x = w / 2 + 220
            for bx, label, diff in [(btn1_x, "EASY", 'easy'), (btn2_x, "MEDIUM", 'medium'), (btn3_x, "HARD", 'hard')]:
                rounded_rect(bg_canvas, bx-90, btn_y-40, bx+90, btn_y+40, 15, fill=self.c["btn_idle"], outline=self.c["border"], tags="ui_elements")
                bg_canvas.create_text(bx, btn_y, text=label, font=("Segoe UI", 22, "bold"), fill="#CCCCCC", tags="ui_elements")
            back_y = h - 60
            rounded_rect(bg_canvas, w/2-100, back_y-20, w/2+100, back_y+20, 10, fill="#1A1A1A", outline="#333333", tags="ui_elements")
            bg_canvas.create_text(w/2, back_y, text="< BACK", font=("Segoe UI", 14, "bold"), fill="white", tags="ui_elements")
            def check_click(e):
                if abs(e.x - btn1_x) < 90 and abs(e.y - btn_y) < 40: self.start_gebeta(True, 'easy')
                elif abs(e.x - btn2_x) < 90 and abs(e.y - btn_y) < 40: self.start_gebeta(True, 'medium')
                elif abs(e.x - btn3_x) < 90 and abs(e.y - btn_y) < 40: self.start_gebeta(True, 'hard')
                elif abs(e.x - w/2) < 100 and abs(e.y - back_y) < 20: self.show_mode_screen()
            bg_canvas.unbind("<Button-1>")
            bg_canvas.bind("<Button-1>", check_click)
        bg_canvas.bind("<Configure>", update_center)

    # ----------------- GEBETA GAME UI -----------------
    def start_gebeta(self, vs_ai, diff):
        self.clear_container()
        self.is_vs_ai_gebeta = vs_ai; self.gebeta_game.reset_board()
        self.ai_thinking = False; self.hover_idx = -1
        if self.is_vs_ai_gebeta: self.gebeta_ai = GebetaAI(difficulty=diff)

        if hasattr(self, 'header') and self.header.winfo_exists(): self.header.destroy()

        self.header = tk.Frame(self.main_frame, bg=self.c["black"], height=80)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)
        
        HoverButton(self.header, "MENU", self.show_menu, self.c["surface"], width=70, height=30, font_size=10, outline_color="").pack(side="left", padx=15, pady=25)

        p1f = tk.Frame(self.header, bg=self.c["black"])
        p1f.pack(side="left", padx=20)
        tk.Label(p1f, text="PLAYER 1", font=("Segoe UI", 9), bg=self.c["black"], fg=self.c["p1_color"]).pack()
        self.p1_lbl = tk.Label(p1f, text="0", font=("Segoe UI", 28, "bold"), bg=self.c["black"], fg=self.c["p1_color"])
        self.p1_lbl.pack()

        self.turn_lbl = tk.Label(self.header, text="Player 1's Turn", font=("Segoe UI", 20, "bold"),
                                 bg=self.c["black"], fg=self.c["text"])
        self.turn_lbl.pack(side="left", expand=True)

        p2f = tk.Frame(self.header, bg=self.c["black"])
        p2f.pack(side="right", padx=20)
        p2_text = "PLAYER 2 (AI)" if self.is_vs_ai_gebeta else "PLAYER 2"
        tk.Label(p2f, text=p2_text, font=("Segoe UI", 9), bg=self.c["black"], fg=self.c["p2_color"]).pack()
        self.p2_lbl = tk.Label(p2f, text="0", font=("Segoe UI", 28, "bold"), bg=self.c["black"], fg=self.c["p2_color"])
        self.p2_lbl.pack()

        HoverButton(self.header, "RESTART", self.restart_gebeta, self.c["surface"], width=80, height=30, font_size=10, outline_color="").pack(side="right", padx=5, pady=25)

        self.canvas = tk.Canvas(self.container, bg=self.c["bg"], highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())
        self.pit_coords = []

    def restart_gebeta(self):
        self.gebeta_game.reset_board(); self.ai_thinking = False
        self.p1_lbl.config(text="0"); self.p2_lbl.config(text="0")
        self.turn_lbl.config(text="Player 1's Turn", fg=self.c["text"])
        self.draw_board()

    def on_click(self, event):
        if self.gebeta_game.game_over or self.ai_thinking: return
        if self.is_vs_ai_gebeta and self.gebeta_game.current_player == 2: return
        for (x, y, idx) in self.pit_coords:
            if (event.x - x) ** 2 + (event.y - y) ** 2 < 38 ** 2:
                if self.gebeta_game.owners[idx] == self.gebeta_game.current_player and self.gebeta_game.board[idx] > 0:
                    self.exec_move(idx)
                return

    def exec_move(self, idx):
        game_over, _, _ = self.gebeta_game.make_move(idx)
        self.draw_board(); self.update_scores()
        if game_over: self.show_end_screen(); return
        if self.is_vs_ai_gebeta and self.gebeta_game.current_player == 2:
            self.ai_thinking = True; self.dots = 0; self.anim_ai()
            self.root.after(self.ai_delay, self.ai_turn)

    def anim_ai(self):
        if self.ai_thinking:
            self.dots = (self.dots % 3) + 1
            self.turn_lbl.config(text="AI Thinking" + "." * self.dots, fg=self.c["terracotta"])
            self.root.after(300, self.anim_ai)

    def ai_turn(self):
        if self.gebeta_game.game_over: return
        move = self.gebeta_ai.get_best_move(self.gebeta_game)
        if move is not None: self.gebeta_game.make_move(move)
        self.ai_thinking = False; self.draw_board(); self.update_scores()
        if not self.gebeta_game.game_over and self.is_vs_ai_gebeta and self.gebeta_game.current_player == 2:
            self.ai_thinking = True; self.dots = 0; self.anim_ai()
            self.root.after(self.ai_delay, self.ai_turn)
        elif self.gebeta_game.game_over: self.show_end_screen()
        else: self.turn_lbl.config(text="Your Turn", fg=self.c["text"])

    def update_scores(self):
        self.p1_lbl.config(text=str(self.gebeta_game.scores[1]))
        self.p2_lbl.config(text=str(self.gebeta_game.scores[2]))

    def show_end_screen(self):
        p1, p2 = self.gebeta_game.scores[1], self.gebeta_game.scores[2]
        if p1 > p2: msg, color = "YOU WIN!", self.c["green_accent"]
        elif p2 > p1 and self.is_vs_ai_gebeta: msg, color = "AI WINS!", self.c["terracotta"]
        elif p2 > p1: msg, color = "PLAYER 2 WINS!", self.c["terracotta"]
        else: msg, color = "IT'S A TIE!", self.c["accent"]
        
        self.turn_lbl.config(text=msg, fg=color)
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w/2, h/2
        
        rounded_rect(self.canvas, cx-220, cy-110, cx+220, cy+110, 40, fill=self.c["card"], outline=self.c["accent"], width=3)
        self.canvas.create_text(cx, cy-40, text=msg, font=("Segoe UI", 36, "bold"), fill=color)
        self.canvas.create_text(cx, cy+10, text=f"P1: {p1}  |  P2: {p2}", font=("Segoe UI", 16), fill=self.c["text"])
        
        rounded_rect(self.canvas, cx-70, cy+45, cx+70, cy+85, 10, fill=self.c["black"], outline=self.c["accent"])
        self.canvas.create_text(cx, cy+65, text="PLAY AGAIN", font=("Segoe UI", 13, "bold"), fill=self.c["text"], tags="end_btn")
        self.canvas.tag_bind("end_btn", "<Button-1>", lambda e: self.restart_gebeta())

    def draw_board(self):
        self.canvas.delete("all"); self.pit_coords = []
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50: return
        self._draw_game_bg(self.canvas, w, h)

        bw, bh = min(w * 0.65, 600), min(h * 0.75, 380)
        cx, cy = w / 2, h / 2; bx, by = cx - bw / 2, cy - bh / 2
        store_offset = 90; left_store_x = bx - store_offset; right_store_x = bx + bw + store_offset
        total_bx = left_store_x - 60; total_b_end = right_store_x + 60
        
        # Procedural Wood Texture Background for the Board
        if wood_texture_raw:
            try:
                resized_wood = wood_texture_raw.resize((int(total_b_end - total_bx), int(bh)), Image.LANCZOS)
                self._wood_photo = ImageTk.PhotoImage(resized_wood)
                # Shadow
                rounded_rect(self.canvas, total_bx+6, by+6, total_b_end-6, by+bh-6, 20, fill="#1a0e0a", outline="")
                self.canvas.create_image(total_bx, by, image=self._wood_photo, anchor="nw")
            except Exception:
                pass
        
        # Board Borders
        rounded_rect(self.canvas, total_bx, by, total_b_end, by+bh, 20, fill="", outline=self.c["border"], width=4)
        self.canvas.create_line(bx, cy, bx + bw, cy, fill=self.c["border"], width=2, dash=(6, 6))

        spacing = bw / 7
        for i in range(6): self.draw_pit(bx + spacing * (i + 1), cy - 70, 11 - i)
        for i in range(6): self.draw_pit(bx + spacing * (i + 1), cy + 70, i)

        self.draw_store_pit(left_store_x, cy, 1); self.draw_store_pit(right_store_x, cy, 2)

        if not self.gebeta_game.game_over and not self.ai_thinking:
            txt = "Your Turn" if self.is_vs_ai_gebeta and self.gebeta_game.current_player == 1 else f"Player {self.gebeta_game.current_player}'s Turn"
            self.turn_lbl.config(text=txt, fg=self.c["text"])

    def draw_store_pit(self, x, y, player):
        score = self.gebeta_game.scores[player]
        owner_color = self.c["p1_color"] if player == 1 else self.c["p2_color"]
        
        self.canvas.create_oval(x-45, y-85, x+45, y+85, fill="#1a0e0a", outline="")
        self.canvas.create_oval(x-42, y-82, x+42, y+82, fill=self.c["pit"], outline=owner_color, width=3)

        if score > 0:
            for i in range(min(score, 8)):
                a = (i / 8) * 2 * math.pi; sx = x + 20 * math.cos(a); sy = y + 45 * math.sin(a)
                self.canvas.create_oval(sx-6, sy-6, sx+6, sy+6, fill=self.c["accent"], outline="#bba040")
            if score > 8:
                for i in range(min(score - 8, 6)):
                    a = (i / 6) * 2 * math.pi + 0.5; sx = x + 9 * math.cos(a); sy = y + 18 * math.sin(a)
                    self.canvas.create_oval(sx-6, sy-6, sx+6, sy+6, fill=self.c["accent"], outline="#bba040")
        self.canvas.create_text(x, y, text=str(score), font=("Segoe UI", 30, "bold"), fill=self.c["text"])

    def draw_pit(self, x, y, idx):
        owner, count = self.gebeta_game.owners[idx], self.gebeta_game.board[idx]
        owner_color = self.c["p1_color"] if owner == 1 else self.c["p2_color"]
        
        if idx == self.hover_idx and owner == self.gebeta_game.current_player and count > 0:
            if not (self.is_vs_ai_gebeta and self.gebeta_game.current_player == 2):
                self.canvas.create_oval(x-40, y-40, x+40, y+40, outline=self.c["accent"], width=3, dash=(4, 2))

        self.canvas.create_oval(x-38, y-38, x+38, y+38, fill="#1a0e0a", outline="")
        self.canvas.create_oval(x-35, y-35, x+35, y+35, fill=self.c["pit"], outline=owner_color, width=3)

        sr = 8; pos = []
        if count > 0:
            if count <= 6:
                rr = 18
                for i in range(count):
                    a = (i / count) * 2 * math.pi - math.pi / 2; pos.append((x + rr * math.cos(a), y + rr * math.sin(a)))
            else:
                pos.append((x, y)); rr = 20
                for i in range(8):
                    a = (i / 8) * 2 * math.pi; pos.append((x + rr * math.cos(a), y + rr * math.sin(a)))

        for sx, sy in pos:
            self.canvas.create_oval(sx-sr+2, sy-sr+2, sx+sr+2, sy+sr+2, fill="black", outline="")
            self.canvas.create_oval(sx-sr, sy-sr, sx+sr, sy+sr, fill=self.c["accent"], outline="#bba040")

        t_col = self.c["text"] if count <= 9 else self.c["terracotta"]
        self.canvas.create_text(x, y, text=str(count), font=("Segoe UI", 12, "bold"), fill=t_col)
        self.pit_coords.append((x, y, idx))

    def on_hover(self, event):
        if self.gebeta_game.game_over or self.ai_thinking: return
        f = -1
        for x, y, i in self.pit_coords:
            if (event.x - x) ** 2 + (event.y - y) ** 2 < 38 ** 2: f = i; break
        if f != self.hover_idx: self.hover_idx = f; self.draw_board()

    def on_leave(self, event):
        if self.hover_idx != -1: self.hover_idx = -1; self.draw_board()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
