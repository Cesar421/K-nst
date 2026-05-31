"""
Generador de Armonías de Color
================================
Rueda interactiva con 9 esquemas de armonía cromática.
Haz clic en la rueda, ajusta sliders, introduce hex manualmente.
"""

import pygame
import colorsys
import math
import sys

pygame.init()

# ── Dimensiones ──────────────────────────────────────────────────────────────
W, H = 1050, 680
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Generador de Armonías de Color")
clock = pygame.time.Clock()

# ── Colores UI ────────────────────────────────────────────────────────────────
BG        = (18,  18,  22)
PANEL     = (28,  28,  34)
CARD      = (38,  38,  46)
BORDER    = (60,  60,  74)
TEXT      = (220, 220, 228)
TEXT_DIM  = (130, 130, 148)
ACCENT    = (110, 100, 240)
WHITE     = (255, 255, 255)

# ── Fuentes ───────────────────────────────────────────────────────────────────
try:
    FONT_SM  = pygame.font.SysFont("segoeui",   13)
    FONT_MD  = pygame.font.SysFont("segoeui",   15)
    FONT_LG  = pygame.font.SysFont("segoeui",   18, bold=True)
    FONT_XL  = pygame.font.SysFont("segoeui",   22, bold=True)
    FONT_MONO= pygame.font.SysFont("consolas",  14)
except Exception:
    FONT_SM = FONT_MD = FONT_LG = FONT_XL = FONT_MONO = pygame.font.Font(None, 16)

# ── Esquemas de armonía ───────────────────────────────────────────────────────
SCHEMES = [
    ("Complementario",    "comp"),
    ("Análogo",           "analog"),
    ("Monocromático",     "mono"),
    ("Tríada",            "triad"),
    ("Split-Comp.",       "split"),
    ("Tétrada Rect.",     "tetrad"),
    ("Cuadrado",          "square"),
    ("Pentágono",         "penta"),
    ("Hexágono",          "hexa"),
]

SCHEME_INFO = {
    "comp":   ("2 colores — Opuestos 180°",   "Máximo contraste. Uno domina, el otro acenta. Ideal: botones CTA, señalética."),
    "analog": ("3-6 colores — Vecinos 30°",   "Armonía natural y fluida. Ideal: interfaces, moda, naturaleza."),
    "mono":   ("2-6 colores — Mismo matiz",   "Sofisticado y cohesivo. Varía luminosidad y saturación. Ideal: minimalismo."),
    "triad":  ("3 colores — Equidistantes 120°","Vibrante y equilibrado. Ideal: infografías, ilustración, identidades."),
    "split":  ("3 colores — Flancos del comp.","Contraste fuerte pero menos tenso. Ideal: packaging, web de impacto."),
    "tetrad": ("4 colores — Dos pares comp.",  "Rico y complejo. Un color debe dominar. Ideal: editorial, UI."),
    "square": ("4 colores — 90° exactos",      "Muy equilibrado. Ideal: dashboards, sistemas de diseño."),
    "penta":  ("5 colores — 72° entre sí",     "Para sistemas complejos con categorías definidas."),
    "hexa":   ("6 colores — 60° entre sí",     "Paleta completa. Ideal: visualización de datos, plataformas amplias."),
}

# ── Conversiones de color ─────────────────────────────────────────────────────
def hsl_to_rgb(h, s, l):
    """h 0-360, s 0-100, l 0-100  →  (r,g,b) 0-255"""
    r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
    return (int(r*255), int(g*255), int(b*255))

def rgb_to_hsl(r, g, b):
    """(r,g,b) 0-255  →  h 0-360, s 0-100, l 0-100"""
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return (h*360, s*100, l*100)

def hex_to_rgb(hex_str):
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c*2 for c in hex_str)
    if len(hex_str) != 6:
        return None
    try:
        return (int(hex_str[0:2],16), int(hex_str[2:4],16), int(hex_str[4:6],16))
    except ValueError:
        return None

def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"

def contrast_text(rgb):
    r, g, b = rgb
    lum = (0.299*r + 0.587*g + 0.114*b) / 255
    return (20, 20, 20) if lum > 0.55 else (240, 240, 240)

def get_harmony_hues(scheme, base_h, n):
    h = base_h
    if scheme == "comp":
        return [h, (h+180)%360]
    elif scheme == "analog":
        step = 28
        half = (n-1)//2
        return [(h + (i-half)*step) % 360 for i in range(n)]
    elif scheme == "mono":
        return [h]*n
    elif scheme == "triad":
        return [h, (h+120)%360, (h+240)%360]
    elif scheme == "split":
        return [h, (h+150)%360, (h+210)%360]
    elif scheme == "tetrad":
        return [h, (h+60)%360, (h+180)%360, (h+240)%360]
    elif scheme == "square":
        return [(h + i*90) % 360 for i in range(4)]
    elif scheme == "penta":
        return [(h + i*72) % 360 for i in range(5)]
    elif scheme == "hexa":
        return [(h + i*60) % 360 for i in range(6)]
    return [h]

def get_palette(scheme, base_h, sat, lit, n):
    hues = get_harmony_hues(scheme, base_h, n)
    colors = []
    if scheme == "mono":
        lits = [max(20, min(80, 15 + int(i * 60 / max(n-1,1)))) for i in range(n)]
        sats = [max(20, sat - i*8) for i in range(n)]
        for i in range(n):
            rgb = hsl_to_rgb(base_h, sats[i], lits[i])
            colors.append(rgb)
    else:
        for hv in hues:
            rgb = hsl_to_rgb(hv, sat, lit)
            colors.append(rgb)
    return colors

# ── Rueda de color ─────────────────────────────────────────────────────────────
WHEEL_SURF = None
WHEEL_CX, WHEEL_CY, WHEEL_R = 180, 200, 130

def build_wheel(lit):
    global WHEEL_SURF
    size = WHEEL_R * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = WHEEL_R + 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist <= WHEEL_R:
                angle = (math.degrees(math.atan2(dy, dx)) + 90) % 360
                saturation = min(100.0, (dist / WHEEL_R) * 100)
                rgb = hsl_to_rgb(angle, saturation, lit)
                if dist > WHEEL_R - 1:
                    alpha = max(0, min(255, int((WHEEL_R - dist + 1) * 255)))
                else:
                    alpha = 255
                r = max(0, min(255, int(rgb[0])))
                g = max(0, min(255, int(rgb[1])))
                b = max(0, min(255, int(rgb[2])))
                surf.set_at((x, y), (r, g, b, alpha))
    WHEEL_SURF = surf

# ── Slider ─────────────────────────────────────────────────────────────────────
class Slider:
    def __init__(self, x, y, w, label, lo, hi, val, fmt="{:.0f}"):
        self.rect = pygame.Rect(x, y, w, 6)
        self.label = label
        self.lo, self.hi, self.val = lo, hi, val
        self.fmt = fmt
        self.dragging = False

    def thumb_x(self):
        t = (self.val - self.lo) / (self.hi - self.lo)
        return int(self.rect.x + t * self.rect.w)

    def draw(self, surf):
        tx = self.thumb_x()
        # track
        pygame.draw.rect(surf, BORDER, self.rect, border_radius=3)
        # fill
        fill = pygame.Rect(self.rect.x, self.rect.y, tx - self.rect.x, 6)
        pygame.draw.rect(surf, ACCENT, fill, border_radius=3)
        # thumb
        pygame.draw.circle(surf, WHITE, (tx, self.rect.centery), 9)
        pygame.draw.circle(surf, ACCENT, (tx, self.rect.centery), 7)
        # label
        lbl = FONT_SM.render(self.label, True, TEXT_DIM)
        surf.blit(lbl, (self.rect.x, self.rect.y - 18))
        # value
        val_txt = FONT_MONO.render(self.fmt.format(self.val), True, TEXT)
        surf.blit(val_txt, (self.rect.right - val_txt.get_width(), self.rect.y - 18))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            thumb = pygame.Rect(self.thumb_x()-10, self.rect.centery-10, 20, 20)
            if thumb.collidepoint(event.pos) or self.rect.inflate(0, 14).collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def _set_from_x(self, mx):
        t = max(0, min(1, (mx - self.rect.x) / self.rect.w))
        self.val = self.lo + t * (self.hi - self.lo)

# ── Caja de texto hex ──────────────────────────────────────────────────────────
class HexInput:
    def __init__(self, x, y, w=160):
        self.rect = pygame.Rect(x, y, w, 36)
        self.text = ""
        self.active = False
        self.error = False
        self.cursor_vis = True
        self.cursor_timer = 0

    def draw(self, surf):
        border_color = (220,80,80) if self.error else (ACCENT if self.active else BORDER)
        pygame.draw.rect(surf, CARD, self.rect, border_radius=8)
        pygame.draw.rect(surf, border_color, self.rect, 1, border_radius=8)
        display = "#" + self.text
        if self.active and self.cursor_vis:
            display += "|"
        txt = FONT_MONO.render(display, True, TEXT if not self.error else (220,100,100))
        surf.blit(txt, (self.rect.x+10, self.rect.centery - txt.get_height()//2))
        hint = FONT_SM.render("Introduce hex (ej: #FF6B35) y presiona Enter", True, TEXT_DIM)
        surf.blit(hint, (self.rect.x, self.rect.y - 20))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.error = False
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.error = False
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "submit"
            elif event.unicode in "0123456789abcdefABCDEF#" and len(self.text) < 6:
                ch = event.unicode.lstrip("#").upper()
                self.text += ch
                self.error = False
        return None

    def tick(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer > 500:
            self.cursor_vis = not self.cursor_vis
            self.cursor_timer = 0

# ── Estado global ──────────────────────────────────────────────────────────────
state = {
    "hue": 15.0,
    "sat": 80.0,
    "lit": 52.0,
    "scheme": "comp",
    "n": 4,
    "copied": None,
    "copied_timer": 0,
}

sliders = [
    Slider(560, 100, 220, "Matiz (Hue)",       0, 360, state["hue"], "{:.0f}°"),
    Slider(560, 160, 220, "Saturación",         10, 100, state["sat"], "{:.0f}%"),
    Slider(560, 220, 220, "Luminosidad",         20, 80,  state["lit"], "{:.0f}%"),
    Slider(560, 280, 220, "Número de colores",   2,  8,   state["n"],   "{:.0f}"),
]

hex_input = HexInput(560, 370)

def sync_sliders_to_state():
    sliders[0].val = state["hue"]
    sliders[1].val = state["sat"]
    sliders[2].val = state["lit"]

build_wheel(state["lit"])

# ── Botones de esquema ─────────────────────────────────────────────────────────
SCHEME_BTNS = []
bx, by = 560, 440
bw, bh = 100, 30
for i, (name, key) in enumerate(SCHEMES):
    col = i % 4
    row = i // 4
    SCHEME_BTNS.append({
        "rect": pygame.Rect(bx + col*(bw+8), by + row*(bh+6), bw, bh),
        "key": key,
        "name": name,
    })

# ── Helpers de dibujo ──────────────────────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=10, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)

def draw_text_center(surf, text, font, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))

def draw_wheel_marker(surf, base_h, sat, lit):
    cx = WHEEL_CX
    cy = WHEEL_CY
    r  = WHEEL_R
    rad = math.radians(base_h - 90)
    t   = sat / 100
    x   = int(cx + r * t * math.cos(rad))
    y   = int(cy + r * t * math.sin(rad))
    pygame.draw.circle(surf, WHITE, (x, y), 9)
    pygame.draw.circle(surf, hsl_to_rgb(base_h, sat, lit), (x, y), 7)
    pygame.draw.circle(surf, (40,40,40), (x, y), 9, 1)

def draw_wheel_harmony_dots(surf, scheme, base_h, sat, lit):
    hues = get_harmony_hues(scheme, base_h, int(state["n"]))
    for i, hv in enumerate(hues):
        if abs(hv - base_h) < 0.5:
            continue
        rad = math.radians(hv - 90)
        t   = sat / 100
        x   = int(WHEEL_CX + WHEEL_R * t * math.cos(rad))
        y   = int(WHEEL_CY + WHEEL_R * t * math.sin(rad))
        pygame.draw.circle(surf, hsl_to_rgb(hv, sat, lit), (x,y), 7)
        pygame.draw.circle(surf, WHITE, (x,y), 7, 2)

# ── Loop principal ─────────────────────────────────────────────────────────────
running = True
palette = []
wheel_dirty = True

while running:
    dt = clock.tick(60)

    # ── Eventos ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Sliders
        slider_changed = False
        for sl in sliders:
            if sl.handle_event(event):
                slider_changed = True

        if slider_changed:
            state["hue"] = sliders[0].val
            state["sat"] = sliders[1].val
            state["lit"] = sliders[2].val
            state["n"]   = int(sliders[3].val)
            if abs(sliders[2].val - state["lit"]) > 0.5:
                wheel_dirty = True

        # Clic en la rueda
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            dx, dy = mx - WHEEL_CX, my - WHEEL_CY
            dist = math.hypot(dx, dy)
            if dist <= WHEEL_R:
                state["hue"] = (math.degrees(math.atan2(dy, dx)) + 90) % 360
                state["sat"] = min(100, (dist / WHEEL_R) * 100)
                sliders[0].val = state["hue"]
                sliders[1].val = state["sat"]

        # Botones de esquema
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in SCHEME_BTNS:
                if btn["rect"].collidepoint(event.pos):
                    state["scheme"] = btn["key"]

        # Clic en swatches (copiar hex)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, color in enumerate(palette):
                sx = 30 + i * (swatch_w + 10) if palette else 0
                sr = pygame.Rect(sx, 500, swatch_w if palette else 0, 110)
                if sr.collidepoint(event.pos):
                    hex_val = rgb_to_hex(*color)
                    try:
                        pygame.scrap.init()
                        pygame.scrap.put(pygame.SCRAP_TEXT, hex_val.encode())
                    except Exception:
                        pass
                    state["copied"] = hex_val
                    state["copied_timer"] = 1800

        # Hex input
        result = hex_input.handle_event(event)
        if result == "submit":
            rgb = hex_to_rgb(hex_input.text)
            if rgb:
                h, s, l = rgb_to_hsl(*rgb)
                state["hue"] = h
                state["sat"] = max(10, s)
                state["lit"] = max(20, min(80, l))
                sync_sliders_to_state()
                hex_input.text = ""
                hex_input.error = False
                wheel_dirty = True
            else:
                hex_input.error = True

    # Reconstruir rueda si cambia luminosidad
    if wheel_dirty:
        build_wheel(int(state["lit"]))
        wheel_dirty = False

    # Paleta actual
    palette = get_palette(
        state["scheme"],
        state["hue"],
        state["sat"],
        state["lit"],
        int(state["n"]),
    )

    n_swatches = len(palette)
    swatch_area_w = 510
    swatch_w = max(60, (swatch_area_w - (n_swatches - 1) * 10) // n_swatches)

    # Temporizador "copiado"
    if state["copied_timer"] > 0:
        state["copied_timer"] -= dt

    # ── Dibujo ────────────────────────────────────────────────────────────────
    screen.fill(BG)

    # Panel izquierdo
    pygame.draw.rect(screen, PANEL, (0, 0, 540, H))

    # Título
    title = FONT_XL.render("Armonías de Color", True, TEXT)
    screen.blit(title, (20, 18))
    sub = FONT_SM.render("Generador interactivo — haz clic en la rueda o introduce un código hex", True, TEXT_DIM)
    screen.blit(sub, (20, 48))

    # Rueda de color
    if WHEEL_SURF:
        screen.blit(WHEEL_SURF, (WHEEL_CX - WHEEL_R - 2, WHEEL_CY - WHEEL_R - 2))
    pygame.draw.circle(screen, BORDER, (WHEEL_CX, WHEEL_CY), WHEEL_R + 2, 1)

    draw_wheel_harmony_dots(screen, state["scheme"], state["hue"], state["sat"], state["lit"])
    draw_wheel_marker(screen, state["hue"], state["sat"], state["lit"])

    # Info del esquema
    sch_key = state["scheme"]
    sch_title, sch_desc = SCHEME_INFO.get(sch_key, ("", ""))
    info_x = 340
    t1 = FONT_MD.render(sch_title, True, TEXT)
    screen.blit(t1, (info_x, 80))
    words = sch_desc.split()
    line, lines = "", []
    for w in words:
        test = line + (" " if line else "") + w
        if FONT_SM.size(test)[0] > 175:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    for j, ln in enumerate(lines):
        s = FONT_SM.render(ln, True, TEXT_DIM)
        screen.blit(s, (info_x, 104 + j*17))

    # Color base (hex grande)
    base_rgb = hsl_to_rgb(state["hue"], state["sat"], state["lit"])
    base_hex = rgb_to_hex(*base_rgb)
    pygame.draw.rect(screen, base_rgb, (340, 170, 60, 60), border_radius=10)
    pygame.draw.rect(screen, BORDER, (340, 170, 60, 60), 1, border_radius=10)
    bh_txt = FONT_MONO.render(base_hex, True, TEXT)
    screen.blit(bh_txt, (408, 188))
    bl_txt = FONT_SM.render("Color base", True, TEXT_DIM)
    screen.blit(bl_txt, (408, 170))
    hsl_txt = FONT_SM.render(f"H:{state['hue']:.0f}° S:{state['sat']:.0f}% L:{state['lit']:.0f}%", True, TEXT_DIM)
    screen.blit(hsl_txt, (408, 208))

    # Swatches de paleta
    palette_label = FONT_MD.render("Paleta generada", True, TEXT)
    screen.blit(palette_label, (20, 468))

    for i, color in enumerate(palette):
        sx = 20 + i * (swatch_w + 10)
        sy = 492
        pygame.draw.rect(screen, color, (sx, sy, swatch_w, 110), border_radius=10)
        pygame.draw.rect(screen, BORDER, (sx, sy, swatch_w, 110), 1, border_radius=10)
        hex_c = rgb_to_hex(*color)
        ct = contrast_text(color)
        # hex
        hx = FONT_MONO.render(hex_c, True, ct)
        hx_scale = min(1.0, (swatch_w - 10) / max(hx.get_width(), 1))
        if hx_scale < 1.0:
            hx = pygame.transform.scale(hx, (int(hx.get_width()*hx_scale), hx.get_height()))
        screen.blit(hx, (sx + (swatch_w - hx.get_width())//2, sy + 72))
        # rgb
        rg = FONT_SM.render(f"{color[0]},{color[1]},{color[2]}", True, ct)
        rg_s = min(1.0, (swatch_w - 6) / max(rg.get_width(), 1))
        if rg_s < 1.0:
            rg = pygame.transform.scale(rg, (int(rg.get_width()*rg_s), rg.get_height()))
        screen.blit(rg, (sx + (swatch_w - rg.get_width())//2, sy + 90))
        # "Copiar" hint
        if swatch_w > 80:
            cp = FONT_SM.render("clic = copiar", True, ct)
            screen.blit(cp, (sx + (swatch_w - cp.get_width())//2, sy + 8))

    # Notificación de copiado
    if state["copied_timer"] > 0:
        alpha = min(255, state["copied_timer"] * 255 // 400)
        notif = FONT_MD.render(f"  {state['copied']} copiado  ", True, WHITE)
        nr = pygame.Rect(20, 614, notif.get_width() + 20, 34)
        pygame.draw.rect(screen, (50, 180, 100), nr, border_radius=8)
        screen.blit(notif, (nr.x + 10, nr.centery - notif.get_height()//2))

    # ── Panel derecho ──────────────────────────────────────────────────────────
    pygame.draw.rect(screen, PANEL, (540, 0, W-540, H))
    pygame.draw.line(screen, BORDER, (540, 0), (540, H), 1)

    # Sliders
    for sl in sliders:
        sl.draw(screen)

    # Hex input
    hex_input.tick(dt)
    hex_input.draw(screen)

    # Botones de esquema
    sch_label = FONT_MD.render("Esquemas de armonía", True, TEXT)
    screen.blit(sch_label, (560, 422))

    for btn in SCHEME_BTNS:
        active = btn["key"] == state["scheme"]
        bg = ACCENT if active else CARD
        border = ACCENT if active else BORDER
        pygame.draw.rect(screen, bg, btn["rect"], border_radius=8)
        pygame.draw.rect(screen, border, btn["rect"], 1, border_radius=8)
        tc = WHITE if active else TEXT_DIM
        t = FONT_SM.render(btn["name"], True, tc)
        screen.blit(t, (btn["rect"].centerx - t.get_width()//2,
                        btn["rect"].centery - t.get_height()//2))

    # Guía de uso rápido
    tips_y = 580
    tips = [
        "Rueda: clic para elegir matiz y saturación",
        "Sliders: ajuste fino de cada parámetro",
        "Hex input: pega o escribe un código y presiona Enter",
        "Swatches: clic para copiar el código de color",
    ]
    guide = FONT_SM.render("Guía rápida", True, TEXT)
    screen.blit(guide, (560, tips_y))
    for k, tip in enumerate(tips):
        ts = FONT_SM.render(f"• {tip}", True, TEXT_DIM)
        screen.blit(ts, (560, tips_y + 18 + k*17))

    pygame.display.flip()

pygame.quit()
sys.exit()