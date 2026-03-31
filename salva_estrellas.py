#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Starfield Simulation — recreación del salvapantallas de Windows 3.1
Viaje a través de las estrellas con proyección 3D clásica.

Controles:
  T                   → panel de configuración
  ESC / SPACE / clic  → salir
"""

import tkinter as tk
import random
import webbrowser
import os
from PIL import Image, ImageTk

# ── Configuración inicial ──────────────────────────────────────────────────────
DEFAULT_NUM_STARS = 300     # cantidad de estrellas
DEFAULT_SPEED     = 4       # velocidad (1 = lento … 20 = warp máximo)
DEFAULT_FPS       = 60      # frames por segundo
DEPTH             = 800     # profundidad del campo estelar (fija)
FULLSCREEN        = True    # True = pantalla completa | False = ventana 1280×720

# Paleta de colores por profundidad (lejos → cerca)
STAR_COLORS = [
    '#1a1a2e', '#2d2d5e', '#4a4a8a', '#7070bb',
    '#9999cc', '#bbbbdd', '#ddddee', '#eeeef5', '#ffffff',
]
_N_COLORS = len(STAR_COLORS)

# ── Cursor: imagen puntero.JPG, negro → verde neón ────────────────────────────
_CURSOR_NEON  = (57, 255, 20, 255)   # #39FF14 en RGBA
_CURSOR_GLOW  = (10, 58, 3, 180)     # halo oscuro semitransparente
_CURSOR_SCALE = 0.6                  # factor de escala del cursor (1.0 = tamaño original)

def _make_cursor_image(img_path, threshold=100, scale=_CURSOR_SCALE):
    """Carga la imagen, la escala, extrae píxeles oscuros y los pinta verde neón.
    Retorna (PIL Image RGBA, offset_x, offset_y). Sin dependencia de tkinter."""
    src  = Image.open(img_path).convert('L')
    if scale != 1.0:
        nw = max(1, int(src.width  * scale))
        nh = max(1, int(src.height * scale))
        src = src.resize((nw, nh), Image.NEAREST)
    w, h = src.size
    pix  = src.load()

    dark = [(r, c) for r in range(h) for c in range(w) if pix[c, r] < threshold]
    if not dark:
        return None, 0, 0

    r0 = min(r for r, c in dark);  r1 = max(r for r, c in dark)
    c0 = min(c for r, c in dark);  c1 = max(c for r, c in dark)
    cw = (c1 - c0 + 1) + 2
    ch = (r1 - r0 + 1) + 2

    out = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    op  = out.load()

    # Halo primero (1 px de expansión en cada dirección)
    for r, c in dark:
        nr = (r - r0) + 1
        nc = (c - c0) + 1
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                pr, pc = nr + dr, nc + dc
                if 0 <= pr < ch and 0 <= pc < cw and op[pc, pr][3] == 0:
                    op[pc, pr] = _CURSOR_GLOW

    # Píxeles principales encima
    for r, c in dark:
        op[(c - c0) + 1, (r - r0) + 1] = _CURSOR_NEON

    return out, cw // 2, ch // 2

_CURSOR_DIR   = os.path.dirname(os.path.abspath(__file__))
# La PIL Image se pre-procesa aquí; el PhotoImage se crea en __init__ tras tk.Tk()
_CURSOR_IMG, _CURSOR_OX, _CURSOR_OY = _make_cursor_image(
    os.path.join(_CURSOR_DIR, 'puntero.JPG')
)

# ── Firma ─────────────────────────────────────────────────────────────────────
_SIG_URL      = 'https://github.com/SlashUY'
_SIG_RED      = '#FF1111'   # color en reposo
_SIG_PULSE_A  = '#FFFF00'   # amarillo  ─┐ colores del latido
_SIG_PULSE_B  = '#39FF14'   # verde neón ─┘
_SIG_GLOW     = '#5c0505'   # halo rojizo
_SIG_PULSE_MS = 380         # ms por paso del pulso
_SIG_FONT     = ('Courier New', 17, 'bold')

# ── Colores del panel de configuración ────────────────────────────────────────
UI_BG     = '#000010'
UI_BORDER = '#3333aa'
UI_TITLE  = '#6699ff'
UI_LABEL  = '#aabbff'
UI_INPUT  = '#ffffff'
UI_HINT   = '#445588'
UI_ERR    = '#ff4444'
UI_FONT   = ('Courier New', 13, 'bold')
UI_SMALL  = ('Courier New', 10)


# ── Clase Estrella ─────────────────────────────────────────────────────────────
class Star:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, cx, cy, spread_z=True):
        self.x = random.uniform(-cx, cx)
        self.y = random.uniform(-cy, cy)
        self.z = random.uniform(1, DEPTH) if spread_z else float(DEPTH)

    def reset(self, cx, cy):
        self.x = random.uniform(-cx, cx)
        self.y = random.uniform(-cy, cy)
        self.z = float(DEPTH)


# ── Aplicación principal ───────────────────────────────────────────────────────
class Starfield:
    def __init__(self, root: tk.Tk):
        self.root          = root
        self._running      = True
        self._paused       = False
        self._panel        = None
        self._cursor_id    = None  # ID del item cursor en el canvas
        self._cursor_photo = None  # PhotoImage del cursor (creado tras tk.Tk)
        self._sig_id       = None  # ID del texto de la firma
        self._sig_bb       = None  # bounding box de la firma (x1,y1,x2,y2)
        self._sig_hovering = False
        self._sig_pulse_job   = None
        self._sig_pulse_state = False

        self.num_stars = DEFAULT_NUM_STARS
        self.speed     = DEFAULT_SPEED
        self.fps       = DEFAULT_FPS

        self._setup_window()
        self._setup_canvas()
        # Convertir PIL Image a PhotoImage ahora que tk.Tk() ya existe
        if _CURSOR_IMG is not None:
            self._cursor_photo = ImageTk.PhotoImage(_CURSOR_IMG)
        self._init_stars()
        self._draw_signature()
        self._bind_keys()
        self._tick()

    # ── Ventana ────────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title('Starfield')
        self.root.configure(bg='black')
        self.root.resizable(False, False)

        if FULLSCREEN:
            self.root.attributes('-fullscreen', True)
            self.root.update_idletasks()
            self.W = self.root.winfo_screenwidth()
            self.H = self.root.winfo_screenheight()
        else:
            self.W, self.H = 1280, 720
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f'{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}')

        self.CX = self.W // 2
        self.CY = self.H // 2

    def _setup_canvas(self):
        self.canvas = tk.Canvas(
            self.root, width=self.W, height=self.H,
            bg='black', highlightthickness=0, cursor='none'
        )
        self.canvas.pack()
        self.canvas.bind('<Motion>',   self._move_cursor)
        self.canvas.bind('<Leave>',    self._hide_cursor)
        self.canvas.bind('<Button-1>', self._on_canvas_click)

    # ── Cursor alien ───────────────────────────────────────────────────────────
    def _move_cursor(self, event):
        mx, my = event.x, event.y

        if self._cursor_photo is None:
            return

        x = mx - _CURSOR_OX
        y = my - _CURSOR_OY

        if self._cursor_id is None:
            self._cursor_id = self.canvas.create_image(
                x, y, image=self._cursor_photo, anchor='nw'
            )
        else:
            self.canvas.coords(self._cursor_id, x, y)

        self.canvas.tag_raise(self._cursor_id)

        # Detectar hover sobre la firma
        if self._sig_bb:
            x1, y1, x2, y2 = self._sig_bb
            over = x1 <= mx <= x2 and y1 <= my <= y2
            if over and not self._sig_hovering:
                self._sig_hovering = True
                self._sig_pulse_tick()
            elif not over and self._sig_hovering:
                self._sig_hovering = False
                self._sig_stop_pulse()

    def _hide_cursor(self, event=None):
        if self._cursor_id is not None:
            self.canvas.delete(self._cursor_id)
            self._cursor_id = None
        if self._sig_hovering:
            self._sig_hovering = False
            self._sig_stop_pulse()

    # ── Firma ─────────────────────────────────────────────────────────────────
    def _draw_signature(self):
        x, y = 22, self.H - 22

        for dx, dy in ((-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)):
            self.canvas.create_text(
                x + dx, y + dy, text='SSLASH_UY', anchor='sw',
                font=_SIG_FONT, fill=_SIG_GLOW
            )

        self._sig_id = self.canvas.create_text(
            x, y, text='SSLASH_UY', anchor='sw',
            font=_SIG_FONT, fill=_SIG_RED
        )

        self.canvas.update_idletasks()
        self._sig_bb = self.canvas.bbox(self._sig_id)

    # ── Pulso de la firma ──────────────────────────────────────────────────────
    def _sig_pulse_tick(self):
        if not self._sig_hovering or not self._sig_id:
            return
        self._sig_pulse_state = not self._sig_pulse_state
        color = _SIG_PULSE_A if self._sig_pulse_state else _SIG_PULSE_B
        self.canvas.itemconfig(self._sig_id, fill=color)
        self._sig_pulse_job = self.root.after(_SIG_PULSE_MS, self._sig_pulse_tick)

    def _sig_stop_pulse(self):
        if self._sig_pulse_job:
            self.root.after_cancel(self._sig_pulse_job)
            self._sig_pulse_job = None
        self._sig_pulse_state = False
        if self._sig_id:
            self.canvas.itemconfig(self._sig_id, fill=_SIG_RED)

    # ── Estrellas ──────────────────────────────────────────────────────────────
    def _init_stars(self, spread_z=True):
        self._sig_hovering = False
        self._sig_stop_pulse()
        self.canvas.delete('all')
        self._cursor_id = None
        self._sig_id    = None
        self._sig_bb    = None
        self.stars    = [Star(self.CX, self.CY, spread_z) for _ in range(self.num_stars)]
        self.star_ids = [None] * self.num_stars

    # ── Teclas ─────────────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind('<Escape>', self._exit)
        self.root.bind('<space>',  self._exit)
        self.root.bind('<t>', self._open_panel)
        self.root.bind('<T>', self._open_panel)
        self.root.focus_set()

    def _on_canvas_click(self, event):
        if self._panel is not None:
            return
        if self._sig_bb:
            x1, y1, x2, y2 = self._sig_bb
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                webbrowser.open(_SIG_URL)
                return
        self._exit()

    def _exit(self, event=None):
        if self._panel is not None:
            return
        self._running = False
        self.root.destroy()

    # ── Loop principal ─────────────────────────────────────────────────────────
    def _tick(self):
        if not self._running:
            return
        if not self._paused:
            self._update()
        self.root.after(max(1, 1000 // self.fps), self._tick)

    def _update(self):
        cx, cy = self.CX, self.CY
        canvas = self.canvas
        scale  = min(self.W, self.H) * 0.9
        speed  = self.speed

        for i, star in enumerate(self.stars):
            if self.star_ids[i] is not None:
                canvas.delete(self.star_ids[i])
                self.star_ids[i] = None

            star.z -= speed
            sx = int(cx + star.x / star.z * scale)
            sy = int(cy + star.y / star.z * scale)

            if star.z <= 1 or not (0 <= sx < self.W) or not (0 <= sy < self.H):
                star.reset(cx, cy)
                continue

            frac  = 1 - star.z / DEPTH
            size  = max(0.5, frac * 4.5)
            color = STAR_COLORS[min(_N_COLORS - 1, int(frac * _N_COLORS))]
            r     = size / 2
            self.star_ids[i] = canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=color, outline=''
            )

        # Mantener cursor y firma siempre encima de las estrellas
        if self._cursor_id:
            canvas.tag_raise(self._cursor_id)
        if self._sig_id:
            canvas.tag_raise(self._sig_id)

    # ── Panel de configuración ─────────────────────────────────────────────────
    def _open_panel(self, event=None):
        if self._panel is not None:
            return
        self._paused = True
        self._hide_cursor()

        PW, PH = 460, 320
        px = (self.W - PW) // 2
        py = (self.H - PH) // 2

        border = tk.Frame(self.canvas, bg=UI_BORDER)
        border.place(x=px - 2, y=py - 2, width=PW + 4, height=PH + 4)
        panel = tk.Frame(border, bg=UI_BG)
        panel.place(x=2, y=2, width=PW, height=PH)
        self._panel = border

        tk.Label(panel, text='⚙  CONFIGURACIÓN  ⚙',
                 bg=UI_BG, fg=UI_TITLE, font=('Courier New', 15, 'bold')
                 ).grid(row=0, column=0, columnspan=3, pady=(18, 10))
        tk.Frame(panel, bg=UI_BORDER, height=1).grid(
            row=1, column=0, columnspan=3, sticky='ew', padx=20, pady=(0, 14))

        campos = [
            ('Estrellas', 'num_stars', '1 – 1000'),
            ('Velocidad', 'speed',     '1 – 20'),
            ('FPS',       'fps',       '10 – 120'),
        ]
        entries = {}
        for row, (label, attr, hint) in enumerate(campos, start=2):
            tk.Label(panel, text=f'{label}:', bg=UI_BG, fg=UI_LABEL,
                     font=UI_FONT, anchor='e', width=12
                     ).grid(row=row, column=0, padx=(20, 6), pady=6, sticky='e')
            var = tk.StringVar(value=str(getattr(self, attr)))
            tk.Entry(panel, textvariable=var, width=8,
                     bg='#0a0a20', fg=UI_INPUT, insertbackground=UI_INPUT,
                     font=UI_FONT, relief='flat',
                     highlightthickness=1, highlightcolor=UI_BORDER,
                     highlightbackground=UI_BORDER
                     ).grid(row=row, column=1, padx=6, pady=6, sticky='w')
            entries[attr] = var
            tk.Label(panel, text=hint, bg=UI_BG, fg=UI_HINT,
                     font=UI_SMALL).grid(row=row, column=2, padx=(4, 20), sticky='w')

        msg_var = tk.StringVar()
        tk.Label(panel, textvariable=msg_var, bg=UI_BG, fg=UI_ERR,
                 font=UI_SMALL).grid(row=5, column=0, columnspan=3, pady=(4, 0))
        tk.Label(panel, text='ENTER = aplicar y reiniciar    ESC = cancelar',
                 bg=UI_BG, fg=UI_HINT, font=UI_SMALL
                 ).grid(row=6, column=0, columnspan=3, pady=(6, 16))
        tk.Frame(panel, bg=UI_BORDER, height=1).grid(
            row=7, column=0, columnspan=3, sticky='ew', padx=20, pady=(0, 14))

        def aplicar(event=None):
            try:
                ns  = int(entries['num_stars'].get())
                sp  = int(entries['speed'].get())
                fps = int(entries['fps'].get())
                if not (1 <= ns <= 1000):  raise ValueError('Estrellas: 1–1000')
                if not (1 <= sp <= 20):    raise ValueError('Velocidad: 1–20')
                if not (10 <= fps <= 120): raise ValueError('FPS: 10–120')
            except ValueError as e:
                msg_var.set(f'✗  {e}')
                return
            self.num_stars = ns
            self.speed     = sp
            self.fps       = fps
            cerrar_panel()
            self._init_stars(spread_z=False)
            self._draw_signature()
            self._paused = False
            self.root.focus_set()

        def cerrar_panel(event=None):
            if self._panel:
                self._panel.destroy()
                self._panel = None

        def cancelar(event=None):
            cerrar_panel()
            self._paused = False
            self.root.focus_set()

        panel.bind('<Return>', aplicar)
        panel.bind('<Escape>', cancelar)
        for child in panel.winfo_children():
            child.bind('<Return>', aplicar)
            child.bind('<Escape>', cancelar)

        first_entry = panel.grid_slaves(row=2, column=1)
        if first_entry:
            first_entry[0].focus_set()
            first_entry[0].select_range(0, 'end')


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app  = Starfield(root)
    root.mainloop()
