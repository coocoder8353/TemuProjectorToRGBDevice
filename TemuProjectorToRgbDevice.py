"""
TEMU PROJECTOR PIXEL ART STUDIO  ·  v2  (RGB Presets Edition)
==============================================================
Requirements: Python 3.8+, tkinter (built-in), Pillow
Install Pillow:  pip install Pillow
"""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import json, math, time, colorsys, random
from PIL import Image, ImageTk, ImageDraw

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

CANVAS_W  = 32
CANVAS_H  = 20
CELL_SIZE = 22
PROJ_SCALE = 16

BG_DARK   = "#0d0d0d"
BG_MID    = "#1a1a1a"
BG_PANEL  = "#111111"
BG_TAB    = "#0a0a0a"
ACCENT    = "#ff4136"
ACCENT2   = "#ff851b"
TEXT_MAIN = "#f0f0f0"
TEXT_DIM  = "#555555"
TEXT_MED  = "#999999"

PALETTE = [
    "#000000","#ffffff","#ff4136","#ff851b",
    "#ffdc00","#2ecc40","#00bcd4","#0074d9",
    "#b10dc9","#f012be","#01ff70","#7fdbff",
    "#ff69b4","#ff6b35","#c8ff00","#d4a017",
    "#3d9970","#001f3f","#85144b","#aaaaaa",
    "#555555","#222222","#e8d5b7","#6c4f3d",
]
TOOLS = ["draw","erase","fill","eyedrop","line","rect"]

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def hsv_hex(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def lerp_color(c1, c2, t):
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

# ─── RGB PRESET GENERATORS ────────────────────────────────────────────────────
# Each generator(t) returns a 2-D list [row][col] = hex color string
# t = time in seconds (float), used for animation

def gen_rainbow_wave(t):
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            h = (col/CANVAS_W + row/CANVAS_H*0.3 + t*0.4) % 1.0
            r.append(hsv_hex(h, 1.0, 1.0))
        grid.append(r)
    return grid

def gen_plasma(t):
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            cx, cy = col/CANVAS_W*6, row/CANVAS_H*4
            v  = math.sin(cx + t*2)
            v += math.sin(cy + t*1.5)
            v += math.sin((cx+cy)/2 + t)
            v += math.sin(math.sqrt(cx*cx + cy*cy + 1) - t*2)
            h = (v * 0.25) % 1.0
            r.append(hsv_hex(h, 1.0, 1.0))
        grid.append(r)
    return grid

def gen_fire(t):
    # Scrolling fire palette
    fire_cols = ["#000000","#1a0000","#330000","#660000","#990000",
                 "#cc2200","#ff4400","#ff7700","#ffaa00","#ffdd00","#ffff88"]
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            # intensity rises from bottom, flickers
            y_frac = 1.0 - row/CANVAS_H   # 0 at top, 1 at bottom
            noise  = math.sin(col*1.7 + t*8 + row*0.5) * 0.15
            noise += math.sin(col*3.1 - t*12) * 0.1
            intensity = max(0.0, min(1.0, y_frac**1.4 + noise))
            idx = int(intensity * (len(fire_cols)-1))
            r.append(fire_cols[idx])
        grid.append(r)
    return grid

def gen_matrix(t, _state={"drops":{}}):
    drops = _state["drops"]
    # init drops
    if not drops:
        for col in range(CANVAS_W):
            drops[col] = random.randint(0, CANVAS_H)
    # advance
    tick = int(t * 8)
    if not hasattr(gen_matrix, "_last_tick"):
        gen_matrix._last_tick = tick
    if tick != gen_matrix._last_tick:
        gen_matrix._last_tick = tick
        for col in drops:
            if random.random() < 0.15:
                drops[col] = 0
            else:
                drops[col] = (drops[col] + 1) % (CANVAS_H + 4)
    # build brightness map
    bright = [[0.0]*CANVAS_W for _ in range(CANVAS_H)]
    for col, head in drops.items():
        for tail in range(8):
            row = head - tail
            if 0 <= row < CANVAS_H:
                bright[row][col] = max(bright[row][col], 1.0 - tail/8)
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            b = bright[row][col]
            if b > 0.85:
                r.append("#ccffcc")   # bright head
            elif b > 0:
                v = int(b * 200)
                r.append("#{:02x}{:02x}{:02x}".format(0, v, 0))
            else:
                r.append("#000000")
        grid.append(r)
    return grid

def gen_starfield(t, _state={"stars":[]}):
    stars = _state["stars"]
    if not stars:
        for _ in range(60):
            stars.append([
                random.uniform(0, CANVAS_W),
                random.uniform(0, CANVAS_H),
                random.uniform(0.3, 1.0),  # speed
                random.uniform(0.4, 1.0),  # brightness
            ])
    grid = [["#000000"]*CANVAS_W for _ in range(CANVAS_H)]
    for s in stars:
        s[0] = (s[0] - s[2]*0.12) % CANVAS_W
        col = int(s[0]) % CANVAS_W
        row = int(s[1]) % CANVAS_H
        v = int(s[3] * 255)
        grid[row][col] = "#{:02x}{:02x}{:02x}".format(v,v,v)
    return grid

def gen_pulse(t):
    cx, cy = CANVAS_W/2, CANVAS_H/2
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            dist = math.sqrt((col-cx)**2 + (row-cy)**2)
            wave = math.sin(dist*0.8 - t*5) * 0.5 + 0.5
            h = (t*0.15 + dist*0.03) % 1.0
            v = wave ** 2
            r.append(hsv_hex(h, 1.0, v))
        grid.append(r)
    return grid

def gen_lightning(t, _state={"bolts":[], "next_bolt":0}):
    s = _state
    if t > s["next_bolt"]:
        # generate a new zigzag bolt
        col = random.randint(2, CANVAS_W-3)
        bolt = []
        for row in range(CANVAS_H):
            col = max(0, min(CANVAS_W-1, col + random.randint(-2,2)))
            bolt.append((col, row))
        s["bolts"] = bolt
        s["next_bolt"] = t + random.uniform(0.3, 1.2)

    grid = [["#000000"]*CANVAS_W for _ in range(CANVAS_H)]
    age = s["next_bolt"] - t
    bright = min(1.0, age * 4)
    for col, row in s["bolts"]:
        v = int(bright * 255)
        grid[row][col] = "#{:02x}{:02x}{:02x}".format(v, v, int(v*0.6))
        # glow
        for dc in [-1, 1]:
            nc = col + dc
            if 0 <= nc < CANVAS_W:
                gv = int(bright * 100)
                grid[row][nc] = "#{:02x}{:02x}{:02x}".format(gv//2, gv//2, 0)
    return grid

def gen_checkerboard(t):
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            phase = int(t * 2) % 2
            cell  = (col + row + phase) % 2
            h1 = (t * 0.1) % 1.0
            h2 = (h1 + 0.5) % 1.0
            r.append(hsv_hex(h1, 1.0, 1.0) if cell else hsv_hex(h2, 1.0, 1.0))
        grid.append(r)
    return grid

def gen_lava(t):
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            cx2, cy2 = col/CANVAS_W*4, row/CANVAS_H*3
            v  = math.sin(cx2 * 1.5 + t)
            v += math.sin(cy2 * 2 - t * 0.7)
            v += math.sin((cx2+cy2) + t * 1.2)
            norm = (v + 3) / 6
            # lava: black -> deep red -> orange -> yellow-white
            if norm < 0.4:
                frac = norm / 0.4
                color = lerp_color("#000000","#cc2200", frac)
            elif norm < 0.7:
                frac = (norm-0.4)/0.3
                color = lerp_color("#cc2200","#ff8800", frac)
            else:
                frac = (norm-0.7)/0.3
                color = lerp_color("#ff8800","#ffff99", frac)
            r.append(color)
        grid.append(r)
    return grid

def gen_vortex(t):
    cx, cy = CANVAS_W/2, CANVAS_H/2
    grid = []
    for row in range(CANVAS_H):
        r = []
        for col in range(CANVAS_W):
            dx, dy = col-cx, row-cy
            angle  = math.atan2(dy, dx)
            dist   = math.sqrt(dx*dx + dy*dy)
            h = (angle/(2*math.pi) + dist*0.08 - t*0.5) % 1.0
            v = min(1.0, dist / (CANVAS_W*0.55))
            r.append(hsv_hex(h, 1.0, v))
        grid.append(r)
    return grid

def gen_solid_rgb(t):
    h = (t * 0.2) % 1.0
    color = hsv_hex(h, 1.0, 1.0)
    return [[color]*CANVAS_W for _ in range(CANVAS_H)]

def gen_strobe(t):
    on = int(t * 6) % 2 == 0
    color = "#ffffff" if on else "#000000"
    return [[color]*CANVAS_W for _ in range(CANVAS_H)]

# Registry: (label, generator_function, description)
RGB_PRESETS = [
    ("🌈 Rainbow Wave",   gen_rainbow_wave, "Scrolling hue gradient across canvas"),
    ("🔮 Plasma",         gen_plasma,       "Psychedelic interference pattern"),
    ("🔥 Fire",           gen_fire,         "Flickering flame from the bottom"),
    ("💊 Matrix Rain",    gen_matrix,       "Green code drops — classic hacker"),
    ("⭐ Starfield",      gen_starfield,    "Flying through hyperspace"),
    ("💥 Pulse",          gen_pulse,        "Expanding color rings from center"),
    ("⚡ Lightning",      gen_lightning,    "Random lightning bolt strikes"),
    ("♟  Checker",        gen_checkerboard,"Color-cycling checkerboard"),
    ("🌋 Lava",           gen_lava,         "Bubbling molten rock"),
    ("🌀 Vortex",         gen_vortex,       "Spinning color spiral"),
    ("🎨 Solid RGB",      gen_solid_rgb,    "Full-screen slow color cycle"),
    ("⚪ Strobe",         gen_strobe,       "Warning: flashing white/black"),
]

# ─── PIXEL CANVAS ─────────────────────────────────────────────────────────────

class PixelCanvas(tk.Canvas):
    def __init__(self, master, app, **kw):
        w = CANVAS_W * CELL_SIZE
        h = CANVAS_H * CELL_SIZE
        super().__init__(master, width=w, height=h,
                         bg="#181818", cursor="crosshair",
                         highlightthickness=1, highlightbackground="#333",
                         **kw)
        self.app = app
        self.grid_cells = {}
        self.colors = {}
        self._last_cell = None
        self._line_start = None
        self._rect_start = None
        self._overlay_ids = []

        self._build_grid()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<ButtonPress-3>",   self._on_rclick)

    def _build_grid(self):
        for row in range(CANVAS_H):
            for col in range(CANVAS_W):
                x1,y1 = col*CELL_SIZE, row*CELL_SIZE
                rid = self.create_rectangle(x1,y1,x1+CELL_SIZE,y1+CELL_SIZE,
                                             fill="#181818",outline="#222",width=0.5)
                self.grid_cells[(col,row)] = rid

    def _cell_at(self,x,y):
        col,row = int(x//CELL_SIZE), int(y//CELL_SIZE)
        if 0<=col<CANVAS_W and 0<=row<CANVAS_H:
            return col,row
        return None

    def set_pixel(self,col,row,color):
        if color is None:
            color="#181818"; self.colors.pop((col,row),None)
        else:
            self.colors[(col,row)] = color
        self.itemconfig(self.grid_cells[(col,row)], fill=color)

    def get_pixel(self,col,row):
        return self.colors.get((col,row))

    def bulk_set(self, grid):
        """Set all pixels from a 2-D list without redrawing grid lines."""
        for row in range(CANVAS_H):
            for col in range(CANVAS_W):
                color = grid[row][col]
                self.colors[(col,row)] = color
                self.itemconfig(self.grid_cells[(col,row)], fill=color)

    def _apply_tool(self,cell):
        tool=self.app.tool.get(); color=self.app.fg_color; col,row=cell
        if tool=="draw":   self.set_pixel(col,row,color)
        elif tool=="erase":self.set_pixel(col,row,None)
        elif tool=="fill": self._flood_fill(col,row,color)
        elif tool=="eyedrop":
            picked=self.get_pixel(col,row) or "#181818"; self.app.set_fg(picked)

    def _flood_fill(self,col,row,new_color):
        old=self.get_pixel(col,row)
        if old==new_color: return
        stack=[(col,row)]; visited=set()
        while stack:
            c,r=stack.pop()
            if (c,r) in visited: continue
            if not(0<=c<CANVAS_W and 0<=r<CANVAS_H): continue
            if self.get_pixel(c,r)!=old: continue
            visited.add((c,r)); self.set_pixel(c,r,new_color)
            for dc,dr in[(1,0),(-1,0),(0,1),(0,-1)]: stack.append((c+dc,r+dr))

    def _clear_overlay(self):
        for oid in self._overlay_ids: self.delete(oid)
        self._overlay_ids.clear()

    def _draw_overlay(self,col,row):
        if 0<=col<CANVAS_W and 0<=row<CANVAS_H:
            x1,y1=col*CELL_SIZE,row*CELL_SIZE
            oid=self.create_rectangle(x1,y1,x1+CELL_SIZE,y1+CELL_SIZE,
                                       fill=self.app.fg_color,outline="",stipple="gray50")
            self._overlay_ids.append(oid)

    def _preview_line(self,c0,r0,c1,r1):
        self._clear_overlay()
        for col,row in self._bresenham(c0,r0,c1,r1):
            self._draw_overlay(col,row)

    def _preview_rect(self,c0,r0,c1,r1):
        self._clear_overlay()
        for col in range(min(c0,c1),max(c0,c1)+1):
            for row in[min(r0,r1),max(r0,r1)]: self._draw_overlay(col,row)
        for row in range(min(r0,r1),max(r0,r1)+1):
            for col in[min(c0,c1),max(c0,c1)]: self._draw_overlay(col,row)

    def _commit_line(self,c0,r0,c1,r1):
        self._clear_overlay()
        for col,row in self._bresenham(c0,r0,c1,r1): self.set_pixel(col,row,self.app.fg_color)

    def _commit_rect(self,c0,r0,c1,r1):
        self._clear_overlay()
        for col in range(min(c0,c1),max(c0,c1)+1):
            for row in[min(r0,r1),max(r0,r1)]: self.set_pixel(col,row,self.app.fg_color)
        for row in range(min(r0,r1),max(r0,r1)+1):
            for col in[min(c0,c1),max(c0,c1)]: self.set_pixel(col,row,self.app.fg_color)

    @staticmethod
    def _bresenham(c0,r0,c1,r1):
        pts=[]; dc,dr=abs(c1-c0),-abs(r1-r0)
        sc=1 if c1>c0 else -1; sr=1 if r1>r0 else -1; err=dc+dr
        while True:
            pts.append((c0,r0))
            if c0==c1 and r0==r1: break
            e2=2*err
            if e2>=dr: err+=dr; c0+=sc
            if e2<=dc: err+=dc; r0+=sr
        return pts

    def _on_press(self,e):
        cell=self._cell_at(e.x,e.y)
        if not cell: return
        tool=self.app.tool.get()
        if tool in("draw","erase","fill","eyedrop"):
            self._apply_tool(cell); self._last_cell=cell
        elif tool=="line": self._line_start=cell
        elif tool=="rect": self._rect_start=cell

    def _on_drag(self,e):
        cell=self._cell_at(e.x,e.y)
        if not cell: return
        tool=self.app.tool.get()
        if tool in("draw","erase") and cell!=self._last_cell:
            self._apply_tool(cell); self._last_cell=cell
        elif tool=="line" and self._line_start: self._preview_line(*self._line_start,*cell)
        elif tool=="rect" and self._rect_start: self._preview_rect(*self._rect_start,*cell)

    def _on_release(self,e):
        cell=self._cell_at(e.x,e.y)
        tool=self.app.tool.get()
        if tool=="line" and self._line_start and cell:
            self._commit_line(*self._line_start,*cell); self._line_start=None
        elif tool=="rect" and self._rect_start and cell:
            self._commit_rect(*self._rect_start,*cell); self._rect_start=None

    def _on_rclick(self,e):
        cell=self._cell_at(e.x,e.y)
        if cell: self.app.set_fg(self.get_pixel(*cell) or "#181818")

    def to_pil(self,scale=1):
        img=Image.new("RGB",(CANVAS_W*scale,CANVAS_H*scale),"#000000")
        draw=ImageDraw.Draw(img)
        for(col,row),color in self.colors.items():
            x0,y0=col*scale,row*scale
            draw.rectangle([x0,y0,x0+scale-1,y0+scale-1],fill=color)
        return img

    def clear_all(self):
        for(col,row) in list(self.colors.keys()): self.set_pixel(col,row,None)

    def load_colors(self,data):
        self.clear_all()
        for key,color in data.items():
            col,row=map(int,key.split(","))
            self.set_pixel(col,row,color)

    def save_dict(self):
        return{f"{c},{r}":col for(c,r),col in self.colors.items()}


# ─── MONITOR DETECTION ────────────────────────────────────────────────────────

def get_monitors():
    """
    Return a list of (x, y, w, h) for every monitor.
    Tries screeninfo, then falls back to a tk-based single-monitor entry.
    """
    try:
        from screeninfo import get_monitors as _gm
        return [(m.x, m.y, m.width, m.height) for m in _gm()]
    except Exception:
        pass
    # fallback: just report whatever tk sees as "the screen"
    root = tk._default_root or tk.Tk()
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    return [(0, 0, w, h)]


def pick_monitor(parent):
    """
    Pop a dialog listing all detected monitors so the user can choose one.
    Returns (x, y, w, h) or None if cancelled.
    """
    monitors = get_monitors()

    if len(monitors) == 1:
        # Only one screen — just warn them and use it
        mx, my, mw, mh = monitors[0]
        messagebox.showinfo(
            "One screen detected",
            f"Only one display found ({mw}×{mh}).\n\n"
            "Make sure your projector/TV is plugged in and set to\n"
            "EXTEND (not mirror/duplicate) in your display settings,\n"
            "then try again.\n\n"
            "Projecting on this screen anyway…",
            parent=parent
        )
        return monitors[0]

    # Multiple screens — let user pick
    dialog = tk.Toplevel(parent)
    dialog.title("Choose display")
    dialog.configure(bg=BG_DARK)
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog,
             text="Which screen is your projector?",
             bg=BG_DARK, fg=TEXT_MAIN,
             font=("Courier", 12, "bold")).pack(padx=20, pady=(16, 4))
    tk.Label(dialog,
             text="(Tip: set displays to EXTEND mode, not mirror)",
             bg=BG_DARK, fg=TEXT_DIM,
             font=("Courier", 9)).pack(padx=20, pady=(0, 12))

    chosen = [None]

    for i, (mx, my, mw, mh) in enumerate(monitors):
        label = f"Screen {i+1}:  {mw}×{mh}  at  ({mx}, {my})"
        if i == 0:
            label += "  ← (likely your main monitor)"
        else:
            label += "  ← projector / TV?"
        btn = tk.Button(
            dialog, text=label,
            bg=BG_MID, fg=TEXT_MAIN,
            font=("Courier", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=12, pady=8,
            command=lambda m=(mx,my,mw,mh): (chosen.__setitem__(0, m), dialog.destroy())
        )
        btn.pack(fill="x", padx=16, pady=4)

    tk.Button(dialog, text="Cancel", bg="#1a0000", fg=TEXT_DIM,
              font=("Courier", 9), relief="flat", cursor="hand2",
              command=dialog.destroy).pack(pady=(4, 14))

    parent.wait_window(dialog)
    return chosen[0]


# ─── ANIMATED PROJECTOR PREVIEW ───────────────────────────────────────────────

class ProjectorWindow(tk.Toplevel):
    """Fullscreen projector output on a chosen monitor."""
    def __init__(self, master, pixel_canvas, generator=None, monitor=None):
        super().__init__(master)
        self.pixel_canvas = pixel_canvas
        self.generator = generator
        self.title("PROJECTOR")
        self.configure(bg="black")

        if monitor is None:
            monitor = (0, 0,
                       master.winfo_screenwidth(),
                       master.winfo_screenheight())
        mx, my, mw, mh = monitor
        self._mw = mw
        self._mh = mh

        # Position on the correct monitor BEFORE going fullscreen
        self.geometry(f"{mw}x{mh}+{mx}+{my}")
        self.update_idletasks()

        # Use overrideredirect for a proper borderless black window on any OS
        self.overrideredirect(True)
        self.geometry(f"{mw}x{mh}+{mx}+{my}")  # set again after override

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0,
                                width=mw, height=mh)
        self.canvas.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda e: self._stop())
        self.bind("<Key>",    lambda e: self._stop())
        self.focus_force()

        self._running = True
        self._start_t = time.time()
        self._render()

    def _stop(self):
        self._running = False
        self.destroy()

    def _render(self):
        if not self._running:
            return
        mw, mh = self._mw, self._mh
        sc = min(mw // CANVAS_W, mh // CANVAS_H)
        tw, th = CANVAS_W * sc, CANVAS_H * sc
        ox, oy = (mw - tw) // 2, (mh - th) // 2

        t = (time.time() - self._start_t)

        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, mw, mh, fill="black", outline="")

        if self.generator:
            grid = self.generator(t)
            for row in range(CANVAS_H):
                for col in range(CANVAS_W):
                    color = grid[row][col]
                    if color != "#000000":
                        x0 = ox + col * sc
                        y0 = oy + row * sc
                        self.canvas.create_rectangle(
                            x0, y0, x0+sc, y0+sc, fill=color, outline="")
        else:
            for (col, row), color in self.pixel_canvas.colors.items():
                x0 = ox + col * sc
                y0 = oy + row * sc
                self.canvas.create_rectangle(
                    x0, y0, x0+sc, y0+sc, fill=color, outline="")

        self.canvas.create_text(mw // 2, mh - 18,
                                text="ESC or any key to exit",
                                fill="#1a1a1a", font=("Courier", 10))

        delay = 33 if self.generator else 200
        self.after(delay, self._render)


# ─── MAIN APP ─────────────────────────────────────────────────────────────────

class TemuPixelStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TEMU PIXEL PROJECTOR STUDIO  v2")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.fg_color = "#ff4136"
        self.tool = tk.StringVar(value="draw")
        self.preview_img = None
        self._active_tab = tk.StringVar(value="draw")
        self._anim_job = None
        self._anim_gen = None
        self._anim_t0  = 0
        self._proj_win = None
        self._build_ui()
        self._update_preview()

    # ── Top-level layout ──────────────────────────────────────────────────────

    def _build_ui(self):
        # Title
        tb = tk.Frame(self, bg=BG_DARK, pady=6)
        tb.pack(fill="x", padx=12)
        tk.Label(tb, text="▓▒░ TEMU PIXEL PROJECTOR STUDIO ░▒▓",
                 bg=BG_DARK, fg=ACCENT, font=("Courier",13,"bold")).pack(side="left")
        tk.Label(tb, text=f"{CANVAS_W}×{CANVAS_H}",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Courier",10)).pack(side="right")
        tk.Frame(self, bg="#2a2a2a", height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(padx=10, pady=8)

        # Left panel with tabs
        left = tk.Frame(body, bg=BG_TAB, highlightthickness=1,
                        highlightbackground="#2a2a2a")
        left.pack(side="left", padx=(0,10), fill="y")
        self._build_tab_bar(left)
        self._build_draw_panel(left)
        self._build_rgb_panel(left)
        self._switch_tab("draw")

        # Canvas
        mid = tk.Frame(body, bg=BG_DARK)
        mid.pack(side="left")
        self.pixel_canvas = PixelCanvas(mid, self)
        self.pixel_canvas.pack()

        # Right panel
        right = tk.Frame(body, bg=BG_PANEL, highlightthickness=1,
                         highlightbackground="#2a2a2a")
        right.pack(side="left", padx=(10,0), fill="y")
        self._build_preview_panel(right)
        self._build_actions(right)

    def _build_tab_bar(self, parent):
        bar = tk.Frame(parent, bg="#0a0a0a")
        bar.pack(fill="x")
        self._tab_btns = {}
        for key, label in [("draw","✏  DRAW"), ("rgb","⚡ RGB PRESETS")]:
            b = tk.Button(bar, text=label,
                          bg="#1a0000" if key=="draw" else BG_TAB,
                          fg=ACCENT if key=="draw" else TEXT_DIM,
                          font=("Courier",10,"bold"),
                          relief="flat", cursor="hand2",
                          padx=10, pady=6,
                          command=lambda k=key: self._switch_tab(k))
            b.pack(side="left", fill="x", expand=True)
            self._tab_btns[key] = b

    def _switch_tab(self, key):
        self._active_tab.set(key)
        for k, b in self._tab_btns.items():
            if k == key:
                b.configure(bg="#1a0000", fg=ACCENT)
            else:
                b.configure(bg=BG_TAB, fg=TEXT_DIM)
        if key == "draw":
            self.draw_panel.pack(fill="x")
            self.rgb_panel.pack_forget()
        else:
            self.draw_panel.pack_forget()
            self.rgb_panel.pack(fill="both", expand=True)

    # ── Draw panel ────────────────────────────────────────────────────────────

    def _build_draw_panel(self, parent):
        self.draw_panel = tk.Frame(parent, bg=BG_PANEL)
        p = self.draw_panel
        self._lbl(p, "TOOLS")
        icons = {"draw":"✏","erase":"◻","fill":"◈","eyedrop":"◉","line":"╱","rect":"▭"}
        grid = tk.Frame(p, bg=BG_PANEL); grid.pack(padx=8, pady=4)
        for i, tool in enumerate(TOOLS):
            tk.Radiobutton(grid, text=f"{icons[tool]} {tool.upper()}",
                           variable=self.tool, value=tool,
                           bg=BG_PANEL, fg=TEXT_MAIN, selectcolor="#330000",
                           activebackground=BG_MID, activeforeground=ACCENT,
                           font=("Courier",10,"bold"), relief="flat",
                           indicatoron=False, width=10, pady=4, cursor="hand2"
                           ).grid(row=i//2, column=i%2, padx=3, pady=2)
        for key,val in{"d":"draw","e":"erase","f":"fill","i":"eyedrop","l":"line","r":"rect"}.items():
            self.bind(key, lambda e,v=val: self.tool.set(v))

        self._lbl(p, "ACTIVE COLOR")
        row = tk.Frame(p, bg=BG_PANEL); row.pack(padx=8, pady=4, fill="x")
        self.fg_btn = tk.Button(row, bg=self.fg_color, width=4, height=2,
                                 relief="flat", cursor="hand2",
                                 command=self._pick_custom_color,
                                 highlightthickness=2, highlightbackground="#555")
        self.fg_btn.pack(side="left", padx=(0,6))
        info = tk.Frame(row, bg=BG_PANEL); info.pack(side="left")
        self.color_hex_lbl = tk.Label(info, text=self.fg_color, bg=BG_PANEL,
                                       fg=TEXT_MAIN, font=("Courier",11,"bold"))
        self.color_hex_lbl.pack(anchor="w")
        tk.Label(info, text="click to customize", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Courier",8)).pack(anchor="w")

        self._lbl(p, "PALETTE")
        pal = tk.Frame(p, bg=BG_PANEL); pal.pack(padx=8, pady=4)
        for i, color in enumerate(PALETTE):
            tk.Button(pal, bg=color, width=2, height=1, relief="flat",
                      cursor="hand2",
                      command=lambda c=color: self.set_fg(c)
                      ).grid(row=i//6, column=i%6, padx=1, pady=1)

        self._lbl(p, "CANVAS")
        tk.Button(p, text="🗑  CLEAR ALL", command=self._clear_confirm,
                  bg="#1a0000", fg=TEXT_MAIN, font=("Courier",10,"bold"),
                  relief="flat", cursor="hand2", width=18, pady=5
                  ).pack(padx=8, pady=4)

    # ── RGB presets panel ─────────────────────────────────────────────────────

    def _build_rgb_panel(self, parent):
        self.rgb_panel = tk.Frame(parent, bg=BG_PANEL)
        p = self.rgb_panel

        self._lbl(p, "ANIMATED RGB PRESETS")
        tk.Label(p, text="One click → fills canvas + projects live",
                 bg=BG_PANEL, fg=TEXT_MED, font=("Courier",8)).pack(padx=8, anchor="w")

        scroll_frame = tk.Frame(p, bg=BG_PANEL)
        scroll_frame.pack(fill="both", expand=True, padx=4, pady=6)

        self._preset_btns = []
        self._selected_preset = tk.IntVar(value=-1)

        for idx, (label, gen_fn, desc) in enumerate(RGB_PRESETS):
            row_f = tk.Frame(scroll_frame, bg=BG_MID,
                             highlightthickness=1, highlightbackground="#222")
            row_f.pack(fill="x", pady=2, padx=4)

            top = tk.Frame(row_f, bg=BG_MID)
            top.pack(fill="x", padx=6, pady=(4,1))

            name_lbl = tk.Label(top, text=label, bg=BG_MID, fg=TEXT_MAIN,
                                 font=("Courier",10,"bold"), anchor="w")
            name_lbl.pack(side="left")

            btns = tk.Frame(row_f, bg=BG_MID)
            btns.pack(fill="x", padx=6, pady=(2,4))

            tk.Label(btns, text=desc, bg=BG_MID, fg=TEXT_DIM,
                     font=("Courier",8), anchor="w").pack(side="left")

            proj_btn = tk.Button(btns, text="▶ PROJECT",
                                  bg="#0a1a00", fg="#44ff44",
                                  font=("Courier",9,"bold"),
                                  relief="flat", cursor="hand2", padx=6,
                                  command=lambda g=gen_fn, l=label: self._project_preset(g, l))
            proj_btn.pack(side="right", padx=(4,0))

            fill_btn = tk.Button(btns, text="↓ FILL",
                                  bg="#001a1a", fg="#44ddff",
                                  font=("Courier",9,"bold"),
                                  relief="flat", cursor="hand2", padx=6,
                                  command=lambda g=gen_fn: self._fill_preset(g))
            fill_btn.pack(side="right")

        # Speed control
        self._lbl(p, "ANIMATION SPEED")
        spd_row = tk.Frame(p, bg=BG_PANEL); spd_row.pack(padx=8, fill="x")
        self.speed_var = tk.DoubleVar(value=1.0)
        tk.Scale(spd_row, from_=0.1, to=4.0, resolution=0.1,
                 orient="horizontal", variable=self.speed_var,
                 bg=BG_PANEL, fg=TEXT_MAIN, troughcolor=BG_MID,
                 highlightthickness=0, showvalue=True,
                 font=("Courier",8), label="").pack(fill="x")

        # Stop animation
        tk.Button(p, text="⏹  STOP ANIMATION",
                  command=self._stop_anim,
                  bg="#1a0000", fg=TEXT_MAIN,
                  font=("Courier",10,"bold"), relief="flat",
                  cursor="hand2", width=18, pady=5).pack(padx=8, pady=6)

    # ── Preview + actions panel ────────────────────────────────────────────────

    def _build_preview_panel(self, parent):
        self._lbl(parent, "PREVIEW")
        self.preview_canvas = tk.Canvas(parent,
                                         width=CANVAS_W*5, height=CANVAS_H*5,
                                         bg="black", highlightthickness=1,
                                         highlightbackground="#333")
        self.preview_canvas.pack(padx=8, pady=4)
        self.stat_lbl = tk.Label(parent, text="0 pixels", bg=BG_PANEL,
                                  fg=TEXT_DIM, font=("Courier",9))
        self.stat_lbl.pack(pady=(0,4))
        self._schedule_preview()

    def _build_actions(self, parent):
        self._lbl(parent, "FILE / PROJECT")
        for label, cmd, bg in [
            ("📽  PROJECT CANVAS",  self._open_projector,  "#1a0800"),
            ("💾  SAVE PNG",        self._save_png,        "#001a00"),
            ("💿  SAVE PROJECT",    self._save_project,    "#0d0d1a"),
            ("📂  LOAD PROJECT",    self._load_project,    "#00001a"),
        ]:
            tk.Button(parent, text=label, command=cmd,
                      bg=bg, fg=TEXT_MAIN,
                      activebackground=ACCENT, activeforeground="white",
                      font=("Courier",10,"bold"), relief="flat",
                      cursor="hand2", width=18, pady=5
                      ).pack(padx=8, pady=3)
        tk.Label(parent, text="RGB presets project live\nESC to close projector",
                 bg=BG_PANEL, fg=TEXT_DIM, font=("Courier",8),
                 justify="center").pack(pady=(2,8))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=BG_PANEL if parent.cget("bg")==BG_PANEL else parent.cget("bg"),
                 fg=TEXT_DIM, font=("Courier",9)).pack(anchor="w", padx=8, pady=(8,2))

    def set_fg(self, color):
        self.fg_color = color
        self.fg_btn.configure(bg=color)
        self.color_hex_lbl.configure(text=color.upper())

    def _pick_custom_color(self):
        result = colorchooser.askcolor(color=self.fg_color, title="Pick a color", parent=self)
        if result and result[1]:
            self.set_fg(result[1])

    # ── Animation ─────────────────────────────────────────────────────────────

    def _fill_preset(self, gen_fn):
        """Animate canvas in the editor view (snapshot mode, updates every 50ms)."""
        self._stop_anim()
        self._anim_gen = gen_fn
        self._anim_t0  = time.time()
        self._animate_canvas()

    def _animate_canvas(self):
        if self._anim_gen is None:
            return
        t = (time.time() - self._anim_t0) * self.speed_var.get()
        grid = self._anim_gen(t)
        self.pixel_canvas.bulk_set(grid)
        self._anim_job = self.after(50, self._animate_canvas)

    def _stop_anim(self):
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        self._anim_gen = None

    def _project_preset(self, gen_fn, label):
        if self._proj_win and self._proj_win.winfo_exists():
            self._proj_win.destroy()
        monitor = pick_monitor(self)
        if monitor is None:
            return
        self._proj_win = ProjectorWindow(self, self.pixel_canvas,
                                         generator=gen_fn, monitor=monitor)

    # ── Preview refresh ───────────────────────────────────────────────────────

    def _schedule_preview(self):
        self._update_preview()
        self.after(150, self._schedule_preview)

    def _update_preview(self):
        img = self.pixel_canvas.to_pil(scale=5)
        self.preview_img = ImageTk.PhotoImage(img)
        self.preview_canvas.create_image(0,0,anchor="nw",image=self.preview_img)
        self.stat_lbl.configure(text=f"{len(self.pixel_canvas.colors)} pixels")

    # ── File actions ──────────────────────────────────────────────────────────

    def _clear_confirm(self):
        if messagebox.askyesno("Clear canvas","Wipe everything?",parent=self):
            self._stop_anim()
            self.pixel_canvas.clear_all()

    def _save_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
            filetypes=[("PNG","*.png")], parent=self)
        if path:
            self.pixel_canvas.to_pil(scale=PROJ_SCALE).save(path)
            messagebox.showinfo("Saved", path, parent=self)

    def _save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("Project","*.json")], parent=self)
        if path:
            with open(path,"w") as f:
                json.dump({"version":2,"width":CANVAS_W,"height":CANVAS_H,
                            "pixels":self.pixel_canvas.save_dict()}, f)
            messagebox.showinfo("Saved", path, parent=self)

    def _load_project(self):
        path = filedialog.askopenfilename(
            filetypes=[("Project","*.json"),("All","*.*")], parent=self)
        if path:
            try:
                with open(path) as f: data=json.load(f)
                self.pixel_canvas.load_colors(data.get("pixels",{}))
                self._stop_anim()
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=self)

    def _open_projector(self):
        if not self.pixel_canvas.colors:
            messagebox.showinfo("Empty","Draw something first!",parent=self)
            return
        monitor = pick_monitor(self)
        if monitor is None:
            return
        self._proj_win = ProjectorWindow(self, self.pixel_canvas,
                                         generator=None, monitor=monitor)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess, sys

    # Auto-install Pillow if missing
    try:
        from PIL import Image, ImageTk, ImageDraw
    except ImportError:
        print("Installing Pillow…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageTk, ImageDraw

    # Auto-install screeninfo if missing (needed for multi-monitor support)
    try:
        import screeninfo
    except ImportError:
        print("Installing screeninfo for multi-monitor support…")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "screeninfo"])
        except Exception:
            pass  # graceful fallback if it fails

    app = TemuPixelStudio()
    app.mainloop()
