import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont
import random
import pygame
import math
import time
import os

# ==========================================
# 🎮 ASSET CONFIGURATION VARIABLES
# ==========================================

SOUND_LASER_PLAYER   = "sounds/player_laser.mp3"
SOUND_SHIP_BLAST     = "sounds/ship_blast.mp3"
SOUND_BOSS_LASER     = "sounds/boss_laser.mp3"
SOUND_VICTORY_GAME   = "sounds/victory_game.mp3"
SOUND_VICTORY_LEVEL  = "sounds/victory_level.mp3"
SOUND_GAME_ENTRY     = "sounds/game_entry.mp3"
SOUND_POWERUP_GRAB   = "sounds/powerup_grab.mp3"

IMG_PLAYER_SHIP      = "images/player.png"
IMG_ENEMY_SHIP       = "images/enemy.png"
IMG_BOSS_SHIP        = "images/boss.png"
IMG_MEGA_BOSS_SHIP   = "images/mega_boss.png"
IMG_PLAYER_BLAST     = "images/player_blast.png"
IMG_ENEMY_BLAST      = "images/enemy_blast.png"
IMG_BOSS_BLAST       = "images/boss_blast.png"
IMG_POWERUP_SPEED    = "images/pu_speed.png"
IMG_POWERUP_SHIELD   = "images/pu_shield.png"
IMG_POWERUP_DOUBLE   = "images/pu_double_laser.png"
IMG_POWERUP_HEALTH   = "images/pu_health.png"
IMG_BG_LEVEL_1       = "images/bg_level_1.png"
IMG_BG_LEVEL_2       = "images/bg_level_2.png"
IMG_BG_LEVEL_3       = "images/bg_level_3.png"
IMG_BG_LEVEL_4       = "images/bg_level_4.png"
IMG_BG_LEVEL_5       = "images/bg_level_5.png"

# ==========================================
# 🎨 COLOUR PALETTE
# ==========================================
CLR_BG        = "#05060F"   # near-black deep space
CLR_PANEL     = "#0A0D1E"   # slightly lighter for panels
CLR_BORDER    = "#1A2040"   # subtle border
CLR_ACCENT    = "#00D4FF"   # electric cyan
CLR_ACCENT2   = "#FF3CAC"   # magenta
CLR_GOLD      = "#FFD700"
CLR_GREEN     = "#00FF88"
CLR_RED       = "#FF2244"
CLR_TEXT      = "#C8D8FF"
CLR_DIM       = "#3A4A6A"


# ==========================================
# 🖼  DRAWING HELPERS
# ==========================================

def make_star_bg(w, h, n_stars=220):
    """Generate a procedural starfield as a PIL Image."""
    img = Image.new("RGBA", (w, h), (5, 6, 15, 255))
    draw = ImageDraw.Draw(img)
    for _ in range(n_stars):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        r = random.random()
        if r < 0.6:
            brightness = random.randint(100, 180)
            draw.point((x, y), fill=(brightness, brightness, brightness + 20, 255))
        elif r < 0.9:
            brightness = random.randint(180, 255)
            sz = 1
            draw.ellipse((x - sz, y - sz, x + sz, y + sz),
                         fill=(brightness, brightness, 255, 255))
        else:
            draw.ellipse((x - 1, y - 1, x + 1, y + 1),
                         fill=(255, 220, 100, 255))
    # Nebula clouds
    for _ in range(4):
        cx, cy = random.randint(0, w), random.randint(0, h)
        r_val = random.choice([(0, 60, 120), (60, 0, 90), (0, 80, 60)])
        for radius in range(80, 10, -10):
            alpha = int(18 * (1 - radius / 80))
            color = (*r_val, alpha)
            draw.ellipse((cx - radius, cy - radius * 0.6,
                          cx + radius, cy + radius * 0.6), fill=color)
    return img


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius,
                            fill=fill, outline=outline, width=width)


def make_panel_image(w, h, bg_color, border_color, radius=12, border_width=2,
                     glow_color=None, glow_alpha=60):
    """Craft a frosted-glass-style panel as a PhotoImage."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Glow halo
    if glow_color:
        for i in range(8, 0, -1):
            gc = (*glow_color, glow_alpha // i)
            draw.rounded_rectangle((-i * 2, -i * 2, w + i * 2, h + i * 2),
                                    radius=radius + i * 2, fill=gc)
    # Fill
    r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius,
                            fill=(r, g, b, 210))
    # Border
    if border_color:
        r2, g2, b2 = int(border_color[1:3], 16), int(border_color[3:5], 16), int(border_color[5:7], 16)
        draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius,
                                outline=(r2, g2, b2, 255), width=border_width)
    return ImageTk.PhotoImage(img)


def hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ==========================================
# 🚀 MAIN GAME CLASS
# ==========================================

class SpaceShooter(ttk.Window):
    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("GALACTIC DEFENDER")
        self.geometry("860x760")
        self.resizable(False, False)
        self.configure(bg=CLR_BG)

        pygame.mixer.init()

        self.current_level  = 1
        self.score          = 0
        self.inventory      = []
        self.mega_boss_health = 200
        self.active_keys    = {"Left": False, "Right": False}

        # Starfield shared across menus
        self._star_bg_img   = None

        self.load_assets()
        self.show_main_menu()

    # ──────────────────────────────────────
    # ASSET LOADING
    # ──────────────────────────────────────

    def load_assets(self):
        self.images = {}

        def _open_or_placeholder(path, size, color):
            if os.path.exists(path):
                return Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((2, 2, size[0]-2, size[1]-2), fill=color)
            return img

        def rot(img, deg):
            return img.rotate(deg, expand=False)

        self.images["player"]    = ImageTk.PhotoImage(rot(_open_or_placeholder(IMG_PLAYER_SHIP,   (70,  70),  "#00AAFF"), 90))
        self.images["enemy"]     = ImageTk.PhotoImage(rot(_open_or_placeholder(IMG_ENEMY_SHIP,    (55,  55),  "#FF4444"), 90))
        self.images["boss"]      = ImageTk.PhotoImage(rot(_open_or_placeholder(IMG_BOSS_SHIP,     (130, 130), "#FF8800"), 90))
        self.images["mega_boss"] = ImageTk.PhotoImage(rot(_open_or_placeholder(IMG_MEGA_BOSS_SHIP,(180, 180), "#FF00FF"), 90))

        bg_paths = [IMG_BG_LEVEL_1, IMG_BG_LEVEL_2, IMG_BG_LEVEL_3, IMG_BG_LEVEL_4, IMG_BG_LEVEL_5]
        bg_tints = [(0,20,60),(10,0,50),(20,10,40),(30,0,30),(40,0,20)]
        for i, (path, tint) in enumerate(zip(bg_paths, bg_tints), start=1):
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA").resize((800, 600), Image.LANCZOS)
            else:
                img = make_star_bg(800, 600)
                # Add level tint overlay
                overlay = Image.new("RGBA", (800, 600), (*tint, 80))
                img = Image.alpha_composite(img, overlay)
            self.images[f"bg_level_{i}"] = ImageTk.PhotoImage(img)

        # Shared starfield for menus (860×760)
        star_pil = make_star_bg(860, 760, n_stars=300)
        self._star_bg_pil   = star_pil
        self._star_bg_img   = ImageTk.PhotoImage(star_pil)

    def play_sound(self, path):
        if os.path.exists(path):
            try:
                pygame.mixer.Sound(path).play()
            except Exception:
                pass

    # ──────────────────────────────────────
    # SHARED BACKGROUND CANVAS
    # ──────────────────────────────────────

    def _make_bg_canvas(self, w, h):
        """Return a canvas filled with the starfield."""
        c = tk.Canvas(self, width=w, height=h, bg=CLR_BG,
                      highlightthickness=0, bd=0)
        c.place(x=0, y=0)
        c.create_image(0, 0, anchor="nw", image=self._star_bg_img)
        return c

    # ──────────────────────────────────────
    # REUSABLE WIDGETS
    # ──────────────────────────────────────

    def _neon_label(self, parent, text, size=14, color=CLR_ACCENT, bold=True, **kw):
        weight = "bold" if bold else "normal"
        lbl = tk.Label(parent, text=text,
                       font=("Courier New", size, weight),
                       fg=color, bg=CLR_BG, **kw)
        return lbl

    def _glow_button(self, parent, text, command, w=220, accent=CLR_ACCENT):
        """A canvas-drawn neon button with hover animation."""
        btn_h = 46
        f = tk.Frame(parent, bg=CLR_BG)

        c = tk.Canvas(f, width=w, height=btn_h, bg=CLR_BG,
                      highlightthickness=0, cursor="hand2")
        c.pack()

        r, g, b = hex_to_rgb(accent)

        def _draw(hovered=False):
            c.delete("all")
            alpha_fill = 180 if hovered else 100
            # Border glow layers
            for i in range(5, 0, -1):
                glow_a = int(60 / i) if hovered else int(30 / i)
                c.create_rectangle(i, i, w - i, btn_h - i,
                                   outline=accent, width=1)
            c.create_rectangle(2, 2, w - 2, btn_h - 2,
                               fill=CLR_PANEL if hovered else CLR_BG,
                               outline=accent, width=2)
            fg = "white" if hovered else accent
            c.create_text(w // 2, btn_h // 2, text=text,
                          font=("Courier New", 12, "bold"),
                          fill=fg, anchor="center")

        _draw(False)
        c.bind("<Enter>",    lambda e: _draw(True))
        c.bind("<Leave>",    lambda e: _draw(False))
        c.bind("<Button-1>", lambda e: command())
        return f

    # ──────────────────────────────────────
    # SCREENS
    # ──────────────────────────────────────

    def show_main_menu(self):
        self.clear_window()
        bg = self._make_bg_canvas(860, 760)

        # ── Animated title ──
        title_y = [80]
        title_id = bg.create_text(430, 80, text="GALACTIC DEFENDER",
                                  font=("Courier New", 38, "bold"),
                                  fill=CLR_ACCENT, anchor="center")
        sub_id   = bg.create_text(430, 125, text="★  INTERSTELLAR COMBAT SIMULATOR  ★",
                                  font=("Courier New", 11),
                                  fill=CLR_DIM, anchor="center")

        # Glow pulse
        _pulse = [0]
        def _animate_title():
            v  = math.sin(time.time() * 2) * 0.5 + 0.5
            r  = int(0   + v * 0)
            g  = int(180 + v * 75)
            b  = int(210 + v * 45)
            col = f"#{r:02x}{g:02x}{b:02x}"
            bg.itemconfig(title_id, fill=col)
            bg.after(30, _animate_title)
        _animate_title()

        # ── Decorative horizontal rules ──
        for y_rule in (145, 155):
            bg.create_line(120, y_rule, 740, y_rule, fill=CLR_BORDER, width=1)
        bg.create_line(120, 150, 740, 150, fill=CLR_ACCENT, width=1)

        # ── Ship silhouette (decorative) ──
        bg.create_text(430, 260, text="▲", font=("Courier New", 60),
                       fill="#0D1A3A", anchor="center")
        bg.create_text(430, 258, text="▲", font=("Courier New", 48),
                       fill=CLR_ACCENT, anchor="center")

        # ── Level badges / stats strip ──
        for i, (lvl, color) in enumerate(
            [("LVL 1", CLR_GREEN), ("LVL 2", CLR_ACCENT), ("LVL 3", CLR_GOLD),
             ("LVL 4", "#FF8800"), ("LVL 5", CLR_ACCENT2)]):
            x = 160 + i * 110
            bg.create_rectangle(x - 35, 340, x + 35, 370,
                                 fill=CLR_PANEL, outline=color, width=1)
            bg.create_text(x, 355, text=lvl, font=("Courier New", 10, "bold"),
                           fill=color)

        bg.create_text(430, 395, text="5 STAGES • BOSS BATTLES • REDROXX AWAITS",
                       font=("Courier New", 10), fill=CLR_DIM)

        # ── Buttons ──
        btn_frame = tk.Frame(bg, bg=CLR_BG)
        bg.create_window(430, 480, window=btn_frame, anchor="center")

        for label, cmd, accent in [
            ("▶  START MISSION",  self.show_instructions, CLR_GREEN),
            ("✕  ABORT",          self.destroy,           CLR_RED),
        ]:
            b = self._glow_button(btn_frame, label, cmd, w=260, accent=accent)
            b.pack(pady=8)

        # ── Footer ──
        bg.create_text(430, 720, text="USE ARROW KEYS TO MOVE  •  SPACE TO FIRE  •  1/2/3 FOR POWER-UPS",
                       font=("Courier New", 9), fill=CLR_DIM)

    # ──────────────────────────────────────

    def show_instructions(self):
        self.clear_window()
        bg = self._make_bg_canvas(860, 760)

        bg.create_text(430, 55, text="MISSION BRIEFING",
                       font=("Courier New", 28, "bold"), fill=CLR_GOLD)
        bg.create_line(140, 80, 720, 80, fill=CLR_GOLD, width=1)

        lines = [
            ("←  →",         "Move ship left / right"),
            ("SPACE",         "Fire laser cannon"),
            ("1 / 2 / 3",     "Activate stored power-up"),
            ("",              ""),
            ("◉ ENEMIES",     "Destroy them before they pass you"),
            ("◉ BOSSES",      "Appear at levels 4 & 5  —  high HP"),
            ("◉ MEGA BOSS",   "'THE REDROXX'  —  final challenge"),
            ("◉ POWER-UPS",   "Pick up for speed, shield, or heal"),
        ]

        for i, (key, desc) in enumerate(lines):
            y = 130 + i * 50
            if not key:
                bg.create_line(180, y, 680, y, fill=CLR_BORDER, width=1)
                continue
            color = CLR_ACCENT if i < 3 else CLR_TEXT
            bg.create_rectangle(180, y - 16, 340, y + 16,
                                 fill=CLR_PANEL, outline=CLR_BORDER)
            bg.create_text(260, y, text=key, font=("Courier New", 12, "bold"),
                           fill=CLR_GOLD)
            bg.create_text(360, y, text=desc, font=("Courier New", 12),
                           fill=color, anchor="w")

        f = tk.Frame(bg, bg=CLR_BG)
        bg.create_window(430, 660, window=f)
        b = self._glow_button(f, "⚡  LAUNCH MISSION", self.start_game,
                              w=260, accent=CLR_ACCENT2)
        b.pack()

    # ──────────────────────────────────────

    def show_level_clear(self):
        self.play_sound(SOUND_VICTORY_LEVEL)
        # Overlay message on existing canvas
        self.canvas.create_rectangle(200, 260, 600, 380,
                                     fill=CLR_PANEL, outline=CLR_ACCENT, width=2,
                                     tags="popup")
        self.canvas.create_text(400, 300,
                                text=f"✦  STAGE {self.current_level} CLEARED  ✦",
                                font=("Courier New", 22, "bold"),
                                fill=CLR_ACCENT, tags="popup")
        self.canvas.create_text(400, 340,
                                text=f"Score: {self.score}",
                                font=("Courier New", 14),
                                fill=CLR_GOLD, tags="popup")
        self.current_level += 1
        self.after(3000, self.start_level)

    # ──────────────────────────────────────

    def show_victory_screen(self):
        self.clear_window()
        self.play_sound(SOUND_VICTORY_GAME)
        bg = self._make_bg_canvas(860, 760)

        # Gold burst
        for angle in range(0, 360, 15):
            x2 = 430 + 200 * math.cos(math.radians(angle))
            y2 = 330 + 200 * math.sin(math.radians(angle))
            bg.create_line(430, 330, x2, y2, fill=CLR_GOLD,
                           width=1 if angle % 30 else 2)

        bg.create_text(430, 200, text="VICTORY!",
                       font=("Courier New", 52, "bold"), fill=CLR_GOLD)
        bg.create_text(430, 260, text="THE REDROXX HAS BEEN DEFEATED",
                       font=("Courier New", 14), fill=CLR_ACCENT)

        msg_lines = [
            "Congratulations, Commander.",
            "You've defended the galaxy from certain doom.",
            "Your legend will echo across the stars.",
            "",
            f"FINAL SCORE:  {self.score}",
        ]
        for i, line in enumerate(msg_lines):
            col = CLR_GOLD if "SCORE" in line else CLR_TEXT
            bg.create_text(430, 360 + i * 34, text=line,
                           font=("Courier New", 13 if "SCORE" not in line else 16,
                                 "bold" if "SCORE" in line else "normal"),
                           fill=col)

        f = tk.Frame(bg, bg=CLR_BG)
        bg.create_window(430, 600, window=f)
        self._glow_button(f, "⟳  PLAY AGAIN", self.start_game,
                          w=220, accent=CLR_GREEN).pack(pady=6)
        self._glow_button(f, "⌂  MAIN MENU", self.show_main_menu,
                          w=220, accent=CLR_ACCENT).pack(pady=6)

    # ──────────────────────────────────────

    def trigger_game_over(self):
        self.is_running = False
        self.play_sound(SOUND_SHIP_BLAST)
        self.clear_window()
        bg = self._make_bg_canvas(860, 760)

        bg.create_text(430, 220, text="SHIP DESTROYED",
                       font=("Courier New", 44, "bold"), fill=CLR_RED)
        bg.create_text(430, 280, text="— MISSION FAILED —",
                       font=("Courier New", 16), fill=CLR_DIM)

        # Score box
        bg.create_rectangle(280, 330, 580, 410,
                            fill=CLR_PANEL, outline=CLR_RED, width=2)
        bg.create_text(430, 355, text="FINAL SCORE",
                       font=("Courier New", 12), fill=CLR_DIM)
        bg.create_text(430, 385, text=str(self.score),
                       font=("Courier New", 28, "bold"), fill=CLR_GOLD)

        f = tk.Frame(bg, bg=CLR_BG)
        bg.create_window(430, 530, window=f)
        self._glow_button(f, "⟳  TRY AGAIN",   self.start_game,      w=220, accent=CLR_ACCENT).pack(pady=6)
        self._glow_button(f, "⌂  MAIN MENU",   self.show_main_menu,  w=220, accent=CLR_DIM).pack(pady=6)

    # ──────────────────────────────────────
    # GAMEPLAY
    # ──────────────────────────────────────

    def start_game(self):
        self.current_level    = 1
        self.score            = 0
        self.inventory        = []
        self.mega_boss_health = 200
        self.active_keys      = {"Left": False, "Right": False}
        self.start_level()

    def start_level(self):
        self.clear_window()

        # ── HUD frame ──
        hud = tk.Frame(self, bg=CLR_PANEL, height=54)
        hud.pack(fill=X, padx=0, pady=0)
        hud.pack_propagate(False)

        # Left cluster
        left = tk.Frame(hud, bg=CLR_PANEL)
        left.pack(side=LEFT, padx=14, pady=6)

        tk.Label(left, text="HP", font=("Courier New", 9, "bold"),
                 fg=CLR_DIM, bg=CLR_PANEL).grid(row=0, column=0, sticky="w")
        self.hp_bar_var = tk.IntVar(value=100)
        self.hp_bar = ttk.Progressbar(left, length=140, maximum=100,
                                       variable=self.hp_bar_var,
                                       bootstyle="danger-striped")
        self.hp_bar.grid(row=1, column=0, sticky="w")
        self.lbl_health = tk.Label(left, text="100 / 100",
                                   font=("Courier New", 9),
                                   fg=CLR_GREEN, bg=CLR_PANEL)
        self.lbl_health.grid(row=2, column=0, sticky="w")

        # Centre cluster
        centre = tk.Frame(hud, bg=CLR_PANEL)
        centre.pack(side=LEFT, expand=True)

        self.lbl_level = tk.Label(centre,
                                  text=f"◈  STAGE {self.current_level} / 5  ◈",
                                  font=("Courier New", 13, "bold"),
                                  fg=CLR_ACCENT, bg=CLR_PANEL)
        self.lbl_level.pack()
        self.lbl_score = tk.Label(centre,
                                  text=f"SCORE  {self.score:06d}",
                                  font=("Courier New", 11),
                                  fg=CLR_GOLD, bg=CLR_PANEL)
        self.lbl_score.pack()

        # Right cluster — inventory
        right = tk.Frame(hud, bg=CLR_PANEL)
        right.pack(side=RIGHT, padx=14, pady=6)
        tk.Label(right, text="POWER-UPS", font=("Courier New", 9, "bold"),
                 fg=CLR_DIM, bg=CLR_PANEL).pack(anchor="e")
        self.lbl_inv = tk.Label(right, text="[EMPTY]",
                                font=("Courier New", 10),
                                fg=CLR_ACCENT2, bg=CLR_PANEL)
        self.lbl_inv.pack(anchor="e")

        # Thin neon underline
        sep = tk.Canvas(self, height=3, bg=CLR_BG, highlightthickness=0)
        sep.pack(fill=X)
        sep.create_line(0, 1, 860, 1, fill=CLR_ACCENT, width=2)

        # ── Game canvas ──
        self.canvas = tk.Canvas(self, width=800, height=600,
                                bg=CLR_BG, highlightthickness=0)
        self.canvas.pack(pady=0)

        bg_key = f"bg_level_{self.current_level}"
        if bg_key in self.images:
            self.canvas.create_image(400, 300, image=self.images[bg_key])

        # ── Player ──
        self.player_health = 100
        self.player_id = self.canvas.create_image(400, 520,
                                                   image=self.images["player"])

        self.enemies  = []
        self.lasers   = []
        self.powerups = []

        self.setup_level_data()

        self.bind("<KeyPress-Left>",    lambda e: self.active_keys.update({"Left":  True}))
        self.bind("<KeyRelease-Left>",  lambda e: self.active_keys.update({"Left":  False}))
        self.bind("<KeyPress-Right>",   lambda e: self.active_keys.update({"Right": True}))
        self.bind("<KeyRelease-Right>", lambda e: self.active_keys.update({"Right": False}))
        self.bind("<space>",            lambda e: self.fire_laser())
        self.bind("1",                  lambda e: self.use_powerup(0))
        self.bind("2",                  lambda e: self.use_powerup(1))
        self.bind("3",                  lambda e: self.use_powerup(2))

        self.is_running = True
        self.game_loop()

    # ──────────────────────────────────────

    def setup_level_data(self):
        self.boss_spawned      = False
        self.mega_boss_spawned = False

        config = {
            1: (8,  2, False),
            2: (12, 3, True),
            3: (16, 4, True),
            4: (10, 4, True),
            5: (8,  4, True),
        }
        to_spawn, spd, can_fire = config.get(self.current_level, (8, 3, True))
        self.enemies_to_spawn = to_spawn
        self.enemy_speed      = spd
        self.can_enemies_fire = can_fire

    # ──────────────────────────────────────

    def move_player(self, dx):
        coords = self.canvas.coords(self.player_id)
        if not coords:
            return
        nx = coords[0] + dx
        if 35 < nx < 765:
            self.canvas.move(self.player_id, dx, 0)

    def fire_laser(self):
        if not self.is_running:
            return
        self.play_sound(SOUND_LASER_PLAYER)
        coords = self.canvas.coords(self.player_id)
        if coords:
            lid = self.canvas.create_line(
                coords[0], coords[1] - 35,
                coords[0], coords[1] - 55,
                fill=CLR_ACCENT, width=3, tags="player_laser"
            )
            self.lasers.append({"id": lid, "type": "player", "damage": 50})

    def enemy_fire_laser(self, enemy):
        coords = self.canvas.coords(enemy["id"])
        if not coords:
            return
        etype = enemy["type"]
        if etype == "basic":
            lid = self.canvas.create_line(
                coords[0], coords[1] + 25,
                coords[0], coords[1] + 45,
                fill=CLR_RED, width=3
            )
            self.lasers.append({"id": lid, "type": "enemy", "damage": 20})
        elif etype == "boss":
            self.play_sound(SOUND_BOSS_LASER)
            for ox in (-20, 20):
                lid = self.canvas.create_line(
                    coords[0] + ox, coords[1] + 50,
                    coords[0] + ox, coords[1] + 70,
                    fill="#FF8800", width=4
                )
                self.lasers.append({"id": lid, "type": "enemy", "damage": 25})
        elif etype == "mega_boss":
            self.play_sound(SOUND_BOSS_LASER)
            for ox in (-40, 0, 40):
                lid = self.canvas.create_line(
                    coords[0] + ox, coords[1] + 70,
                    coords[0] + ox, coords[1] + 95,
                    fill=CLR_ACCENT2, width=5
                )
                self.lasers.append({"id": lid, "type": "enemy", "damage": 25})

    def use_powerup(self, index):
        if index < len(self.inventory):
            power = self.inventory.pop(index)
            self.update_ui()

    # ──────────────────────────────────────

    def game_loop(self):
        if not self.is_running:
            return

        # 0. Smooth movement
        if self.active_keys.get("Left"):
            self.move_player(-12)
        if self.active_keys.get("Right"):
            self.move_player(12)

        # 1. Spawn basic enemies
        if self.enemies_to_spawn > 0 and random.random() < 0.02:
            x = random.randint(50, 750)
            eid = self.canvas.create_image(x, -20, image=self.images["enemy"])
            self.enemies.append({"id": eid, "health": 50, "type": "basic"})
            self.enemies_to_spawn -= 1

        # 2. Spawn boss / mega boss
        if self.current_level >= 4 and self.enemies_to_spawn == 5 and not self.boss_spawned:
            bid = self.canvas.create_image(400, 100, image=self.images["boss"])
            self.enemies.append({"id": bid, "health": 10, "type": "boss"})
            self.boss_spawned = True

        if self.current_level == 5 and self.enemies_to_spawn == 0 and not self.mega_boss_spawned:
            mid = self.canvas.create_image(400, 150, image=self.images["mega_boss"])
            self.enemies.append({"id": mid, "health": self.mega_boss_health, "type": "mega_boss"})
            self.mega_boss_spawned = True

        # 3. Move & fire enemies
        for e in list(self.enemies):
            if e["type"] in ("boss", "mega_boss"):
                move_x = math.sin(time.time() * 2) * 4
                self.canvas.move(e["id"], move_x, 0)
            else:
                self.canvas.move(e["id"], 0, self.enemy_speed)

            if self.can_enemies_fire:
                fire_chance = 0.005 if e["type"] == "basic" else 0.02
                if random.random() < fire_chance:
                    self.enemy_fire_laser(e)

            coords = self.canvas.coords(e["id"])
            if coords and coords[1] > 650:
                self.canvas.delete(e["id"])
                self.enemies.remove(e)
                if e["type"] == "basic":
                    self.player_health -= 20
                    self.update_ui()
                    if self.player_health <= 0:
                        self.trigger_game_over()
                        return

        # 4. Move lasers & collisions
        for l in list(self.lasers):
            if l["type"] == "player":
                self.canvas.move(l["id"], 0, -12)
                lbb = self.canvas.bbox(l["id"])
                for e in list(self.enemies):
                    ebb = self.canvas.bbox(e["id"])
                    if self.check_collision(lbb, ebb):
                        e["health"] -= l["damage"]
                        self.canvas.delete(l["id"])
                        if l in self.lasers:
                            self.lasers.remove(l)
                        if e["health"] <= 0:
                            self.play_sound(SOUND_SHIP_BLAST)
                            self.canvas.delete(e["id"])
                            if e in self.enemies:
                                self.enemies.remove(e)
                            self.score += 100
                            self.update_ui()
                        break
            else:
                self.canvas.move(l["id"], 0, 9)
                lbb = self.canvas.bbox(l["id"])
                pbb = self.canvas.bbox(self.player_id)
                if self.check_collision(lbb, pbb):
                    self.player_health -= l["damage"]
                    self.update_ui()
                    self.canvas.delete(l["id"])
                    if l in self.lasers:
                        self.lasers.remove(l)
                    if self.player_health <= 0:
                        self.trigger_game_over()
                        return

            coords = self.canvas.coords(l["id"])
            if coords and (coords[1] < 0 or coords[1] > 620):
                self.canvas.delete(l["id"])
                if l in self.lasers:
                    self.lasers.remove(l)

        # 5. Level clear
        if self.enemies_to_spawn == 0 and len(self.enemies) == 0:
            self.is_running = False
            if self.current_level == 5:
                self.show_victory_screen()
            else:
                self.show_level_clear()
            return

        self.after(16, self.game_loop)

    # ──────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────

    def check_collision(self, b1, b2):
        if not b1 or not b2:
            return False
        return b1[0] < b2[2] and b1[2] > b2[0] and b1[1] < b2[3] and b1[3] > b2[1]

    def update_ui(self):
        hp = max(0, self.player_health)
        self.hp_bar_var.set(hp)
        self.lbl_health.config(text=f"{hp} / 100")
        if hp <= 25:
            self.lbl_health.config(fg=CLR_RED)
            self.hp_bar.configure(bootstyle="danger-striped")
        elif hp <= 50:
            self.lbl_health.config(fg=CLR_GOLD)
            self.hp_bar.configure(bootstyle="warning-striped")
        else:
            self.lbl_health.config(fg=CLR_GREEN)
            self.hp_bar.configure(bootstyle="success-striped")

        self.lbl_score.config(text=f"SCORE  {self.score:06d}")
        inv_text = "  ".join(f"[{i+1}]{p}" for i, p in enumerate(self.inventory)) or "[EMPTY]"
        self.lbl_inv.config(text=inv_text)

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()


# ==========================================

if __name__ == "__main__":
    app = SpaceShooter()
    app.mainloop()