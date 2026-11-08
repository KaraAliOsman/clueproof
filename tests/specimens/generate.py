#!/usr/bin/env python3
"""Deterministic generator of fictional SPECIMEN test photos for the "Before You Share" Skill.

Usage (from the repository root):

    python tests/specimens/generate.py

Writes
    tests/specimens/beach-day/B01..B12      1600x1200 JPEG (quality 82)
    tests/specimens/hazard-set/H01..H10     1600x1200 JPEG; H09 is a 1170x2532 PNG calculator screenshot
    tests/specimens/MANIFEST.md             table of every image (generated, do not edit by hand)
    docs/assets/specimens/*.jpg             web copies, 640 px wide (screenshot 320 px), quality 70, no EXIF
    docs/assets/specimens/manifest.json     machine-readable manifest for the website

Every scene is drawn from code with fixed seeds and fixed EXIF dates, so a re-run with the same
Pillow version and fonts produces byte-identical files. Every person, place, company, plate and
number is fictional (Republic of Exemplia, Lakeside, Harbor St, Exemplia Air, Exemplia Bank).
No real government, airline or bank design is imitated.
"""

from __future__ import annotations

import functools
import hashlib
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from PIL.TiffImagePlugin import IFDRational

HERE = Path(__file__).resolve().parent              # tests/specimens
REPO = HERE.parent.parent
WEB = REPO / "docs" / "assets" / "specimens"

W, H = 1600, 1200            # photo size
SW, SH = 1170, 2532          # phone screenshot size
SS = 2                       # supersampling factor (draw at 2x, downsample for smooth edges)
JPEG_Q, WEB_Q = 82, 70
WEB_W, WEB_W_SHOT = 640, 320
GENERATED = "2026-11-08"
DATE = "2025:07:19"
DESCRIPTION = "SPECIMEN - fictional generated test image (Before You Share)"
SOFTWARE = "Before You Share specimen generator"

# Public beach landmark (Barceloneta beach area, Barcelona): a public place, not a home.
GPS_LAT = (41, 22, 42.24)    # 41.3784 N
GPS_LON = (2, 11, 33.0)      # 2.1925 E
GPS_PLACE = "Barceloneta beach area"


# --------------------------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------------------------

def _mpl_font_dir():
    try:
        import matplotlib  # optional, only used to find a bundled DejaVu font
        return Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    except Exception:
        return None


_FONT_FILES = {
    "bold": ["DejaVuSans-Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    "regular": ["DejaVuSans.ttf", "arial.ttf", "LiberationSans-Regular.ttf", "Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf"],
    "cond": ["DejaVuSansCondensed-Bold.ttf", "arialnb.ttf", "LiberationSansNarrow-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"],
    "mono": ["DejaVuSansMono-Bold.ttf", "consolab.ttf", "LiberationMono-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"],
    "hand": ["segoeprb.ttf", "comicbd.ttf", "Comic Sans MS Bold.ttf",
             "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf", "DejaVuSans-BoldOblique.ttf"],
}
_FALLBACK = {"cond": "bold", "mono": "bold", "hand": "bold", "regular": None, "bold": None}


@functools.lru_cache(maxsize=None)
def _font_path(kind):
    candidates = list(_FONT_FILES[kind])
    mpl = _mpl_font_dir()
    if mpl:
        candidates += [str(mpl / Path(c).name) for c in _FONT_FILES[kind] if c.startswith("DejaVu")]
    for cand in candidates:
        try:
            ImageFont.truetype(cand, 12)
            return cand
        except OSError:
            continue
    return None


@functools.lru_cache(maxsize=None)
def font(kind, px):
    """Return (font, faux_bold_stroke) for a font kind at a pixel size."""
    path = _font_path(kind)
    if path:
        return ImageFont.truetype(path, px), 0
    if _FALLBACK.get(kind):
        return font(_FALLBACK[kind], px)
    # Pillow's bundled scalable font; embolden with a stroke when bold is wanted.
    return ImageFont.load_default(px), (max(1, px // 28) if kind == "bold" else 0)


def fonts_in_use():
    return {k: (Path(_font_path(k)).name if _font_path(k) else "Pillow default") for k in _FONT_FILES}


# --------------------------------------------------------------------------------------------
# Colour helpers
# --------------------------------------------------------------------------------------------

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def mix(c1, c2, t):
    t = clamp(t)
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def ramp(stops, t):
    t = clamp(t)
    if not isinstance(stops[0][0], (int, float)) or len(stops[0]) != 2 or isinstance(stops[0][1], int):
        stops = [(i / (len(stops) - 1), s) for i, s in enumerate(stops)]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0) if p1 > p0 else 0)
    return tuple(stops[-1][1])


def darken(c, f):
    return tuple(int(round(v * (1 - f))) for v in c[:3])


def lighten(c, f):
    return tuple(int(round(v + (255 - v) * f)) for v in c[:3])


def lerp_pt(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# --------------------------------------------------------------------------------------------
# Canvas: logical coordinates, drawn at SS x resolution
# --------------------------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255), mode="RGB"):
        self.w, self.h, self.mode = w, h, mode
        if mode == "RGBA" and len(bg) == 3:
            bg = (*bg, 0)
        self.img = Image.new(mode, (int(w * SS), int(h * SS)), bg)
        self.d = ImageDraw.Draw(self.img)

    # -- internals ---------------------------------------------------------------------------
    def _c(self, color):
        if color is None:
            return None
        color = tuple(int(v) for v in color)
        if self.mode == "RGBA" and len(color) == 3:
            return (*color, 255)
        if self.mode == "RGB" and len(color) == 4:
            return color[:3]
        return color

    @staticmethod
    def _xy(pts):
        return [(x * SS, y * SS) for x, y in pts]

    @staticmethod
    def _b(b):
        return [b[0] * SS, b[1] * SS, b[2] * SS, b[3] * SS]

    def _region(self, xs, ys, pad):
        X0 = max(0, int(math.floor((min(xs) - pad) * SS)))
        Y0 = max(0, int(math.floor((min(ys) - pad) * SS)))
        X1 = min(self.img.width, int(math.ceil((max(xs) + pad) * SS)) + 1)
        Y1 = min(self.img.height, int(math.ceil((max(ys) + pad) * SS)) + 1)
        return X0, Y0, X1, Y1

    def _paste_mask(self, src, xy, mask):
        X, Y = xy
        mw, mh = mask.size
        cx0, cy0 = max(0, -X), max(0, -Y)
        cx1, cy1 = min(mw, self.img.width - X), min(mh, self.img.height - Y)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        m = mask.crop((cx0, cy0, cx1, cy1))
        box = (X + cx0, Y + cy0, X + cx1, Y + cy1)
        if isinstance(src, tuple):
            self.img.paste(self._c(src), box, m)
        else:
            s = src.crop((cx0, cy0, cx1, cy1))
            if self.mode == "RGB":
                self.img.paste(s.convert("RGB"), box, m)
            else:
                s = s.convert("RGBA")
                s.putalpha(ImageChops.multiply(s.getchannel("A"), m))
                self.img.alpha_composite(s, (box[0], box[1]))

    # -- primitives --------------------------------------------------------------------------
    def rect(self, b, fill=None, outline=None, width=0, r=0):
        w = max(1, int(round(width * SS))) if outline is not None else 0
        if r:
            self.d.rounded_rectangle(self._b(b), radius=r * SS, fill=self._c(fill),
                                     outline=self._c(outline), width=w)
        else:
            self.d.rectangle(self._b(b), fill=self._c(fill), outline=self._c(outline), width=w)

    def ellipse(self, b, fill=None, outline=None, width=0):
        w = max(1, int(round(width * SS))) if outline is not None else 0
        self.d.ellipse(self._b(b), fill=self._c(fill), outline=self._c(outline), width=w)

    def poly(self, pts, fill=None, outline=None, width=0):
        w = max(1, int(round(width * SS))) if outline is not None else 0
        self.d.polygon(self._xy(pts), fill=self._c(fill), outline=self._c(outline), width=w)

    def line(self, pts, fill, width=1.0, joint="curve"):
        self.d.line(self._xy(pts), fill=self._c(fill), width=max(1, int(round(width * SS))), joint=joint)

    def arc(self, b, start, end, fill, width=1.0):
        self.d.arc(self._b(b), start, end, fill=self._c(fill), width=max(1, int(round(width * SS))))

    def pieslice(self, b, start, end, fill):
        self.d.pieslice(self._b(b), start, end, fill=self._c(fill))

    def chord(self, b, start, end, fill):
        self.d.chord(self._b(b), start, end, fill=self._c(fill))

    def vgrad(self, b, stops):
        x0, y0, x1, y1 = [int(round(v * SS)) for v in b]
        n = max(1, y1 - y0 - 1)
        for y in range(y0, y1):
            self.d.line([(x0, y), (x1 - 1, y)], fill=self._c(ramp(stops, (y - y0) / n)))

    def hgrad(self, b, stops):
        x0, y0, x1, y1 = [int(round(v * SS)) for v in b]
        n = max(1, x1 - x0 - 1)
        for x in range(x0, x1):
            self.d.line([(x, y0), (x, y1 - 1)], fill=self._c(ramp(stops, (x - x0) / n)))

    def _shape_mask(self, kind, geom, alpha, width, r, pad):
        if kind in ("ellipse", "rect", "rrect"):
            xs, ys = [geom[0], geom[2]], [geom[1], geom[3]]
        else:
            xs, ys = [p[0] for p in geom], [p[1] for p in geom]
        X0, Y0, X1, Y1 = self._region(xs, ys, pad + width + 2)
        if X1 <= X0 or Y1 <= Y0:
            return None
        m = Image.new("L", (X1 - X0, Y1 - Y0), 0)
        md = ImageDraw.Draw(m)

        def t(x, y):
            return (x * SS - X0, y * SS - Y0)

        if kind == "ellipse":
            md.ellipse([*t(geom[0], geom[1]), *t(geom[2], geom[3])], fill=alpha)
        elif kind == "rect":
            md.rectangle([*t(geom[0], geom[1]), *t(geom[2], geom[3])], fill=alpha)
        elif kind == "rrect":
            md.rounded_rectangle([*t(geom[0], geom[1]), *t(geom[2], geom[3])], radius=r * SS, fill=alpha)
        elif kind == "poly":
            md.polygon([t(*p) for p in geom], fill=alpha)
        elif kind == "line":
            md.line([t(*p) for p in geom], fill=alpha, width=max(1, int(round(width * SS))), joint="curve")
        return m, (X0, Y0), (min(xs), min(ys), max(xs), max(ys))

    def soft(self, kind, geom, color, alpha=255, blur=0.0, width=1.0, r=0):
        """Draw a shape with partial opacity and an optional Gaussian-blurred edge."""
        res = self._shape_mask(kind, geom, int(alpha), width, r, blur * 3)
        if not res:
            return
        m, (X0, Y0), _ = res
        if blur:
            m = m.filter(ImageFilter.GaussianBlur(blur * SS))
        self._paste_mask(tuple(color[:3]), (X0, Y0), m)

    def grad_fill(self, kind, geom, stops, vertical=True, r=0, alpha=255):
        """Fill a shape with a linear gradient measured across the shape's own bounds."""
        res = self._shape_mask(kind, geom, int(alpha), 0, r, 0)
        if not res:
            return
        m, (X0, Y0), (bx0, by0, bx1, by1) = res
        w, h = m.size
        if vertical:
            span0, span1, n = by0 * SS, by1 * SS, h
            colors = [ramp(stops, (Y0 + i - span0) / max(1, span1 - span0)) for i in range(n)]
            g = Image.new("RGB", (1, n))
            g.putdata(colors)
            g = g.resize((w, h), Image.NEAREST)
        else:
            span0, span1, n = bx0 * SS, bx1 * SS, w
            colors = [ramp(stops, (X0 + i - span0) / max(1, span1 - span0)) for i in range(n)]
            g = Image.new("RGB", (n, 1))
            g.putdata(colors)
            g = g.resize((w, h), Image.NEAREST)
        self._paste_mask(g, (X0, Y0), m)

    # -- text --------------------------------------------------------------------------------
    def text(self, xy, s, size, fill, kind="bold", anchor="la", stroke=0.0, stroke_fill=None):
        f, fb = font(kind, int(round(size * SS)))
        sw = int(round(stroke * SS)) + fb
        pos = (xy[0] * SS, xy[1] * SS)
        self.d.text(pos, s, font=f, fill=self._c(fill), anchor=anchor, stroke_width=sw,
                    stroke_fill=self._c(stroke_fill or fill))
        bb = self.d.textbbox(pos, s, font=f, anchor=anchor, stroke_width=sw)
        return tuple(v / SS for v in bb)

    def text_width(self, s, size, kind="bold"):
        f, fb = font(kind, int(round(size * SS)))
        bb = f.getbbox(s, stroke_width=fb)
        return (bb[2] - bb[0]) / SS

    def fit(self, s, size, max_w, kind="bold", min_size=8):
        while size > min_size and self.text_width(s, size, kind) > max_w:
            size -= 1
        return size

    # -- composition -------------------------------------------------------------------------
    def place(self, layer, center, angle=0.0, shadow=None):
        """Paste an RGBA layer (Canvas or Image) centred at a logical point; return its logical bbox."""
        lay = layer.img if isinstance(layer, Canvas) else layer
        if angle:
            lay = lay.rotate(angle, resample=Image.BICUBIC, expand=True)
        X = int(round(center[0] * SS - lay.width / 2))
        Y = int(round(center[1] * SS - lay.height / 2))
        a = lay.getchannel("A")
        if shadow:
            dx, dy, blur, op = shadow
            pad = int(blur * SS * 3) + 2
            m = Image.new("L", (lay.width + 2 * pad, lay.height + 2 * pad), 0)
            m.paste(a, (pad, pad))
            m = m.filter(ImageFilter.GaussianBlur(blur * SS)).point(lambda v: v * op // 255)
            self._paste_mask((0, 0, 0), (X + int(dx * SS) - pad, Y + int(dy * SS) - pad), m)
        self._paste_mask(lay, (X, Y), a)
        bb = a.getbbox()
        return ((X + bb[0]) / SS, (Y + bb[1]) / SS, (X + bb[2]) / SS, (Y + bb[3]) / SS)

    def blur_region(self, b, radius, feather=0.0):
        X0, Y0, X1, Y1 = self._region([b[0], b[2]], [b[1], b[3]], radius * 3 + feather * 3)
        crop = self.img.crop((X0, Y0, X1, Y1)).filter(ImageFilter.GaussianBlur(radius * SS))
        if feather:
            m = Image.new("L", crop.size, 0)
            ImageDraw.Draw(m).rectangle([b[0] * SS - X0, b[1] * SS - Y0, b[2] * SS - X0, b[3] * SS - Y0], fill=255)
            m = m.filter(ImageFilter.GaussianBlur(feather * SS))
            self.img.paste(crop, (X0, Y0), m)
        else:
            inner = crop.crop((int(b[0] * SS - X0), int(b[1] * SS - Y0), int(b[2] * SS - X0), int(b[3] * SS - Y0)))
            self.img.paste(inner, (int(b[0] * SS), int(b[1] * SS)))

    def blur_all(self, radius):
        self.img = self.img.filter(ImageFilter.GaussianBlur(radius * SS))
        self.d = ImageDraw.Draw(self.img)

    def specimen_mark(self):
        """Small, unobtrusive visible SPECIMEN mark in the bottom-right corner."""
        size = 20
        tw = self.text_width("SPECIMEN", size)
        x1, y1 = self.w - 16, self.h - 16
        x0, y0 = x1 - tw - 22, y1 - 34
        self.soft("rrect", (x0, y0, x1, y1), (0, 0, 0), 120, r=8)
        self.text(((x0 + x1) / 2, (y0 + y1) / 2), "SPECIMEN", size, (255, 255, 255), anchor="mm")

    def result(self):
        img = self.img.convert("RGB") if self.mode != "RGB" else self.img
        return img.resize((int(self.w), int(self.h)), Image.LANCZOS)


def layer(w, h):
    return Canvas(w, h, (0, 0, 0), mode="RGBA")


# --------------------------------------------------------------------------------------------
# Reusable scene pieces
# --------------------------------------------------------------------------------------------

SKY_TOP, SKY_LOW = (84, 150, 218), (196, 226, 246)


def sky(c, y1, top=SKY_TOP, low=SKY_LOW, x0=0, x1=None):
    c.vgrad((x0, 0, x1 or c.w, y1), [(0, top), (1, low)])


def cloud(c, cx, cy, s=1.0):
    c.soft("ellipse", (cx - 160 * s, cy + 5 * s, cx + 160 * s, cy + 55 * s), (205, 218, 232), 150, blur=10 * s)
    for dx, dy, r in [(-100, 15, 55), (-45, -20, 75), (30, -35, 85), (100, 0, 65), (0, 20, 70), (150, 25, 40)]:
        c.soft("ellipse", (cx + (dx - r) * s, cy + (dy - r) * s, cx + (dx + r) * s, cy + (dy + r) * s),
               (255, 255, 255), 238, blur=3 * s)


def sun_glow(c, center, r, color=(255, 246, 210)):
    x, y = center
    c.soft("ellipse", (x - r * 3, y - r * 3, x + r * 3, y + r * 3), (255, 250, 225), 90, blur=r)
    c.soft("ellipse", (x - r, y - r, x + r, y + r), color, 255, blur=r * 0.08)


def sea(c, rng, y0, y1, far=(36, 104, 156), near=(66, 160, 180), x0=0, x1=None, lines=220):
    x1 = x1 or c.w
    c.vgrad((x0, y0, x1, y1), [(0, far), (1, near)])
    c.soft("rect", (x0, y0 - 3, x1, y0 + 5), (215, 232, 245), 140, blur=2)
    for _ in range(lines):
        t = rng.random() ** 0.8
        y = y0 + 6 + (y1 - y0 - 10) * t
        length = 15 + 140 * t
        x = rng.uniform(x0 - 50, x1)
        c.soft("line", [(x, y), (x + length, y + rng.uniform(-1, 1))], (232, 246, 252),
               int(50 + 110 * t), width=0.8 + 2.4 * t)


def shore(c, y, amp=10, phase=1.3, foam=(250, 252, 250), wet=(204, 182, 140)):
    pts = [(x, y + amp * math.sin(x / 90 + phase) + amp * 0.5 * math.sin(x / 37 + 2 * phase))
           for x in range(-20, int(c.w) + 41, 20)]
    c.soft("poly", pts + [(c.w + 40, y + 70), (-20, y + 70)], wet, 255, blur=6)
    c.soft("line", pts, foam, 235, width=10, blur=1.5)
    c.soft("line", [(x, yy + 14) for x, yy in pts], foam, 110, width=4, blur=2)


def sand(c, rng, y0, y1=None, top=(238, 218, 176), low=(222, 194, 146), specks=2200, x0=0, x1=None):
    y1 = y1 or c.h
    x1 = x1 or c.w
    c.vgrad((x0, y0, x1, y1), [(0, top), (1, low)])
    cols = [(204, 176, 128), (248, 236, 206), (188, 162, 122), (230, 206, 160)]
    for _ in range(specks):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(0.6, 1.8) * (0.6 + 0.8 * (y - y0) / max(1, y1 - y0))
        c.ellipse((x - r, y - r, x + r, y + r), fill=rng.choice(cols))


def umbrella(c, x, ground, size, col_a, col_b, n=8):
    top = ground - size * 1.3
    c.soft("ellipse", (x - size * 0.7, ground - size * 0.12, x + size * 1.1, ground + size * 0.16),
           (120, 92, 58), 105, blur=size * 0.07)
    c.line([(x, ground), (x, top)], (238, 238, 236), width=max(2, size * 0.035))
    apex = (x, top - size * 0.42)
    rim = [(x - size * math.cos(math.pi * k / n), top + size * 0.16 * math.sin(math.pi * k / n))
           for k in range(n + 1)]
    for k in range(n):
        a, b = rim[k], rim[k + 1]
        sag = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + size * 0.06)
        col = col_a if k % 2 == 0 else col_b
        col = darken(col, 0.22 * (k / n))
        c.poly([apex, a, sag, b], fill=col)
    c.ellipse((apex[0] - size * 0.03, apex[1] - size * 0.05, apex[0] + size * 0.03, apex[1] + size * 0.01),
              fill=(240, 240, 240))


def towel(c, quad, colors, n=7):
    c.soft("poly", [(px + 6, py + 8) for px, py in quad], (90, 70, 40), 70, blur=6)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        p = [lerp_pt(quad[0], quad[1], t0), lerp_pt(quad[0], quad[1], t1),
             lerp_pt(quad[3], quad[2], t1), lerp_pt(quad[3], quad[2], t0)]
        c.poly(p, fill=colors[i % len(colors)])


def beach_ball(c, cx, cy, r):
    c.soft("ellipse", (cx - r * 0.9, cy + r * 0.7, cx + r * 1.4, cy + r * 1.15), (110, 85, 50), 110, blur=r * 0.15)
    cols = [(230, 50, 50), (250, 250, 250), (40, 120, 220), (250, 250, 250), (250, 200, 40), (250, 250, 250)]
    for i, col in enumerate(cols):
        c.pieslice((cx - r, cy - r, cx + r, cy + r), i * 60 - 90, (i + 1) * 60 - 90, col)
    c.ellipse((cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18), fill=(250, 250, 250))
    c.soft("ellipse", (cx - r * 0.65, cy - r * 0.75, cx - r * 0.05, cy - r * 0.25), (255, 255, 255), 120, blur=r * 0.1)
    c.soft("ellipse", (cx - r, cy - r, cx + r, cy + r), (0, 0, 0), 0)


def sailboat(c, x, y, s):
    c.poly([(x - 40 * s, y), (x + 40 * s, y), (x + 30 * s, y + 10 * s), (x - 30 * s, y + 10 * s)], fill=(60, 60, 70))
    c.poly([(x - 2 * s, y - 4 * s), (x - 2 * s, y - 90 * s), (x - 38 * s, y - 4 * s)], fill=(250, 250, 248))
    c.poly([(x + 2 * s, y - 4 * s), (x + 2 * s, y - 70 * s), (x + 30 * s, y - 4 * s)], fill=(235, 238, 242))


def wood(c, rng, box, base=(150, 105, 68), dark=(112, 76, 46), light=(182, 134, 90), plank=None, lines=None):
    x0, y0, x1, y1 = box
    c.rect(box, fill=base)
    n = lines or int((y1 - y0) / 5)
    for _ in range(n):
        y = rng.uniform(y0, y1)
        amp, freq, ph = rng.uniform(2, 8), rng.uniform(0.002, 0.006), rng.uniform(0, 6.28)
        pts = [(x, y + amp * math.sin(x * freq + ph)) for x in range(int(x0) - 20, int(x1) + 41, 40)]
        c.soft("line", pts, rng.choice([dark, light]), rng.randint(25, 80), width=rng.uniform(1, 3.2))
    for _ in range(4):
        kx, ky = rng.uniform(x0, x1), rng.uniform(y0, y1)
        c.soft("ellipse", (kx - 40, ky - 9, kx + 40, ky + 9), dark, 90, blur=4)
    if plank:
        y = y0 + plank
        while y < y1:
            c.soft("line", [(x0, y), (x1, y)], darken(base, 0.45), 200, width=3)
            c.soft("line", [(x0, y + 3), (x1, y + 3)], light, 80, width=2)
            y += plank


def bokeh(c, rng, n, box, colors, rmin=20, rmax=60, alpha=(40, 90)):
    for _ in range(n):
        x, y = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3])
        r = rng.uniform(rmin, rmax)
        c.soft("ellipse", (x - r, y - r, x + r, y + r), rng.choice(colors), rng.randint(*alpha), blur=r * 0.15)


def pad_box(b, p, w, h):
    return (max(0, b[0] - p), max(0, b[1] - p), min(w, b[2] + p), min(h, b[3] + p))


def union(*boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


# --------------------------------------------------------------------------------------------
# Beach day
# --------------------------------------------------------------------------------------------

def draw_b01(rng):
    c = Canvas(W, H)
    sky(c, 470)
    sun_glow(c, (1390, 120), 60)
    for x, y, s in [(260, 150, 1.1), (820, 95, 0.8), (1150, 240, 0.9)]:
        cloud(c, x, y, s)
    sea(c, rng, 470, 720)
    sailboat(c, 1230, 462, 0.8)
    sailboat(c, 420, 466, 0.55)
    sand(c, rng, 720, 1200)
    shore(c, 728)
    umbrella(c, 720, 800, 95, (80, 170, 110), (250, 248, 240))
    towel(c, [(240, 990), (540, 960), (610, 1090), (290, 1130)], [(220, 60, 60), (250, 245, 235)], 8)
    umbrella(c, 430, 1000, 230, (225, 62, 55), (250, 248, 240))
    towel(c, [(900, 880), (1130, 865), (1180, 965), (930, 985)], [(40, 150, 190), (250, 220, 80)], 6)
    umbrella(c, 1060, 900, 185, (40, 120, 200), (250, 215, 70))
    beach_ball(c, 1360, 1050, 50)
    c.specimen_mark()
    return c.result(), {}


def draw_b02(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, 640), [(0, (48, 38, 92)), (0.4, (150, 66, 112)), (0.78, (240, 128, 72)), (1, (253, 192, 104))])
    for x, y, s in [(330, 210, 1.0), (1220, 150, 1.2)]:
        c.soft("ellipse", (x - 220 * s, y - 22 * s, x + 220 * s, y + 22 * s), (210, 110, 120), 120, blur=10)
    c.soft("ellipse", (800 - 330, 610 - 330, 800 + 330, 610 + 330), (255, 210, 130), 110, blur=90)
    c.ellipse((800 - 95, 610 - 95, 800 + 95, 610 + 95), fill=(255, 222, 140))
    c.vgrad((0, 640, W, 1010), [(0, (150, 70, 92)), (1, (36, 26, 56))])
    for i in range(46):
        t = i / 45
        y = 646 + t * 340
        half = 95 + 260 * t ** 1.3
        for _ in range(2):
            x = 800 + rng.uniform(-half, half)
            ln = rng.uniform(20, 70) * (1 + t)
            c.soft("line", [(x - ln / 2, y), (x + ln / 2, y)], (255, 205, 120), int(200 - 120 * t), width=2 + 3 * t)
    c.poly([(0, 640), (0, 560), (120, 540), (260, 575), (380, 610), (470, 640)], fill=(60, 34, 66))
    c.vgrad((0, 1000, W, H), [(0, (70, 44, 58)), (1, (38, 24, 36))])
    for x0 in (180, 1360):
        c.soft("line", [(x0, 1000), (x0 + 30, 1040)], (0, 0, 0), 0)
    for bx, by, s in [(560, 300, 1.0), (620, 340, 0.7), (1080, 260, 0.8)]:
        c.line([(bx - 22 * s, by - 6 * s), (bx, by + 4 * s), (bx + 22 * s, by - 6 * s)], (40, 24, 40), width=3 * s)
    return c.result(), {}


def draw_b03(rng):
    c = Canvas(W, H)
    sky(c, 230)
    cloud(c, 1200, 110, 0.9)
    sea(c, rng, 230, 430, lines=120)
    sand(c, rng, 430, 1200, specks=2600)
    shore(c, 436)
    cx = 800
    # moat and castle shadow
    c.soft("ellipse", (420, 820, 1200, 960), (176, 150, 112), 255, blur=6)
    c.soft("ellipse", (470, 845, 1150, 935), (120, 140, 150), 200, blur=4)
    c.soft("poly", [(1100, 870), (1260, 840), (1300, 900), (1150, 930)], (120, 95, 60), 120, blur=14)
    sand_c, shade, hi = (216, 180, 120), (180, 144, 92), (236, 206, 152)
    # back wall
    c.rect((560, 600, 1040, 870), fill=shade)
    c.rect((520, 640, 1080, 880), fill=sand_c)
    for x in range(520, 1080, 56):
        c.rect((x, 610, x + 30, 642), fill=sand_c)
    c.poly([(1080, 640), (1110, 620), (1110, 862), (1080, 880)], fill=shade)

    def tower(x0, x1, ytop, ybot):
        inset = (x1 - x0) * 0.09
        c.grad_fill("poly", [(x0, ybot), (x1, ybot), (x1 - inset, ytop), (x0 + inset, ytop)],
                    [(0, hi), (0.55, sand_c), (1, shade)], vertical=False)
        for k in range(1, 5):
            yy = ytop + (ybot - ytop) * k / 5
            c.soft("line", [(x0 + inset * (1 - k / 5), yy), (x1 - inset * (1 - k / 5), yy)], shade, 140, width=2)
        c.ellipse((x0 + inset, ytop - 16, x1 - inset, ytop + 16), fill=hi)
        step = (x1 - x0 - 2 * inset) / 5
        for k in range(5):
            if k % 2 == 0:
                c.rect((x0 + inset + k * step, ytop - 40, x0 + inset + (k + 1) * step, ytop), fill=sand_c)
        mid = (x0 + x1) / 2
        c.ellipse((mid - 14, ytop + 60, mid + 14, ytop + 88), fill=(96, 72, 44))
        c.rect((mid - 14, ytop + 74, mid + 14, ytop + 110), fill=(96, 72, 44))

    tower(450, 610, 470, 890)
    tower(990, 1150, 470, 890)
    tower(720, 880, 360, 880)
    c.line([(800, 330), (800, 210)], (110, 80, 50), width=5)
    c.poly([(803, 212), (880, 236), (803, 260)], fill=(220, 50, 50))
    c.ellipse((760, 760, 840, 820), fill=(90, 66, 40))
    c.rect((760, 790, 840, 880), fill=(90, 66, 40))
    # bucket
    c.soft("ellipse", (1230, 990, 1440, 1030), (110, 85, 55), 110, blur=8)
    c.grad_fill("poly", [(1230, 860), (1390, 860), (1370, 1010), (1250, 1010)],
                [(0, (70, 150, 230)), (1, (30, 90, 170))], vertical=False)
    c.ellipse((1230, 845, 1390, 880), fill=(25, 70, 140))
    c.ellipse((1240, 850, 1380, 874), fill=(196, 160, 104))
    c.arc((1222, 780, 1398, 940), 190, 350, (30, 30, 30), width=4)
    # spade
    c.line([(250, 1080), (470, 960)], (220, 50, 50), width=16)
    c.poly([(450, 950), (560, 880), (600, 940), (500, 1000)], fill=(250, 200, 40))
    # shells
    for sx, sy, col in [(330, 820, (245, 200, 200)), (1340, 700, (250, 240, 230)), (640, 1080, (240, 215, 190))]:
        c.pieslice((sx - 22, sy - 22, sx + 22, sy + 22), 180, 360, col)
        for a in range(195, 360, 30):
            c.line([(sx, sy), (sx + 20 * math.cos(math.radians(a)), sy + 20 * math.sin(math.radians(a)))],
                   darken(col, 0.2), width=1.5)
    return c.result(), {}


def draw_b04(rng):
    c = Canvas(W, H)
    sky(c, 420, top=(110, 170, 225))
    sea(c, rng, 420, 640, lines=80)
    sand(c, rng, 640, 1200, specks=600)
    umbrella(c, 260, 700, 200, (230, 80, 60), (250, 245, 235))
    umbrella(c, 1350, 680, 220, (60, 140, 210), (250, 220, 90))
    c.blur_all(22)
    bokeh(c, rng, 26, (0, 0, W, 700), [(255, 255, 255), (255, 240, 200)], 25, 70)
    # cone (tip runs off the bottom of the frame, as if held below)
    cone = [(640, 600), (960, 600), (800, 1290)]
    c.grad_fill("poly", cone, [(0, (238, 190, 120)), (0.5, (214, 160, 92)), (1, (170, 118, 62))], vertical=False)
    lay = layer(W, H)
    for k in range(-14, 16):
        x = 640 + k * 34
        lay.line([(x, 600), (x + 420, 1300)], (150, 100, 50), width=4)
        lay.line([(x + 340, 600), (x - 80, 1300)], (150, 100, 50), width=4)
    mask = Image.new("L", lay.img.size, 0)
    ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in cone], fill=255)
    lay.img.putalpha(ImageChops.multiply(lay.img.getchannel("A"), mask))
    c.place(lay, (W / 2, H / 2))
    c.rect((630, 590, 970, 630), fill=(226, 176, 104), r=14)
    # scoops
    for (sx, sy, r, base) in [(800, 530, 185, (246, 160, 180)), (800, 330, 160, (120, 76, 50))]:
        c.soft("ellipse", (sx - r, sy - r * 0.92 + 20, sx + r, sy + r * 0.92 + 20), (0, 0, 0), 60, blur=14)
        c.grad_fill("ellipse", (sx - r, sy - r * 0.92, sx + r, sy + r * 0.92),
                    [(0, lighten(base, 0.25)), (0.6, base), (1, darken(base, 0.2))])
        for k in range(9):
            a = math.pi * (0.1 + 0.8 * k / 8)
            dx, dy = -r * 0.95 * math.cos(a), r * 0.8 * math.sin(a)
            rr = r * rng.uniform(0.16, 0.24)
            c.ellipse((sx + dx - rr, sy + dy - rr * 0.8, sx + dx + rr, sy + dy + rr * 0.9), fill=darken(base, 0.05))
        c.soft("ellipse", (sx - r * 0.6, sy - r * 0.75, sx - r * 0.05, sy - r * 0.35), (255, 255, 255), 110, blur=r * 0.08)
    for _ in range(40):
        a = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(0, 140)
        x, y = 800 + rad * math.cos(a), 320 + rad * 0.85 * math.sin(a)
        ang = rng.uniform(0, math.pi)
        col = rng.choice([(250, 80, 80), (250, 220, 60), (90, 200, 120), (90, 150, 250), (255, 255, 255)])
        c.line([(x, y), (x + 14 * math.cos(ang), y + 14 * math.sin(ang))], col, width=5)
    c.ellipse((775, 120, 825, 170), fill=(200, 20, 40))
    c.soft("ellipse", (785, 128, 800, 143), (255, 255, 255), 160)
    c.line([(805, 125), (830, 80)], (90, 140, 60), width=4)
    return c.result(), {}


def draw_b05(rng):
    c = Canvas(W, H)
    sky(c, 380)
    cloud(c, 380, 140, 1.0)
    sea(c, rng, 380, 600, lines=140)
    sand(c, rng, 600, 1200)
    shore(c, 606)
    c.soft("ellipse", (480, 940, 1220, 1010), (110, 85, 50), 140, blur=14)
    d = layer(W, H)
    coat, coat_dk, coat_lt = (204, 152, 82), (164, 114, 56), (228, 186, 120)
    # far legs
    for x in (628, 1000):
        d.rect((x, 760, x + 52, 958), fill=coat_dk, r=22)
        d.ellipse((x - 6, 935, x + 62, 970), fill=darken(coat_dk, 0.1))
    # tail
    d.line([(560, 690), (500, 640), (455, 560), (450, 505)], coat, width=34)
    # body
    d.ellipse((520, 600, 1060, 850), fill=coat)
    d.ellipse((880, 580, 1100, 840), fill=coat)
    # neck and head
    d.poly([(950, 650), (1030, 500), (1150, 520), (1100, 720)], fill=coat)
    d.ellipse((1020, 410, 1190, 580), fill=coat)
    d.ellipse((1120, 482, 1290, 580), fill=coat)
    d.rect((1150, 482, 1270, 545), fill=coat, r=20)
    # near legs
    for x in (580, 950):
        d.rect((x, 770, x + 58, 960), fill=coat, r=24)
        d.ellipse((x - 8, 938, x + 70, 978), fill=coat_lt)
    # shading
    shade = Image.linear_gradient("L").resize(d.img.size).point(lambda v: 255 - int(v * 0.32))
    rgb = d.img.convert("RGB")
    rgb = ImageChops.multiply(rgb, Image.merge("RGB", [shade, shade, shade]))
    alpha = d.img.getchannel("A")
    d.img = rgb.convert("RGBA")
    d.img.putalpha(alpha)
    d.d = ImageDraw.Draw(d.img)
    d.soft("ellipse", (600, 610, 1000, 700), coat_lt, 120, blur=20)
    # ear, face details, collar
    d.poly([(1050, 440), (1105, 425), (1120, 560), (1075, 610), (1040, 545)], fill=coat_dk)
    d.ellipse((1255, 478, 1300, 515), fill=(30, 22, 20))
    d.soft("ellipse", (1262, 482, 1276, 494), (255, 255, 255), 150)
    d.ellipse((1128, 468, 1156, 494), fill=(45, 30, 20))
    d.ellipse((1136, 472, 1145, 481), fill=(255, 255, 255))
    d.line([(1290, 552), (1240, 562), (1205, 556)], (90, 55, 30), width=4)
    d.poly([(985, 600), (1040, 520), (1072, 535), (1015, 615)], fill=(205, 40, 50))
    d.ellipse((1012, 598, 1040, 626), fill=(230, 190, 60))
    c.place(d, (W / 2, H / 2))
    # tennis ball
    c.soft("ellipse", (1300, 965, 1390, 990), (100, 80, 50), 120, blur=6)
    c.ellipse((1295, 905, 1375, 985), fill=(205, 225, 60))
    c.arc((1300, 890, 1360, 975), 100, 250, (250, 250, 240), width=5)
    return c.result(), {}


def draw_b06(rng):
    c = Canvas(W, H)
    vx, vy = 800, 520
    sky(c, vy)
    sun_glow(c, (300, 110), 55)
    cloud(c, 1100, 160, 1.0)
    cloud(c, 560, 260, 0.6)
    sea(c, rng, vy, 640, x0=820, lines=90)
    sand(c, rng, 640, 1200, x0=800, specks=900)
    shore(c, 640)
    # dunes on the left
    c.vgrad((0, vy, 820, 1200), [(0, (214, 196, 150)), (1, (196, 176, 128))])
    c.poly([(0, vy + 20), (200, vy - 20), (420, vy + 10), (650, vy - 5), (800, vy), (800, 560), (0, 600)],
           fill=(210, 192, 146))
    for _ in range(220):
        gx, gy = rng.uniform(0, 760), rng.uniform(vy, 1200)
        if gx > 140 + (gy - 1200) * -0.92:
            continue
        hgt = rng.uniform(12, 40) * (0.4 + (gy - vy) / 680)
        c.line([(gx, gy), (gx + rng.uniform(-10, 10), gy - hgt)], rng.choice([(110, 140, 70), (140, 160, 80)]), width=2)
    # boardwalk planks
    left = lambda y: 150 + (780 - 150) * (1200 - y) / (1200 - vy)
    right = lambda y: 1450 - (1450 - 820) * (1200 - y) / (1200 - vy)
    c.poly([(150, 1200), (1450, 1200), (820, vy), (780, vy)], fill=(160, 112, 70))
    z = 1.0
    k = 0
    while True:
        ya, yb = vy + 680 / z, vy + 680 / (z + 0.25)
        if ya - yb < 0.8:
            break
        col = [(170, 120, 76), (156, 108, 66), (178, 128, 82)][k % 3]
        c.poly([(left(ya), ya), (right(ya), ya), (right(yb), yb), (left(yb), yb)], fill=col)
        c.line([(left(yb), yb), (right(yb), yb)], (96, 64, 38), width=max(0.6, 3.0 / z))
        z += 0.25
        k += 1
    # railings and lamp posts
    for side, edge in ((-1, left), (1, right)):
        tops = []
        for zz in [1.05, 1.6, 2.3, 3.3, 4.8, 7.0, 10.0, 15.0]:
            y = vy + 680 / zz
            x = edge(y) + side * 8 / zz
            hgt = 260 / zz
            c.rect((x - 9 / zz, y - hgt, x + 9 / zz, y), fill=(120, 84, 52))
            tops.append((x, y - hgt))
        c.line(tops, (138, 98, 62), width=6)
    for zz in [1.4, 3.0, 6.5]:
        y = vy + 680 / zz
        x = right(y) + 30 / zz
        top = y - 620 / zz
        c.line([(x, y), (x, top)], (50, 52, 58), width=10 / zz + 1)
        c.rect((x - 22 / zz, top - 50 / zz, x + 22 / zz, top), fill=(245, 236, 200), outline=(50, 52, 58), width=4 / zz + 0.5)
        c.poly([(x - 30 / zz, top - 50 / zz), (x + 30 / zz, top - 50 / zz), (x, top - 80 / zz)], fill=(50, 52, 58))
    return c.result(), {}


def draw_b07(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, 110), [(0, (120, 172, 222)), (1, (186, 216, 240))])
    c.vgrad((0, 100, W, 1010), [(0, (238, 226, 202)), (1, (224, 208, 180))])
    for _ in range(140):
        x, y, r = rng.uniform(0, W), rng.uniform(140, 1000), rng.uniform(20, 70)
        c.soft("ellipse", (x - r, y - r * 0.6, x + r, y + r * 0.6), (206, 188, 156), 22, blur=12)
    # roof eave with tiles
    c.rect((0, 70, W, 135), fill=(160, 74, 52))
    for x in range(0, W + 40, 44):
        c.ellipse((x - 24, 112, x + 24, 150), fill=(150, 66, 46))
        c.line([(x, 70), (x, 130)], (130, 56, 40), width=2)
    c.soft("rect", (0, 148, W, 190), (90, 70, 50), 90, blur=12)

    def window(b, shutters=False):
        x0, y0, x1, y1 = b
        c.soft("rect", (x0 - 8, y0 - 6, x1 + 22, y1 + 26), (80, 60, 40), 90, blur=10)
        c.rect((x0 - 16, y0 - 16, x1 + 16, y1 + 16), fill=(250, 248, 242))
        c.vgrad((x0, y0, x1, y1), [(0, (128, 168, 196)), (1, (58, 88, 118))])
        c.soft("poly", [(x0 + (x1 - x0) * 0.18, y0), (x0 + (x1 - x0) * 0.42, y0),
                        (x0 + (x1 - x0) * 0.12, y1), (x0 - 1, y1)], (255, 255, 255), 45)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        c.rect((mx - 6, y0, mx + 6, y1), fill=(250, 248, 242))
        c.rect((x0, my - 6, x1, my + 6), fill=(250, 248, 242))
        c.rect((x0 - 30, y1 + 16, x1 + 30, y1 + 38), fill=(232, 226, 214))
        c.soft("rect", (x0 - 30, y1 + 38, x1 + 30, y1 + 52), (90, 70, 50), 70, blur=6)
        if shutters:
            for sx0 in (x0 - 16 - (x1 - x0) / 2 - 10, x1 + 26):
                c.rect((sx0, y0 - 16, sx0 + (x1 - x0) / 2 - 10, y1 + 16), fill=(70, 120, 110))
                for yy in range(int(y0), int(y1), 22):
                    c.line([(sx0 + 8, yy), (sx0 + (x1 - x0) / 2 - 18, yy)], (50, 92, 84), width=3)
        # flower box
        c.rect((x0 - 10, y1 + 52, x1 + 10, y1 + 100), fill=(150, 90, 60))
        for k in range(14):
            fx = x0 + (x1 - x0) * k / 13
            c.ellipse((fx - 16, y1 + 28, fx + 16, y1 + 60), fill=(80, 140, 70))
            c.ellipse((fx - 8, y1 + 30, fx + 8, y1 + 46), fill=rng.choice([(220, 60, 80), (240, 120, 160), (250, 250, 250)]))

    window((235, 380, 455, 700), shutters=True)
    window((640, 380, 960, 700))
    # stone plinth and sidewalk
    c.rect((0, 960, W, 1010), fill=(196, 188, 176))
    c.vgrad((0, 1010, W, H), [(0, (178, 176, 172)), (1, (140, 138, 136))])
    for x in range(-200, W + 200, 160):
        c.line([(x, 1010), (x - 140, H)], (120, 118, 116), width=2)
    for y in (1060, 1125):
        c.line([(0, y), (W, y)], (120, 118, 116), width=2)
    # door
    dx0, dy0, dx1, dy1 = 1140, 500, 1390, 960
    c.soft("rect", (dx0 - 26, dy0 - 26, dx1 + 40, dy1), (80, 60, 40), 90, blur=12)
    c.rect((dx0 - 22, dy0 - 22, dx1 + 22, dy1), fill=(214, 206, 190))
    c.vgrad((dx0, dy0, dx1, dy1), [(0, (46, 98, 78)), (1, (30, 70, 56))])
    for px0, py0, px1, py1 in [(dx0 + 28, dy0 + 30, dx1 - 28, dy0 + 200), (dx0 + 28, dy0 + 240, dx1 - 28, dy1 - 30)]:
        c.rect((px0, py0, px1, py1), outline=(24, 56, 44), width=5)
        c.line([(px0 + 6, py1 - 4), (px1 - 4, py1 - 4), (px1 - 4, py0 + 6)], (70, 130, 104), width=3)
    c.ellipse((dx1 - 48, 730, dx1 - 24, 754), fill=(214, 176, 80))
    c.rect((dx0 - 40, dy1, dx1 + 40, dy1 + 30), fill=(170, 166, 160))
    # wall lamp
    c.rect((1066, 560, 1100, 640), fill=(40, 40, 44), r=6)
    c.rect((1072, 572, 1094, 626), fill=(250, 230, 160))
    # plant pot
    c.poly([(1000, 880), (1090, 880), (1078, 960), (1012, 960)], fill=(180, 92, 60))
    for k in range(9):
        a = math.pi * (0.15 + 0.7 * k / 8)
        c.ellipse((1045 + 70 * math.cos(a) - 22, 860 - 80 * math.sin(a) - 12,
                   1045 + 70 * math.cos(a) + 22, 860 - 80 * math.sin(a) + 12), fill=(70, 130, 64))
    # house number plaque "42" above the door
    pb = (1170, 330, 1360, 450)
    c.soft("rrect", (pb[0] + 6, pb[1] + 8, pb[2] + 10, pb[3] + 12), (60, 40, 20), 110, blur=6, r=16)
    c.rect(pb, fill=(250, 250, 246), r=16)
    c.rect((pb[0] + 8, pb[1] + 8, pb[2] - 8, pb[3] - 8), outline=(30, 60, 140), width=5, r=12)
    c.text(((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2 + 2), "42", 92, (24, 48, 120), anchor="mm")
    # wall-mounted street sign "HARBOR ST"
    sb = (1090, 165, 1550, 275)
    c.soft("rect", (sb[0] + 8, sb[1] + 10, sb[2] + 12, sb[3] + 14), (60, 40, 20), 110, blur=6)
    c.rect(sb, fill=(28, 74, 150), r=10)
    c.rect((sb[0] + 8, sb[1] + 8, sb[2] - 8, sb[3] - 8), outline=(250, 250, 250), width=4, r=6)
    size = c.fit("HARBOR ST", 70, sb[2] - sb[0] - 60)
    c.text(((sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2 + 2), "HARBOR ST", size, (255, 255, 255), anchor="mm")
    for sx, sy in [(sb[0] + 18, sb[1] + 18), (sb[2] - 18, sb[1] + 18), (sb[0] + 18, sb[3] - 18), (sb[2] - 18, sb[3] - 18)]:
        c.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=(200, 200, 205))
    c.specimen_mark()
    return c.result(), {"ADR": union(pb, sb)}


def car_rear(c, cx, ground, s, body=(176, 32, 44), plate_text="EX 482 1C"):
    """Rear view of a small hatchback. s=1 is 880 px wide. Returns the plate box."""
    def X(dx):
        return cx + dx * s

    def Y(dy):
        return ground - dy * s

    c.soft("ellipse", (X(-480), Y(40), X(480), Y(-35)), (0, 0, 0), 150, blur=18 * s)
    for sign in (-1, 1):
        c.rect((X(sign * 390 - 70), Y(150), X(sign * 390 + 70), Y(0)), fill=(24, 24, 27), r=18 * s)
    c.rect((X(-445), Y(190), X(445), Y(80)), fill=(40, 40, 44), r=34 * s)
    c.grad_fill("rrect", (X(-435), Y(490), X(435), Y(130)),
                [(0, lighten(body, 0.22)), (0.45, body), (1, darken(body, 0.35))], r=60 * s)
    c.poly([(X(-335), Y(480)), (X(335), Y(480)), (X(262), Y(670)), (X(-262), Y(670))], fill=darken(body, 0.12))
    c.grad_fill("poly", [(X(-298), Y(492)), (X(298), Y(492)), (X(238), Y(650)), (X(-238), Y(650))],
                [(0, (84, 104, 124)), (1, (30, 40, 55))])
    c.soft("poly", [(X(-150), Y(650)), (X(-70), Y(650)), (X(-180), Y(492)), (X(-260), Y(492))], (255, 255, 255), 40)
    c.rect((X(-255), Y(690), X(255), Y(660)), fill=darken(body, 0.05), r=14 * s)
    for sign in (-1, 1):
        pts = [(X(sign * 428), Y(460)), (X(sign * 255), Y(460)), (X(sign * 255), Y(388)), (X(sign * 418), Y(368))]
        c.grad_fill("poly", pts, [(0, (255, 96, 74)), (1, (150, 12, 22))])
        c.soft("poly", [(X(sign * 405), Y(450)), (X(sign * 280), Y(450)), (X(sign * 280), Y(435)),
                        (X(sign * 400), Y(430))], (255, 225, 205), 150)
    c.line([(X(-300), Y(480)), (X(-300), Y(330)), (X(300), Y(330)), (X(300), Y(480))], darken(body, 0.35), width=2.5 * s)
    c.rect((X(-238), Y(310), X(238), Y(160)), fill=darken(body, 0.5), r=16 * s)
    pb = (X(-212), Y(296), X(212), Y(176))
    c.rect(pb, fill=(248, 248, 244), r=9 * s)
    c.rect((pb[0] + 7 * s, pb[1] + 7 * s, pb[2] - 7 * s, pb[3] - 7 * s), outline=(28, 28, 28), width=5 * s, r=6 * s)
    size = c.fit(plate_text, 86 * s, (pb[2] - pb[0]) - 44 * s, kind="cond")
    c.text(((pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2 + 3 * s), plate_text, size, (18, 18, 20), kind="cond", anchor="mm")
    return pb


def draw_b08(rng):
    c = Canvas(W, H)
    sky(c, 380)
    cloud(c, 300, 120, 0.9)
    cloud(c, 1300, 200, 0.7)
    sea(c, rng, 380, 470, lines=60)
    c.rect((0, 470, W, 545), fill=(196, 190, 178))
    for x in range(0, W, 120):
        c.line([(x, 470), (x, 545)], (170, 164, 152), width=2)
    c.line([(0, 470), (W, 470)], (222, 218, 210), width=6)
    for lx in (180, 1420):
        c.line([(lx, 545), (lx, 260)], (60, 64, 70), width=8)
        c.ellipse((lx - 22, 240, lx + 22, 270), fill=(60, 64, 70))
    c.vgrad((0, 545, W, H), [(0, (122, 122, 128)), (1, (84, 84, 90))])
    c.rect((0, 545, W, 565), fill=(170, 168, 166))
    for y0 in (640, 760, 930):
        c.poly([(1390 + (y0 - 640) * 0.5, y0), (1410 + (y0 - 640) * 0.5, y0),
                (1420 + (y0 - 640) * 0.55, y0 + 60), (1398 + (y0 - 640) * 0.55, y0 + 60)], fill=(232, 232, 228))
    pb = car_rear(c, 800, 1100, 1.0)
    c.specimen_mark()
    return c.result(), {"PLT": pb}


def draw_b09(rng):
    c = Canvas(W, H)
    # striped beach towel seen from above
    th = math.radians(24)
    u, v = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    cols = [(38, 168, 180), (246, 244, 236), (238, 118, 98), (246, 244, 236)]
    L = 3000
    for k in range(-40, 60):
        s0, s1 = k * 70, (k + 1) * 70
        pts = [(u[0] * s0 + v[0] * -L, u[1] * s0 + v[1] * -L), (u[0] * s1 + v[0] * -L, u[1] * s1 + v[1] * -L),
               (u[0] * s1 + v[0] * L, u[1] * s1 + v[1] * L), (u[0] * s0 + v[0] * L, u[1] * s0 + v[1] * L)]
        c.poly(pts, fill=cols[k % 4])
    for _ in range(9):
        y = rng.uniform(0, H)
        c.soft("line", [(-50, y), (W + 50, y + rng.uniform(-200, 200))], (0, 0, 0), 26, width=40, blur=24)
        c.soft("line", [(-50, y + 50), (W + 50, y + rng.uniform(-200, 200))], (255, 255, 255), 22, width=30, blur=20)
    for _ in range(500):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        c.ellipse((x - 1.3, y - 1.3, x + 1.3, y + 1.3), fill=(214, 190, 140))
    # sunglasses
    c.soft("ellipse", (1205, 165, 1505, 265), (0, 0, 0), 70, blur=12)
    for lx in (1210, 1370):
        c.ellipse((lx, 120, lx + 125, 215), fill=(28, 30, 36), outline=(10, 10, 12), width=6)
        c.soft("ellipse", (lx + 18, 132, lx + 60, 160), (255, 255, 255), 60)
    c.arc((1325, 130, 1385, 180), 200, 340, (10, 10, 12), width=7)
    c.line([(1210, 150), (1120, 60)], (10, 10, 12), width=7)
    c.line([(1495, 150), (1580, 70)], (10, 10, 12), width=7)
    # sunscreen bottle (no label text)
    sb = layer(160, 400)
    sb.grad_fill("rrect", (10, 60, 150, 390), [(0, (255, 170, 60)), (0.5, (250, 140, 40)), (1, (210, 100, 20))], vertical=False, r=40)
    sb.rect((40, 10, 120, 70), fill=(250, 250, 250), r=12)
    sb.rect((30, 180, 130, 300), fill=(255, 236, 200), r=14)
    sb.ellipse((60, 205, 100, 245), fill=(250, 190, 60))
    c.place(sb, (220, 980), angle=40, shadow=(10, 14, 10, 110))
    # boarding pass
    bp = layer(1040, 430)
    bp.rect((0, 0, 1040, 430), fill=(251, 249, 243), r=18)
    bp.rect((0, 0, 1040, 92), fill=(26, 64, 122), r=18)
    bp.rect((0, 50, 1040, 92), fill=(26, 64, 122))
    head = "EXEMPLIA AIR · BOARDING PASS"
    bp.text((30, 47), head, bp.fit(head, 40, 720), (255, 255, 255), anchor="lm")
    bp.text((1010, 47), "SPECIMEN", 20, (190, 210, 240), anchor="rm")
    for y in range(100, 430, 18):
        bp.line([(778, y), (778, y + 9)], (150, 150, 150), width=2.5)
    bp.text((30, 112), "PASSENGER", 19, (110, 110, 116), kind="regular")
    bp.text((30, 136), "RIVERA/SAM", 46, (20, 22, 34))
    cols_x = [(30, "FLIGHT", "EX 000"), (230, "GATE", "B4"), (380, "SEAT", "14C"), (540, "BOARDING", "09:40")]
    for x, lab, val in cols_x:
        bp.text((x, 206), lab, 19, (110, 110, 116), kind="regular")
        bp.text((x, 230), val, 38, (20, 22, 34))
    x = 30.0
    bars = rng
    bp.rect((30, 296, 34, 400), fill=(10, 10, 10))
    bp.rect((38, 296, 41, 400), fill=(10, 10, 10))
    x = 46.0
    black = True
    while x < 720:
        wdt = bars.choice([2.6, 2.6, 5.2, 7.8, 10.4])
        if black:
            bp.rect((x, 296, x + wdt, 400), fill=(10, 10, 10))
        x += wdt
        black = not black
    bp.rect((728, 296, 732, 400), fill=(10, 10, 10))
    bp.rect((736, 296, 740, 400), fill=(10, 10, 10))
    bp.text((800, 110), "RIVERA/SAM", 24, (20, 22, 34))
    bp.text((800, 146), "SEAT 14C", 36, (20, 22, 34))
    qx, qy, qs, n = 812, 210, 196, 25
    m = qs / n
    bp.rect((qx - 6, qy - 6, qx + qs + 6, qy + qs + 6), fill=(255, 255, 255))
    for i in range(n):
        for j in range(n):
            finder = (i < 8 and j < 8) or (i < 8 and j >= n - 8) or (i >= n - 8 and j < 8)
            if finder:
                continue
            if bars.random() < 0.5:
                bp.rect((qx + i * m, qy + j * m, qx + (i + 1) * m, qy + (j + 1) * m), fill=(10, 10, 10))
    for fi, fj in [(0, 0), (n - 7, 0), (0, n - 7)]:
        x0, y0 = qx + fi * m, qy + fj * m
        bp.rect((x0, y0, x0 + 7 * m, y0 + 7 * m), fill=(10, 10, 10))
        bp.rect((x0 + m, y0 + m, x0 + 6 * m, y0 + 6 * m), fill=(255, 255, 255))
        bp.rect((x0 + 2 * m, y0 + 2 * m, x0 + 5 * m, y0 + 5 * m), fill=(10, 10, 10))
    box = c.place(bp, (800, 610), angle=4, shadow=(10, 16, 12, 120))
    c.specimen_mark()
    return c.result(), {"TKT": box}


def draw_b10(rng):
    c = Canvas(W, H)
    sky(c, 260)
    cloud(c, 1100, 110, 0.9)
    sea(c, rng, 260, 440, lines=110)
    sand(c, rng, 440, 1200)
    shore(c, 446)
    towel(c, [(760, 720), (1360, 690), (1480, 1010), (820, 1060)],
          [(250, 200, 60), (246, 244, 236), (60, 150, 200), (246, 244, 236)], 9)
    beach_ball(c, 1300, 600, 70)
    for fx, fy in [(940, 1120), (1040, 1110)]:
        c.soft("ellipse", (fx - 40, fy - 70, fx + 46, fy + 76), (100, 80, 50), 90, blur=6)
        c.ellipse((fx - 40, fy - 76, fx + 40, fy + 70), fill=(40, 170, 160))
        c.line([(fx - 25, fy - 30), (fx, fy - 50), (fx + 25, fy - 30)], (250, 250, 250), width=7)
    # backpack
    navy, navy_lt, navy_dk = (38, 58, 112), (54, 80, 142), (26, 40, 80)
    c.soft("ellipse", (130, 950, 640, 1050), (100, 80, 50), 140, blur=16)
    c.arc((270, 222, 400, 352), 190, 350, navy_dk, width=18)
    c.grad_fill("rrect", (150, 290, 520, 1000), [(0, navy_lt), (0.6, navy), (1, navy_dk)], vertical=False, r=130)
    c.line([(185, 470), (250, 330), (420, 330), (485, 470)], (150, 156, 170), width=5)
    c.grad_fill("rrect", (190, 520, 480, 950), [(0, (64, 92, 156)), (1, (40, 62, 120))], vertical=False, r=60)
    c.line([(205, 540), (465, 540)], (150, 156, 170), width=5)
    c.rect((440, 532, 458, 580), fill=(170, 176, 190), r=4)
    # school crest patch
    pb = (222, 568, 450, 800)
    c.soft("rrect", (pb[0] + 3, pb[1] + 5, pb[2] + 5, pb[3] + 7), (0, 0, 0), 90, blur=4, r=18)
    c.rect(pb, fill=(248, 246, 238), r=18)
    c.rect((pb[0] + 6, pb[1] + 6, pb[2] - 6, pb[3] - 6), outline=(28, 46, 100), width=4, r=14)
    sx = (pb[0] + pb[2]) / 2
    c.poly([(sx - 44, 586), (sx + 44, 586), (sx + 44, 640), (sx, 676), (sx - 44, 640)], fill=(190, 40, 52))
    c.line([(sx - 30, 626), (sx - 15, 614), (sx, 626), (sx + 15, 614), (sx + 30, 626)], (250, 210, 70), width=6)
    c.poly([(sx - 18, 598), (sx + 18, 598), (sx + 18, 606), (sx - 18, 606)], fill=(250, 210, 70))
    s1 = c.fit("LAKESIDE", 40, pb[2] - pb[0] - 26)
    c.text((sx, 712), "LAKESIDE", s1, (28, 46, 100), anchor="mm")
    c.text((sx, 758), "PRIMARY", s1, (28, 46, 100), anchor="mm")
    # name tag hanging from the handle
    c.line([(292, 300), (262, 336), (238, 362)], (30, 30, 34), width=5)
    tb = (130, 356, 330, 470)
    c.soft("rrect", (tb[0] + 4, tb[1] + 6, tb[2] + 6, tb[3] + 8), (0, 0, 0), 90, blur=4, r=14)
    c.rect(tb, fill=(226, 232, 238), r=14)
    c.rect((tb[0] + 10, tb[1] + 18, tb[2] - 10, tb[3] - 10), fill=(255, 255, 255), r=6)
    c.ellipse((226, 362, 242, 376), fill=(120, 126, 140))
    s2 = c.fit("MIA R.", 50, tb[2] - tb[0] - 36)
    c.text(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2 + 8), "MIA R.", s2, (20, 22, 34), anchor="mm")
    c.specimen_mark()
    return c.result(), {"SCH": union(pb, tb)}


def draw_b11(rng):
    c = Canvas(W, H)
    sky(c, 820, top=(110, 168, 222), low=(206, 230, 246))
    cloud(c, 300, 200, 1.1)
    cloud(c, 1250, 330, 0.8)
    sea(c, rng, 820, 1200, lines=160)
    for bx, by, s in [(330, 450, 1.0), (430, 400, 0.7)]:
        c.line([(bx - 40 * s, by - 6 * s), (bx - 14 * s, by - 16 * s), (bx, by), (bx + 14 * s, by - 16 * s), (bx + 40 * s, by - 6 * s)],
               (70, 74, 82), width=4 * s)
    # wooden post
    c.grad_fill("rect", (720, 760, 880, 1200), [(0, (90, 64, 40)), (0.45, (150, 112, 74)), (1, (80, 56, 34))], vertical=False)
    for y in range(800, 1200, 70):
        c.soft("line", [(722, y), (878, y + 8)], (70, 48, 30), 90, width=3)
    c.ellipse((720, 740, 880, 782), fill=(170, 132, 92))
    c.ellipse((760, 750, 840, 772), outline=(140, 104, 70), width=2)
    # seagull facing right
    g = layer(W, H)
    g.line([(790, 690), (784, 756)], (232, 150, 100), width=9)
    g.line([(830, 690), (836, 756)], (232, 150, 100), width=9)
    g.poly([(764, 752), (804, 752), (784, 760)], fill=(232, 150, 100))
    g.poly([(816, 752), (856, 752), (836, 760)], fill=(232, 150, 100))
    g.poly([(660, 590), (556, 628), (566, 662), (668, 652)], fill=(244, 244, 244))
    g.ellipse((636, 520, 926, 712), fill=(246, 246, 246))
    g.ellipse((820, 456, 940, 640), fill=(246, 246, 246))
    g.ellipse((846, 402, 990, 532), fill=(248, 248, 248))
    g.soft("ellipse", (660, 640, 900, 712), (205, 210, 216), 150, blur=10)
    g.poly([(676, 556), (880, 552), (862, 640), (700, 676), (568, 650)], fill=(146, 158, 172))
    for k in range(4):
        g.line([(700 + k * 40, 600 + k * 4), (640 + k * 40, 648)], (120, 130, 144), width=3)
    g.poly([(606, 628), (704, 660), (556, 676), (536, 652)], fill=(28, 30, 34))
    for wx in (572, 604):
        g.ellipse((wx - 6, 656, wx + 6, 668), fill=(240, 240, 240))
    g.poly([(976, 470), (1066, 482), (1072, 494), (1046, 506), (978, 502)], fill=(246, 200, 64))
    g.ellipse((1036, 490, 1050, 504), fill=(214, 50, 40))
    g.ellipse((932, 448, 954, 470), fill=(246, 210, 90))
    g.ellipse((938, 454, 949, 465), fill=(12, 12, 12))
    c.place(g, (W / 2, H / 2), shadow=(14, 10, 10, 60))
    return c.result(), {}


def car_side(c, x, ground, length, color, facing=1):
    h = length * 0.3
    c.soft("ellipse", (x - 10, ground - 12, x + length + 10, ground + 14), (0, 0, 0), 120, blur=8)
    c.grad_fill("rrect", (x, ground - h * 0.95, x + length, ground - h * 0.22),
                [(0, lighten(color, 0.2)), (1, darken(color, 0.25))], r=h * 0.25)
    cab = [(x + length * 0.2, ground - h * 0.9), (x + length * 0.32, ground - h * 1.45),
           (x + length * 0.7, ground - h * 1.45), (x + length * 0.84, ground - h * 0.9)]
    c.poly(cab, fill=darken(color, 0.08))
    c.poly([(x + length * 0.25, ground - h * 0.95), (x + length * 0.34, ground - h * 1.36),
            (x + length * 0.5, ground - h * 1.36), (x + length * 0.5, ground - h * 0.95)], fill=(70, 92, 116))
    c.poly([(x + length * 0.53, ground - h * 0.95), (x + length * 0.53, ground - h * 1.36),
            (x + length * 0.68, ground - h * 1.36), (x + length * 0.78, ground - h * 0.95)], fill=(70, 92, 116))
    for wx in (x + length * 0.2, x + length * 0.8):
        r = h * 0.3
        c.ellipse((wx - r, ground - 2 * r, wx + r, ground), fill=(26, 26, 28))
        c.ellipse((wx - r * 0.5, ground - 1.5 * r, wx + r * 0.5, ground - 0.5 * r), fill=(170, 172, 178))
    fx = x + length - 14 if facing > 0 else x + 2
    c.rect((fx, ground - h * 0.8, fx + 12, ground - h * 0.62), fill=(250, 240, 200))


def palm(c, x, ground, hgt):
    c.line([(x, ground), (x + hgt * 0.06, ground - hgt * 0.5), (x + hgt * 0.02, ground - hgt)], (120, 90, 60), width=hgt * 0.04)
    top = (x + hgt * 0.02, ground - hgt)
    for a in range(0, 360, 40):
        ang = math.radians(a)
        tip = (top[0] + hgt * 0.38 * math.cos(ang), top[1] + hgt * 0.16 * math.sin(ang) + hgt * 0.1)
        mid = (top[0] + hgt * 0.2 * math.cos(ang), top[1] - hgt * 0.06 + hgt * 0.05 * math.sin(ang))
        c.line([top, mid, tip], (50, 120, 60), width=hgt * 0.035)


def draw_b12(rng):
    c = Canvas(W, H)
    sky(c, 330)
    cloud(c, 1050, 120, 0.9)
    sea(c, rng, 330, 430, lines=60)
    c.rect((0, 430, W, 470), fill=(200, 194, 182))
    for px in (120, 520, 1180, 1500):
        palm(c, px, 470, 230)
    c.vgrad((0, 470, W, H), [(0, (116, 116, 122)), (1, (76, 76, 82))])
    for k in range(-2, 14):
        xb = 120 * k
        c.line([(xb + 40, 520), (xb - 30, 690)], (226, 226, 222), width=4)
    for k in range(-2, 10):
        xb = 220 * k
        c.line([(xb + 60, 760), (xb - 80, 1200)], (226, 226, 222), width=7)
    cars = [(180, 650, 300, (60, 110, 180), 1), (560, 655, 320, (230, 230, 228), -1),
            (950, 650, 300, (40, 40, 44), 1), (1300, 655, 310, (200, 160, 40), -1)]
    for x, g, ln, col, f in cars:
        car_side(c, x, g, ln, col, f)
    # out-of-focus car at the bottom left with a small, blurred plate
    pb = car_rear(c, 300, 1035, 0.36, body=(90, 120, 96), plate_text="EX 731 4B")
    c.blur_region((120, 760, 480, 1060), 3.0, feather=12)
    c.blur_region((pb[0] - 2, pb[1] - 2, pb[2] + 2, pb[3] + 2), 5.0, feather=3)
    c.specimen_mark()
    return c.result(), {"PLT": pb}


# --------------------------------------------------------------------------------------------
# Hazard set
# --------------------------------------------------------------------------------------------

def draw_h01(rng):
    c = Canvas(W, H)
    wood(c, rng, (0, 0, W, H), plank=300)
    # coffee mug from above, pen
    c.soft("ellipse", (1260, 60, 1560, 360), (0, 0, 0), 90, blur=16)
    c.ellipse((1250, 50, 1540, 340), fill=(240, 240, 236))
    c.ellipse((1285, 85, 1505, 305), fill=(96, 58, 34))
    c.soft("ellipse", (1320, 110, 1440, 190), (180, 130, 90), 120, blur=10)
    c.rect((1530, 170, 1600, 220), fill=(240, 240, 236), r=20)
    pen = layer(560, 40)
    pen.rect((0, 6, 520, 34), fill=(30, 60, 140), r=14)
    pen.poly([(520, 8), (560, 20), (520, 32)], fill=(200, 200, 205))
    pen.rect((30, 0, 200, 8), fill=(200, 200, 205), r=3)
    c.place(pen, (1340, 980), angle=70, shadow=(8, 10, 6, 120))
    card = layer(900, 568)
    card.grad_fill("rrect", (0, 0, 900, 568), [(0, (212, 236, 232)), (0.5, (230, 242, 226)), (1, (236, 232, 214))],
                   vertical=False, r=34)
    for k in range(14):
        pts = [(x, 140 + k * 30 + 14 * math.sin(x / 40 + k)) for x in range(0, 901, 15)]
        card.line(pts, (180, 214, 206), width=1.5)
    card.rect((0, 0, 900, 104), fill=(30, 92, 96), r=34)
    card.rect((0, 60, 900, 104), fill=(30, 92, 96))
    t1 = "REPUBLIC OF EXEMPLIA"
    card.text((36, 52), t1, card.fit(t1, 46, 700), (255, 255, 255), anchor="lm")
    card.ellipse((790, 18, 862, 90), outline=(240, 220, 140), width=4)
    star = [(826 + 26 * math.cos(math.radians(-90 + 72 * i * 2)), 54 + 26 * math.sin(math.radians(-90 + 72 * i * 2)))
            for i in range(5)]
    card.poly(star, fill=(240, 220, 140))
    card.text((36, 126), "IDENTITY CARD", 36, (30, 92, 96))
    card.rect((36, 182, 270, 482), fill=(206, 214, 214), r=10)
    card.ellipse((103, 222, 203, 332), fill=(150, 160, 162))
    card.chord((63, 330, 243, 520), 180, 360, (150, 160, 162))
    card.rect((36, 470, 270, 482), fill=(206, 214, 214))
    fields = [("SURNAME", "RIVERA"), ("GIVEN NAMES", "SAM"), ("DATE OF BIRTH", "01 JAN 2000"), ("DOCUMENT NO.", "X00000000")]
    for i, (lab, val) in enumerate(fields):
        y = 188 + i * 74
        card.text((300, y), lab, 19, (80, 96, 98), kind="regular")
        card.text((300, y + 22), val, 36, (20, 26, 30))
    card.line([(60, 520), (90, 500), (120, 528), (150, 498), (190, 522), (230, 506)], (40, 50, 110), width=3)
    stamp = layer(300, 90)
    stamp.rect((4, 4, 296, 86), outline=(200, 30, 40), width=6, r=8)
    stamp.text((150, 46), "SPECIMEN", 46, (200, 30, 40), anchor="mm")
    card.place(stamp, (720, 480), angle=12)
    box = c.place(card, (760, 620), angle=-5, shadow=(12, 18, 14, 130))
    c.specimen_mark()
    return c.result(), {"IDD": box}


def draw_h02(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, H), [(0, (226, 224, 220)), (1, (198, 196, 192))])
    for _ in range(26):
        y = rng.uniform(0, H)
        c.soft("line", [(-50, y), (W + 50, y + rng.uniform(-300, 300))], (255, 255, 255), 60, width=rng.uniform(4, 20), blur=8)
    # coffee cup and saucer from above
    cx, cy = 1230, 560
    c.soft("ellipse", (cx - 230, cy - 210, cx + 250, cy + 250), (0, 0, 0), 80, blur=18)
    c.ellipse((cx - 240, cy - 240, cx + 240, cy + 240), fill=(250, 250, 248))
    c.ellipse((cx - 200, cy - 200, cx + 200, cy + 200), outline=(225, 225, 222), width=4)
    c.rect((cx + 140, cy - 34, cx + 300, cy + 34), fill=(245, 245, 243), r=30)
    c.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), fill=(246, 246, 244))
    c.ellipse((cx - 125, cy - 125, cx + 125, cy + 125), fill=(110, 66, 38))
    c.soft("ellipse", (cx - 110, cy - 110, cx + 110, cy + 110), (196, 150, 104), 140, blur=8)
    c.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=(150, 98, 60))
    sp = layer(60, 380)
    sp.ellipse((5, 0, 55, 80), fill=(200, 202, 208))
    sp.rect((24, 70, 36, 380), fill=(200, 202, 208), r=6)
    c.place(sp, (980, 900), angle=-30, shadow=(6, 8, 5, 110))
    card = layer(856, 540)
    card.grad_fill("rrect", (0, 0, 856, 540), [(0, (18, 40, 92)), (1, (44, 98, 160))], vertical=False, r=34)
    card.soft("ellipse", (380, -200, 1100, 560), (255, 255, 255), 30)
    card.soft("ellipse", (520, 160, 1200, 900), (255, 255, 255), 22)
    card.text((48, 58), "EXEMPLIA BANK", 46, (255, 255, 255))
    card.text((808, 62), "DEBIT", 36, (220, 230, 250), anchor="ra")
    card.grad_fill("rrect", (66, 190, 196, 286), [(0, (240, 214, 140)), (1, (196, 160, 80))], r=14)
    for yy in (222, 254):
        card.line([(66, yy), (196, yy)], (150, 120, 60), width=2)
    card.line([(131, 190), (131, 286)], (150, 120, 60), width=2)
    num = "0000 0000 0000 0000"
    card.text((52, 340), num, card.fit(num, 60, 750, kind="mono"), (248, 248, 250), kind="mono", stroke=0.6, stroke_fill=(200, 210, 230))
    card.text((52, 432), "VALID THRU 00/00", 22, (210, 220, 240), kind="regular")
    card.text((52, 466), "SPECIMEN", 32, (248, 248, 250))
    box = c.place(card, (500, 610), angle=8, shadow=(12, 18, 14, 130))
    c.specimen_mark()
    return c.result(), {"PAY": box}


def draw_h03(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, 360), [(0, (226, 222, 214)), (1, (210, 204, 194))])
    c.rect((0, 340, W, 372), fill=(244, 242, 238))
    c.vgrad((0, 372, W, H), [(0, (176, 168, 156)), (1, (150, 142, 130))])
    for y in range(372, H, 120):
        c.line([(0, y), (W, y)], (130, 122, 112), width=2)
    for x in range(-400, W + 400, 200):
        c.line([(x, 372), (x - 300, H)], (130, 122, 112), width=2)
    # doormat
    c.poly([(240, 980), (1340, 980), (1420, 1150), (160, 1150)], fill=(90, 66, 50))
    # box
    c.soft("poly", [(400, 1000), (1200, 1000), (1350, 860), (1360, 1050), (420, 1070)], (0, 0, 0), 120, blur=18)
    front = [(420, 430), (1180, 430), (1180, 1010), (420, 1010)]
    top = [(420, 430), (1180, 430), (1300, 300), (540, 300)]
    side = [(1180, 430), (1300, 300), (1300, 860), (1180, 1010)]
    c.grad_fill("poly", front, [(0, (204, 158, 104)), (1, (184, 138, 88))])
    c.poly(top, fill=(222, 180, 126))
    c.poly(side, fill=(160, 118, 72))
    c.poly([(780, 430), (820, 430), (940, 300), (900, 300)], fill=(196, 160, 110))
    c.rect((780, 430, 820, 500), fill=(196, 160, 110))
    for _ in range(30):
        x, y = rng.uniform(430, 1170), rng.uniform(440, 1000)
        c.soft("line", [(x, y), (x + rng.uniform(20, 60), y)], (170, 126, 80), 60, width=1.5)
    # shipping label
    lb = (470, 520, 1130, 900)
    c.soft("rect", (lb[0] + 6, lb[1] + 8, lb[2] + 8, lb[3] + 10), (0, 0, 0), 80, blur=6)
    c.rect(lb, fill=(252, 252, 250))
    c.rect((lb[0], lb[1], lb[2], lb[1] + 64), fill=(24, 24, 28))
    c.text((lb[0] + 28, lb[1] + 32), "PARCEL", 34, (255, 255, 255), anchor="lm")
    c.text((lb[2] - 28, lb[1] + 32), "SPECIMEN", 22, (200, 200, 205), anchor="rm")
    lines = [("TO:", 34), ("SAM RIVERA", 60), ("42 HARBOR ST", 60), ("LAKESIDE, EXEMPLIA", 56)]
    y = lb[1] + 96
    for txt, sz in lines:
        sz = c.fit(txt, sz, lb[2] - lb[0] - 60)
        bb = c.text((lb[0] + 30, y), txt, sz, (16, 16, 20))
        y = bb[3] + 22
    c.line([(lb[0] + 30, lb[3] - 34), (lb[2] - 30, lb[3] - 34)], (120, 120, 120), width=2)
    c.specimen_mark()
    return c.result(), {"MAL": lb}


def draw_h04(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, 760), [(0, (222, 218, 210)), (1, (200, 194, 184))])
    wood(c, rng, (0, 760, W, H), base=(186, 150, 110), dark=(150, 116, 80), light=(206, 174, 134), lines=80)
    # plant
    c.poly([(1340, 620), (1460, 620), (1440, 770), (1360, 770)], fill=(240, 240, 236))
    for k in range(11):
        a = math.pi * (0.1 + 0.8 * k / 10)
        c.line([(1400, 630), (1400 + 120 * math.cos(a), 600 - 180 * math.sin(a))], (60, 130, 70), width=14)
    # mug
    c.rect((150, 600, 290, 780), fill=(70, 120, 170), r=12)
    c.arc((260, 640, 340, 730), 270, 90, (70, 120, 170), width=14)
    # laptop
    c.soft("poly", [(230, 860), (1370, 860), (1300, 900), (300, 900)], (0, 0, 0), 120, blur=14)
    c.grad_fill("poly", [(330, 720), (1270, 720), (1370, 860), (230, 860)], [(0, (206, 208, 214)), (1, (170, 172, 180))])
    for r in range(4):
        y0 = 730 + r * 26
        inset = (r * 26 + 10) * (100 / 140)
        x0, x1 = 360 - inset * 0.9, 1240 + inset * 0.9
        for k in range(14):
            kx0 = x0 + (x1 - x0) * k / 14
            c.rect((kx0 + 3, y0 + 3, kx0 + (x1 - x0) / 14 - 3, y0 + 21), fill=(60, 62, 70), r=3)
    c.rect((680, 838, 920, 856), fill=(186, 188, 196), r=4)
    c.rect((390, 150, 1210, 724), fill=(34, 36, 42), r=26)
    sx0, sy0, sx1, sy1 = 420, 182, 1180, 692
    c.rect((sx0, sy0, sx1, sy1), fill=(248, 249, 251))
    # chat app UI (generic)
    c.rect((sx0, sy0, sx0 + 210, sy1), fill=(236, 239, 244))
    for i, (nm, col) in enumerate([("Mia", (230, 110, 120)), ("Alex", (90, 160, 220)), ("Grandma", (120, 190, 120)), ("Jordan", (200, 160, 80))]):
        y = sy0 + 30 + i * 86
        if i == 0:
            c.rect((sx0, y - 14, sx0 + 210, y + 66), fill=(214, 224, 240))
        c.ellipse((sx0 + 16, y, sx0 + 68, y + 52), fill=col)
        c.text((sx0 + 42, y + 26), nm[0], 26, (255, 255, 255), anchor="mm")
        c.text((sx0 + 80, y + 4), nm, 22, (30, 34, 44))
        c.text((sx0 + 80, y + 32), "message", 16, (120, 126, 140), kind="regular")
    hx0 = sx0 + 210
    c.rect((hx0, sy0, sx1, sy0 + 62), fill=(255, 255, 255))
    c.line([(hx0, sy0 + 62), (sx1, sy0 + 62)], (220, 224, 230), width=2)
    c.ellipse((hx0 + 18, sy0 + 10, hx0 + 60, sy0 + 52), fill=(230, 110, 120))
    c.text((hx0 + 39, sy0 + 31), "M", 22, (255, 255, 255), anchor="mm")
    c.text((hx0 + 74, sy0 + 12), "Mia", 26, (30, 34, 44))
    c.text((hx0 + 132, sy0 + 20), "online", 17, (60, 160, 90), kind="regular")
    msgs = [(0, "Hi Sam! Are we still on for Saturday?"), (1, "Yes! Beach at 10, bring the umbrella"),
            (0, "Great, I will pick you up at home"), (1, "See you then!")]
    y = sy0 + 86
    for side, txt in msgs:
        size = 22
        tw = c.text_width(txt, size, kind="regular")
        bw = tw + 36
        if side == 0:
            bx0 = hx0 + 20
            fill, tc = (232, 234, 240), (24, 26, 34)
        else:
            bx0 = sx1 - 20 - bw
            fill, tc = (46, 120, 230), (255, 255, 255)
        c.rect((bx0, y, bx0 + bw, y + 56), fill=fill, r=22)
        c.text((bx0 + 18, y + 28), txt, size, tc, kind="regular", anchor="lm")
        y += 78
    c.rect((hx0 + 16, sy1 - 62, sx1 - 16, sy1 - 14), fill=(255, 255, 255), outline=(210, 214, 222), width=2, r=22)
    c.text((hx0 + 40, sy1 - 38), "Type a message", 19, (150, 154, 164), kind="regular", anchor="lm")
    c.soft("poly", [(sx0, sy0), (sx0 + 300, sy0), (sx0 + 80, sy1), (sx0, sy1)], (255, 255, 255), 18)
    c.specimen_mark()
    return c.result(), {"SCR": (sx0, sy0, sx1, sy1)}


def draw_h05(rng):
    c = Canvas(W, H)
    c.vgrad((0, 0, W, H), [(0, (236, 236, 234)), (1, (214, 214, 210))])
    # router (generic, no brand)
    c.soft("rrect", (130, 560, 700, 760), (0, 0, 0), 110, blur=16, r=30)
    c.grad_fill("rrect", (120, 520, 680, 720), [(0, (60, 62, 68)), (1, (26, 28, 32))], r=30)
    for ax in (190, 610):
        c.line([(ax, 540), (ax + (ax - 400) * 0.25, 180)], (30, 32, 36), width=26)
    for k in range(5):
        c.ellipse((250 + k * 60, 670, 266 + k * 60, 686), fill=(80, 230, 120) if k < 4 else (250, 180, 60))
    c.line([(680, 640), (760, 660), (820, 760), (900, 1200)], (40, 40, 44), width=10)
    # pen
    pen = layer(460, 36)
    pen.rect((0, 4, 420, 32), fill=(30, 30, 34), r=12)
    pen.poly([(420, 6), (460, 18), (420, 30)], fill=(200, 200, 205))
    c.place(pen, (620, 1000), angle=-20, shadow=(6, 8, 5, 110))
    # sticky note
    note = layer(470, 470)
    note.grad_fill("rect", (0, 0, 470, 470), [(0, (255, 240, 120)), (1, (250, 224, 90))])
    note.rect((0, 0, 470, 60), fill=(246, 226, 100))
    ink = (24, 34, 110)
    rows = [("WIFI:", 52), ("RiveraHome", 58), ("KEY:", 52), ("sunflower-42", 58)]
    y = 82
    for txt, sz in rows:
        sz = note.fit(txt, sz, 420, kind="hand")
        bb = note.text((32, y), txt, sz, ink, kind="hand")
        y = bb[3] + 18
    box = c.place(note, (1150, 590), angle=-6, shadow=(10, 16, 14, 120))
    c.specimen_mark()
    return c.result(), {"COD": box}


def key_layer(color, length=440, teeth_seed=1, house=True):
    rng = random.Random(teeth_seed)
    L = layer(length + 20, 160)
    hi, dk = lighten(color, 0.45), darken(color, 0.3)
    if house:
        L.grad_fill("ellipse", (4, 10, 144, 150), [(0, hi), (0.5, color), (1, dk)])
        L.ellipse((26, 62, 62, 98), fill=(0, 0, 0, 0))
        L.d.ellipse([26 * SS, 62 * SS, 62 * SS, 98 * SS], fill=(0, 0, 0, 0))
        L.rect((136, 62, 170, 98), fill=color)
        L.grad_fill("rect", (160, 58, length - 16, 92), [(0, hi), (0.5, color), (1, dk)])
        pts = [(170, 92)]
        x = 170
        while x < length - 50:
            x += rng.uniform(16, 26)
            pts.append((x, 92 + rng.uniform(10, 26)))
            x += rng.uniform(8, 14)
            pts.append((x, 92 + rng.uniform(2, 8)))
        pts += [(length - 30, 104), (length - 16, 92)]
        L.poly(pts + [(length - 16, 92)], fill=color)
        L.poly([(length - 16, 58), (length + 10, 76), (length - 16, 92)], fill=color)
        L.line([(180, 72), (length - 30, 72)], dk, width=3)
    return L


def draw_h06(rng):
    c = Canvas(W, H)
    wood(c, rng, (0, 0, W, H), base=(122, 84, 56), dark=(92, 62, 40), light=(150, 108, 74), plank=260)
    ring = (660, 560)
    # car key fob (generic, no logo)
    fob = layer(170, 300)
    fob.grad_fill("rrect", (10, 40, 160, 290), [(0, (70, 72, 78)), (1, (20, 20, 24))], vertical=False, r=60)
    fob.rect((60, 0, 110, 60), fill=(150, 152, 158), r=14)
    fob.ellipse((70, 10, 100, 40), fill=(0, 0, 0, 0))
    fob.d.ellipse([70 * SS, 10 * SS, 100 * SS, 40 * SS], fill=(0, 0, 0, 0))
    for k, y in enumerate((100, 170, 236)):
        fob.ellipse((55, y - 26, 115, y + 26), fill=(46, 48, 54), outline=(110, 112, 120), width=2)
    fob.poly([(85, 82), (101, 108), (69, 108)], fill=(170, 172, 180))
    fob.rect((70, 160, 100, 180), outline=(170, 172, 180), width=3, r=3)
    fob.ellipse((76, 226, 94, 244), fill=(170, 172, 180))
    boxes = [c.place(fob, (ring[0] - 140, ring[1] + 200), angle=28, shadow=(12, 16, 10, 140))]
    keys = [((198, 166, 82), -12, 3), ((190, 194, 200), 22, 7), ((176, 180, 188), 58, 11)]
    for col, ang, seed in keys:
        k = key_layer(col, teeth_seed=seed)
        big = layer(1000, 1000)
        big.img.paste(k.img, (int((500 - 74) * SS), int((500 - 80) * SS)), k.img)
        rot = big.img.rotate(-ang, resample=Image.BICUBIC, center=(500 * SS, 500 * SS))
        boxes.append(c.place(rot, (ring[0] + 74 * math.cos(math.radians(ang)), ring[1] + 74 * math.sin(math.radians(ang))),
                             shadow=(12, 16, 10, 140)))
    c.ellipse((ring[0] - 64, ring[1] - 64, ring[0] + 64, ring[1] + 64), outline=(200, 204, 210), width=9)
    c.arc((ring[0] - 64, ring[1] - 64, ring[0] + 64, ring[1] + 64), 200, 300, (250, 250, 252), width=4)
    c.specimen_mark()
    return c.result(), {"KEY": union(*boxes)}


def draw_h07(rng):
    c = Canvas(W, H)
    c.rect((0, 0, W, 700), fill=(236, 238, 238))
    for x in range(0, W, 200):
        c.line([(x, 0), (x, 700)], (206, 210, 212), width=3)
    for y in range(0, 700, 200):
        c.line([(0, y), (W, y)], (206, 210, 212), width=3)
    c.vgrad((0, 700, W, H), [(0, (246, 246, 244)), (1, (220, 220, 218))])
    for _ in range(30):
        y = rng.uniform(700, H)
        c.soft("line", [(-50, y), (W + 50, y + rng.uniform(-80, 80))], (200, 200, 200), 50, width=rng.uniform(2, 8), blur=4)
    # pills
    for px, py, a in [(1170, 1030, 20), (1250, 1080, -15), (1120, 1110, 60)]:
        p = layer(90, 50)
        p.ellipse((2, 2, 88, 48), fill=(252, 252, 252), outline=(214, 214, 214), width=2)
        p.line([(45, 6), (45, 44)], (210, 210, 210), width=2)
        c.place(p, (px, py), angle=a, shadow=(4, 6, 4, 90))
    # amber bottle
    bx0, bx1, by0, by1 = 520, 1080, 330, 1020
    c.soft("ellipse", (bx0 - 20, by1 - 40, bx1 + 120, by1 + 50), (0, 0, 0), 110, blur=18)
    c.grad_fill("rrect", (bx0, by0, bx1, by1),
                [(0, (120, 54, 10)), (0.22, (214, 120, 40)), (0.4, (236, 150, 60)), (0.75, (190, 96, 24)), (1, (110, 48, 8))],
                vertical=False, r=40)
    c.soft("rect", (bx0 + 70, by0 + 30, bx0 + 110, by1 - 40), (255, 236, 200), 90, blur=6)
    c.grad_fill("rrect", (bx0 - 20, 210, bx1 + 20, 350),
                [(0, (206, 206, 204)), (0.35, (252, 252, 250)), (1, (196, 196, 194))], vertical=False, r=18)
    for x in range(bx0 - 10, bx1 + 20, 18):
        c.line([(x, 222), (x, 338)], (214, 214, 212), width=3)
    c.ellipse((bx0 - 20, 196, bx1 + 20, 228), fill=(246, 246, 244))
    # label
    lb = (bx0 + 30, 470, bx1 - 30, 900)
    c.grad_fill("rect", lb, [(0, (214, 214, 210)), (0.2, (252, 252, 250)), (0.8, (250, 250, 248)), (1, (206, 206, 202))],
                vertical=False)
    c.rect((lb[0], lb[1], lb[2], lb[1] + 58), fill=(32, 110, 120))
    c.text(((lb[0] + lb[2]) / 2, lb[1] + 29), "LAKESIDE PHARMACY", c.fit("LAKESIDE PHARMACY", 30, lb[2] - lb[0] - 50),
           (255, 255, 255), anchor="mm")
    rows = [("RX 0000", 44, "bold"), ("SAM RIVERA", 46, "bold"), ("LISINOPRIL 10 MG", 46, "bold"),
            ("TAKE 1 TABLET DAILY", 30, "regular"), ("QTY 30 · SPECIMEN", 26, "regular")]
    y = lb[1] + 80
    for txt, sz, kind in rows:
        sz = c.fit(txt, sz, lb[2] - lb[0] - 70, kind=kind)
        bb = c.text((lb[0] + 36, y), txt, sz, (20, 22, 28), kind=kind)
        y = bb[3] + 20
    c.specimen_mark()
    return c.result(), {"MED": lb}


def face(c, cx, cy, s, skin, hair, hair_style, eyes, shirt, lips=(176, 76, 80)):
    sk_dk, sk_lt = darken(skin, 0.18), lighten(skin, 0.12)
    if hair_style == "long":
        c.rect((cx - 140 * s, cy - 110 * s, cx + 140 * s, cy + 250 * s), fill=darken(hair, 0.1), r=90 * s)
    # torso and neck
    c.grad_fill("rrect", (cx - 200 * s, cy + 175 * s, cx + 200 * s, cy + 560 * s),
                [(0, lighten(shirt, 0.15)), (1, darken(shirt, 0.2))], vertical=False, r=120 * s)
    c.rect((cx - 48 * s, cy + 100 * s, cx + 48 * s, cy + 200 * s), fill=sk_dk)
    c.chord((cx - 60 * s, cy + 120 * s, cx + 60 * s, cy + 240 * s), 0, 180, sk_dk)
    # ears and head
    for sgn in (-1, 1):
        c.ellipse((cx + sgn * 112 * s - 22 * s, cy - 30 * s, cx + sgn * 112 * s + 22 * s, cy + 40 * s), fill=sk_dk)
    c.grad_fill("ellipse", (cx - 112 * s, cy - 145 * s, cx + 112 * s, cy + 150 * s),
                [(0, sk_lt), (0.55, skin), (1, sk_dk)], vertical=False)
    # hair
    if hair_style == "curly":
        for k in range(16):
            a = math.pi * (1.0 + k / 15)
            hx, hy = cx + 112 * s * math.cos(a), cy - 70 * s + 95 * s * math.sin(a)
            c.ellipse((hx - 42 * s, hy - 42 * s, hx + 42 * s, hy + 42 * s), fill=hair)
        c.ellipse((cx - 100 * s, cy - 175 * s, cx + 100 * s, cy - 70 * s), fill=hair)
    else:
        c.chord((cx - 122 * s, cy - 175 * s, cx + 122 * s, cy + 15 * s), 180, 360, hair)
        c.poly([(cx - 122 * s, cy - 80 * s), (cx + 122 * s, cy - 80 * s), (cx + 112 * s, cy - 40 * s),
                (cx + 30 * s, cy - 78 * s), (cx - 112 * s, cy - 40 * s)], fill=hair)
    # cheeks
    for sgn in (-1, 1):
        c.soft("ellipse", (cx + sgn * 62 * s - 26 * s, cy + 28 * s, cx + sgn * 62 * s + 26 * s, cy + 58 * s),
               (230, 120, 120), 55, blur=8 * s)
    # eyes and brows
    for sgn in (-1, 1):
        ex, ey = cx + sgn * 44 * s, cy - 14 * s
        c.line([(ex - 26 * s, ey - 34 * s), (ex, ey - 42 * s), (ex + 26 * s, ey - 36 * s)], darken(hair, 0.2), width=8 * s)
        c.ellipse((ex - 24 * s, ey - 13 * s, ex + 24 * s, ey + 13 * s), fill=(252, 252, 252))
        c.ellipse((ex - 12 * s, ey - 12 * s, ex + 12 * s, ey + 12 * s), fill=eyes)
        c.ellipse((ex - 6 * s, ey - 6 * s, ex + 6 * s, ey + 6 * s), fill=(14, 14, 16))
        c.ellipse((ex - 1 * s, ey - 8 * s, ex + 5 * s, ey - 2 * s), fill=(255, 255, 255))
        c.arc((ex - 25 * s, ey - 14 * s, ex + 25 * s, ey + 16 * s), 190, 350, (40, 30, 30), width=3.5 * s)
    # nose
    c.soft("line", [(cx + 4 * s, cy - 6 * s), (cx + 12 * s, cy + 36 * s), (cx + 2 * s, cy + 46 * s)], darken(skin, 0.3), 160, width=5 * s)
    c.arc((cx - 18 * s, cy + 30 * s, cx + 18 * s, cy + 52 * s), 20, 160, darken(skin, 0.3), width=3 * s)
    # smile
    c.chord((cx - 44 * s, cy + 52 * s, cx + 44 * s, cy + 110 * s), 0, 180, (120, 40, 50))
    c.chord((cx - 36 * s, cy + 56 * s, cx + 36 * s, cy + 92 * s), 0, 180, (250, 250, 248))
    c.arc((cx - 46 * s, cy + 50 * s, cx + 46 * s, cy + 112 * s), 0, 180, lips, width=5 * s)
    c.line([(cx - 46 * s, cy + 80 * s), (cx + 46 * s, cy + 80 * s)], lips, width=4 * s)
    return (cx - 150 * s, cy - 185 * s, cx + 150 * s, cy + 160 * s)


def draw_h08(rng):
    c = Canvas(W, H)
    sky(c, 520, top=(120, 176, 226))
    c.vgrad((0, 420, W, H), [(0, (110, 160, 90)), (1, (80, 130, 66))])
    bokeh(c, rng, 40, (0, 200, W, 700), [(70, 130, 60), (110, 170, 80), (150, 190, 100)], 40, 110, (90, 160))
    c.blur_all(14)
    # two small bystanders in the background (upper right), then the subject in the foreground
    bystanders = [(1250, 330, 0.36, (236, 196, 164), (60, 40, 30), "short", (70, 110, 70), (200, 70, 70)),
                  (1420, 350, 0.34, (176, 120, 86), (30, 24, 22), "curly", (80, 60, 40), (240, 200, 60))]
    boxes = []
    for p in bystanders:
        x, y, s = p[0], p[1], p[2]
        for dx in (-70, 25):
            c.rect((x + dx * s, y + 500 * s, x + (dx + 45) * s, y + 980 * s), fill=(50, 56, 80), r=14 * s)
        boxes.append(face(c, *p))
    face(c, 760, 560, 1.55, (232, 190, 160), (120, 80, 44), "long", (70, 120, 170), (60, 120, 200))
    c.specimen_mark()
    return c.result(), {"FAC": union(*boxes)}


def draw_h09(rng):
    w, h = SW, SH
    c = Canvas(w, h)
    c.rect((0, 0, w, h), fill=(16, 16, 20))
    white = (255, 255, 255)
    c.text((80, 70), "10:24", 46, white)
    for k in range(4):
        c.rect((880 + k * 22, 108 - k * 12 - 14, 896 + k * 22, 108), fill=white, r=3)
    c.rect((990, 66, 1080, 108), outline=white, width=4, r=10)
    c.rect((998, 74, 1060, 100), fill=white, r=5)
    c.rect((1084, 78, 1092, 96), fill=white, r=2)
    # display
    c.text((w - 80, 820), "12 + 30", 96, (150, 150, 160), kind="regular", anchor="rs")
    c.text((w - 80, 1080), "42", 240, white, kind="regular", anchor="rs")
    # keypad: digits and operators only
    keys = [["(", ")", "%", "÷"], ["7", "8", "9", "×"], ["4", "5", "6", "−"], ["1", "2", "3", "+"], ["0", ".", "±", "="]]
    gap, top = 30, 1150
    d = (w - 2 * 60 - 3 * gap) / 4
    for r, row in enumerate(keys):
        for k, label in enumerate(row):
            x0 = 60 + k * (d + gap)
            y0 = top + r * (d + gap)
            if k == 3:
                fill, tc = (38, 150, 140), white
            elif r == 0:
                fill, tc = (70, 74, 86), (200, 226, 222)
            else:
                fill, tc = (42, 44, 52), white
            c.rect((x0, y0, x0 + d, y0 + d), fill=fill, r=48)
            c.text((x0 + d / 2, y0 + d / 2), label, 96, tc, kind="regular", anchor="mm")
    c.rect((w / 2 - 140, h - 40, w / 2 + 140, h - 28), fill=white, r=6)
    return c.result(), {}


def draw_h10(rng):
    c = Canvas(W, H)
    sky(c, 640, top=(70, 130, 200), low=(200, 222, 238))
    cloud(c, 1200, 140, 0.9)
    mountains = [([(0, 560), (180, 330), (330, 420), (520, 210), (720, 470), (900, 300), (1100, 460), (1300, 260),
                   (1500, 400), (1600, 360), (1600, 640), (0, 640)], (110, 126, 150), (240, 244, 250))]
    for pts, col, snow in mountains:
        c.poly(pts, fill=col)
        for (px, py) in pts[1:-3]:
            if py < 360:
                c.poly([(px, py), (px - 70, py + 80), (px - 20, py + 64), (px + 20, py + 84), (px + 66, py + 76)], fill=snow)
    c.poly([(0, 640), (0, 520), (260, 470), (520, 560), (800, 500), (1100, 560), (1350, 500), (1600, 540), (1600, 640)],
           fill=(82, 104, 96))
    for k in range(70):
        x = k * 23 + rng.uniform(-6, 6)
        hgt = rng.uniform(70, 130)
        c.poly([(x, 650), (x + 18, 650 - hgt), (x + 36, 650)], fill=rng.choice([(34, 70, 52), (44, 84, 60), (30, 60, 46)]))
    top = c.img.crop((0, 0, W * SS, 650 * SS)).transpose(Image.FLIP_TOP_BOTTOM)
    refl = top.filter(ImageFilter.GaussianBlur(3 * SS))
    tint = Image.new("RGB", refl.size, (40, 90, 120))
    refl = Image.blend(refl, tint, 0.35)
    c.img.paste(refl.crop((0, 0, W * SS, 470 * SS)), (0, 650 * SS))
    for _ in range(140):
        y = rng.uniform(660, 1120)
        x = rng.uniform(0, W)
        c.soft("line", [(x, y), (x + rng.uniform(40, 160), y)], (220, 236, 246), rng.randint(30, 90), width=1.5)
    c.vgrad((0, 1110, W, H), [(0, (130, 120, 100)), (1, (100, 92, 76))])
    for _ in range(18):
        x, y, r = rng.uniform(0, W), rng.uniform(1100, 1200), rng.uniform(16, 46)
        c.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=rng.choice([(150, 146, 140), (120, 116, 110), (170, 166, 158)]))
    return c.result(), {}


# --------------------------------------------------------------------------------------------
# Specification (single source for files, manifest.json and MANIFEST.md)
# --------------------------------------------------------------------------------------------

def F(code, label, readings="text and vision"):
    return {"code": code, "label": label, "readings": readings}


SPECS = [
    dict(id="B01", file="B01-beach-wide.jpg", set="beach-day", title="Beach wide",
         description="Wide sandy beach with striped umbrellas, towels, a beach ball and sailboats on the horizon.",
         risks=["LOC"], verdict=("Fix first", "Clear"), findings=[F("LOC", "GPS location stored in the file", "metadata")],
         time="10:05:12", gps=True, mark=True, draw=draw_b01),
    dict(id="B02", file="B02-sunset.jpg", set="beach-day", title="Sunset",
         description="Sun setting over the sea with a golden reflection and a dark headland.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="20:58:40", draw=draw_b02),
    dict(id="B03", file="B03-sandcastle.jpg", set="beach-day", title="Sandcastle",
         description="Sandcastle with three towers, a moat and a red flag, a blue bucket and a spade beside it.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="11:20:03", draw=draw_b03),
    dict(id="B04", file="B04-ice-cream.jpg", set="beach-day", title="Ice cream",
         description="Strawberry and chocolate ice cream cone with sprinkles and a cherry, beach blurred behind.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="12:41:27", draw=draw_b04),
    dict(id="B05", file="B05-dog.jpg", set="beach-day", title="Dog on the sand",
         description="Golden dog with a red collar standing on the sand next to a tennis ball, sea behind.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="13:15:50", draw=draw_b05),
    dict(id="B06", file="B06-boardwalk.jpg", set="beach-day", title="Boardwalk",
         description="Wooden boardwalk in perspective between dunes and the beach, with railings and lamp posts.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="14:02:11", draw=draw_b06),
    dict(id="B07", file="B07-house-front.jpg", set="beach-day", title="House front",
         description="Front of a house with a green door, windows with flower boxes, a number plaque and a wall street sign.",
         risks=["ADR"], verdict=("Keep private", "Clear"), findings=[F("ADR", "House number and street sign")],
         time="15:30:44", mark=True, expect="top right", draw=draw_b07),
    dict(id="B08", file="B08-car.jpg", set="beach-day", title="Car",
         description="Rear of a red hatchback parked on a seafront road with a readable license plate.",
         risks=["PLT"], verdict=("Fix first", "Clear"), findings=[F("PLT", "License plate readable")],
         time="16:04:09", mark=True, expect="bottom center", draw=draw_b08),
    dict(id="B09", file="B09-boarding-pass.jpg", set="beach-day", title="Boarding pass",
         description="Boarding pass with a barcode and a QR-style code lying on a striped beach towel next to sunglasses.",
         risks=["TKT"], verdict=("Keep private", "Fix first"), findings=[F("TKT", "Boarding pass with a barcode and QR code")],
         time="16:36:58", mark=True, expect="middle center", draw=draw_b09),
    dict(id="B10", file="B10-backpack.jpg", set="beach-day", title="Backpack",
         description="Navy school backpack on the sand with a school crest patch and a name tag, towel and ball beside it.",
         risks=["SCH"], verdict=("Keep private", "Clear"), findings=[F("SCH", "School crest and name label on a backpack")],
         time="17:10:31", mark=True, expect="middle left", draw=draw_b10),
    dict(id="B11", file="B11-seagull.jpg", set="beach-day", title="Seagull",
         description="Seagull standing on a wooden post above the sea, two gulls flying in the distance.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="17:45:16", draw=draw_b11),
    dict(id="B12", file="B12-parking.jpg", set="beach-day", title="Parking lot",
         description="Seaside parking lot with parked cars; an out-of-focus car at the bottom left shows a small, blurred plate.",
         risks=["PLT"], verdict=("Check this", "Clear"), findings=[F("PLT", "Possible license plate, blurred", "vision only")],
         time="18:22:05", mark=True, expect="bottom left", draw=draw_b12),
    dict(id="H01", file="H01-id-card.jpg", set="hazard-set", title="ID card",
         description="Fictional identity card of the Republic of Exemplia on a wooden desk, stamped SPECIMEN.",
         risks=["IDD"], verdict=("Keep private", "Fix first"), findings=[F("IDD", "Identity card visible")],
         time="09:10:00", mark=True, draw=draw_h01),
    dict(id="H02", file="H02-payment-card.jpg", set="hazard-set", title="Payment card",
         description="Fictional Exemplia Bank debit card with an all-zero number next to a cup of coffee.",
         risks=["PAY"], verdict=("Keep private", "Keep private"), findings=[F("PAY", "Payment card visible")],
         time="09:20:00", mark=True, draw=draw_h02),
    dict(id="H03", file="H03-package-label.jpg", set="hazard-set", title="Package label",
         description="Cardboard parcel on a doormat with a shipping label showing a name and street address.",
         risks=["MAL"], verdict=("Keep private", "Clear"), findings=[F("MAL", "Package label with a name and address")],
         time="09:30:00", mark=True, draw=draw_h03),
    dict(id="H04", file="H04-laptop-screen.jpg", set="hazard-set", title="Laptop screen",
         description="Laptop on a desk showing a chat app with a message thread.",
         risks=["SCR"], verdict=("Keep private", "Fix first"), findings=[F("SCR", "Screen showing a message thread")],
         time="09:40:00", mark=True, draw=draw_h04),
    dict(id="H05", file="H05-wifi-note.jpg", set="hazard-set", title="Wi-Fi note",
         description="Yellow sticky note with a handwritten Wi-Fi name and key next to a router.",
         risks=["COD"], verdict=("Keep private", "Keep private"), findings=[F("COD", "Note with a Wi-Fi key")],
         time="09:50:00", mark=True, draw=draw_h05),
    dict(id="H06", file="H06-keys.jpg", set="hazard-set", title="Keys",
         description="Three house keys and a car key fob on a ring, lying on a wooden table.",
         risks=["KEY"], verdict=("Fix first", "Clear"), findings=[F("KEY", "House and car keys clearly visible", "vision only")],
         time="10:00:00", mark=True, draw=draw_h06),
    dict(id="H07", file="H07-prescription.jpg", set="hazard-set", title="Prescription bottle",
         description="Amber pill bottle with a printed prescription label on a bathroom counter, tablets beside it.",
         risks=["MED"], verdict=("Keep private", "Fix first"), findings=[F("MED", "Prescription label")],
         time="10:10:00", mark=True, draw=draw_h07),
    dict(id="H08", file="H08-bystanders.jpg", set="hazard-set", title="Bystanders",
         description="One smiling person (the subject) in the foreground of a park, two small people in the background.",
         risks=["FAC"], verdict=("Fix first", "Clear"),
         findings=[F("FAC", "Faces of people in the background who are not the subject", "vision only")],
         time="10:20:00", mark=True, draw=draw_h08),
    dict(id="H09", file="H09-calculator-screenshot.png", web_file="H09-calculator-screenshot.jpg", set="hazard-set",
         title="Calculator screenshot",
         description="Phone screenshot of a generic calculator app showing 12 + 30 = 42; digits and operators only.",
         risks=[], verdict=("Clear", "Clear"), findings=[], time="10:24:00", screenshot=True, draw=draw_h09),
    dict(id="H10", file="H10-metadata-only.jpg", set="hazard-set", title="Metadata only",
         description="Mountain lake with pine trees and snowy peaks; the file stores an owner, a copyright and a camera serial.",
         risks=["MET"], verdict=("Clear", "Clear"),
         findings=[F("MET", "Owner, copyright and camera serial in the file", "metadata")],
         time="10:30:00", owner=True, draw=draw_h10),
]

# Expected verdicts stated in validation-plan.md (hazard set Private is derived from verdict-rules.md).
EXPECTED_COUNTS = {
    ("beach-day", "public"): {"Clear": 6, "Fix first": 2, "Check this": 1, "Keep private": 3},
    ("beach-day", "private"): {"Clear": 11, "Fix first": 1},
    ("hazard-set", "public"): {"Keep private": 6, "Fix first": 2, "Clear": 2},
}


# --------------------------------------------------------------------------------------------
# EXIF
# --------------------------------------------------------------------------------------------

IFD_EXIF, IFD_GPS = 0x8769, 0x8825
T_DESC, T_SOFT, T_DT, T_ARTIST, T_COPY = 0x010E, 0x0131, 0x0132, 0x013B, 0x8298
T_DTO, T_DTD, T_OWNER, T_SERIAL = 0x9003, 0x9004, 0xA430, 0xA431


def _dms(d, m, s):
    return (IFDRational(d, 1), IFDRational(m, 1), IFDRational(int(round(s * 100)), 100))


def make_exif(spec):
    ex = Image.Exif()
    dt = f"{DATE} {spec['time']}"
    ex[T_DESC] = DESCRIPTION
    ex[T_SOFT] = SOFTWARE
    ex[T_DT] = dt
    sub = ex.get_ifd(IFD_EXIF)
    sub[T_DTO] = dt
    sub[T_DTD] = dt
    if spec.get("owner"):
        ex[T_ARTIST] = "SPECIMEN Owner"
        ex[T_COPY] = "SPECIMEN"
        sub[T_OWNER] = "SPECIMEN Owner"
        sub[T_SERIAL] = "SPEC-0000"
    if spec.get("gps"):
        gps = ex.get_ifd(IFD_GPS)
        gps[0] = b"\x02\x02\x00\x00"
        gps[1] = "N"
        gps[2] = _dms(*GPS_LAT)
        gps[3] = "E"
        gps[4] = _dms(*GPS_LON)
    return ex.tobytes()


def _to_deg(v):
    return float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600


def verify_exif(path, spec):
    """Read EXIF back from the written file and check every planted field."""
    with Image.open(path) as im:
        im.load()
        ex = im.getexif()
    sub = ex.get_ifd(IFD_EXIF)
    dt = f"{DATE} {spec['time']}"
    assert sub.get(T_DTO) == dt, (path.name, "DateTimeOriginal", sub.get(T_DTO))
    assert ex.get(T_DESC) == DESCRIPTION, (path.name, "ImageDescription")
    out = {"DateTimeOriginal": sub.get(T_DTO)}
    gps = ex.get_ifd(IFD_GPS)
    if spec.get("gps"):
        lat, lon = _to_deg(gps[2]), _to_deg(gps[4])
        assert gps[1] == "N" and gps[3] == "E", (path.name, "GPS refs")
        assert abs(lat - 41.3784) < 1e-4 and abs(lon - 2.1925) < 1e-4, (path.name, lat, lon)
        out["GPS"] = f"{lat:.4f} {gps[1]}, {lon:.4f} {gps[3]}"
    else:
        assert not gps, (path.name, "unexpected GPS")
    if spec.get("owner"):
        assert ex.get(T_ARTIST) == "SPECIMEN Owner" and ex.get(T_COPY) == "SPECIMEN", (path.name, "owner")
        assert sub.get(T_SERIAL) == "SPEC-0000" and sub.get(T_OWNER) == "SPECIMEN Owner", (path.name, "serial")
        out.update(Artist=ex.get(T_ARTIST), Copyright=ex.get(T_COPY), BodySerialNumber=sub.get(T_SERIAL),
                   CameraOwnerName=sub.get(T_OWNER))
    else:
        assert T_ARTIST not in ex and T_COPY not in ex and T_SERIAL not in sub, (path.name, "unexpected owner fields")
    return out


# --------------------------------------------------------------------------------------------
# Manifest helpers
# --------------------------------------------------------------------------------------------

def grid_cell(nb):
    cx, cy = nb[0] + nb[2] / 2, nb[1] + nb[3] / 2
    row = "top" if cy < 1 / 3 else ("middle" if cy < 2 / 3 else "bottom")
    col = "left" if cx < 1 / 3 else ("center" if cx < 2 / 3 else "right")
    return f"{row} {col}"


def norm_bbox(b, w, h, pad=6):
    x0, y0, x1, y1 = pad_box(b, pad, w, h)
    return [round(x0 / w, 3), round(y0 / h, 3), round((x1 - x0) / w, 3), round((y1 - y0) / h, 3)]


EXIF_NOTES = {
    "gps": f"GPS 41.3784 N, 2.1925 E ({GPS_PLACE}, public place)",
    "owner": "Artist 'SPECIMEN Owner', Copyright 'SPECIMEN', CameraOwnerName 'SPECIMEN Owner', BodySerialNumber 'SPEC-0000'",
}


def write_markdown(entries, web_sizes):
    lines = [
        "# Specimen photo manifest",
        "",
        "Generated by `tests/specimens/generate.py`; do not edit by hand (re-run the generator instead).",
        "Every image is drawn from code, fictional and marked SPECIMEN: a small visible corner mark on photos with a",
        "planted visual or location risk, and `ImageDescription = \"SPECIMEN - fictional generated test image (Before You Share)\"`",
        "in the EXIF of every file. Clean photos (B02 to B06, B11) and the two expected-Clear hazard photos (H09, H10)",
        "carry no visible text mark.",
        "",
        "Positions use the Skill's 3x3 grid (top/middle/bottom and left/center/right) and are computed from the drawn",
        "element's bounding box. Risk codes and severities come from `skill/before-you-share/references/verdict-rules.md`;",
        "expected verdicts come from `skill/before-you-share/references/validation-plan.md`.",
        "",
        "| File | Set | What is drawn | Planted risk | Position | Public | Private | EXIF notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e, spec in entries:
        risk = ", ".join(e["risks"]) or "none"
        pos = "; ".join(f["position"] for f in e["findings"]) or "n/a"
        if e["risks"] == ["PLT"] and e["id"] == "B12":
            risk = "PLT (possible: small and blurred, vision only)"
        notes = [f"DateTimeOriginal {DATE} {spec['time']}"]
        if spec.get("gps"):
            notes.append(EXIF_NOTES["gps"])
        if spec.get("owner"):
            notes.append(EXIF_NOTES["owner"])
        if not spec.get("gps") and not spec.get("owner"):
            notes.append("no GPS, no owner or serial")
        if spec.get("screenshot"):
            notes.append("PNG 1170x2532, EXIF in eXIf chunk")
        draw = e["description"]
        priv = e["verdict"]["private"]
        if spec["set"] == "hazard-set":
            priv += " *"
        lines.append(f"| `{spec['file']}` | {spec['set']} | {draw} | {risk} | {pos} | {e['verdict']['public']} | {priv} | "
                     + "; ".join(notes) + " |")
    lines += [
        "",
        "\\* Hazard set, audience Private: not stated in validation-plan.md; derived from the Private column of",
        "verdict-rules.md (IDD, SCR, MED Amber; PAY, COD Red; MAL, KEY, FAC, MET Info).",
        "",
        "## Expected summary lines (validation-plan.md)",
        "",
        "- Beach day, audience Public: `12 photos checked for a public post: 6 Clear, 2 Fix first, 1 Check this, 3 Keep private.`",
        "  Clear B02, B03, B04, B05, B06, B11; Fix first B01 (LOC), B08 (PLT); Check this B12 (PLT possible);",
        "  Keep private B07 (ADR), B09 (TKT), B10 (SCH).",
        "- Beach day, audience Private: `11 Clear, 1 Fix first` (Fix first B09, TKT is Amber for Private); Info notes on",
        "  B01, B07, B08, B10 and B12.",
        "- Hazard set, audience Public: Keep private H01 (IDD), H02 (PAY), H03 (MAL), H04 (SCR), H05 (COD), H07 (MED);",
        "  Fix first H06 (KEY), H08 (FAC, no recognized people); Clear H09, H10 (MET is Info for Public).",
        "  As a summary line: `10 photos checked for a public post: 2 Clear, 2 Fix first, 0 Check this, 6 Keep private.`",
        "- Hazard set, audience Private (derived, not in validation-plan.md): Keep private H02 (PAY), H05 (COD);",
        "  Fix first H01 (IDD), H04 (SCR), H07 (MED); Clear H03, H06, H08, H09, H10.",
        "",
        "## Notes for testers",
        "",
        "- H02 must be reported only as \"payment card visible\".",
        "- H03's label also shows a street address, so the readings may add ADR; the verdicts do not change",
        "  (Public: Keep private either way; Private: MAL and ADR are both Info).",
        "- B12 is deliberately borderline: the plate is small and out of focus so that text reading cannot read it and",
        "  visual reading should answer \"unsure\" or \"yes\" without text support (Possible, so Check this).",
        "- Web copies in `docs/assets/specimens/` are stripped of EXIF; `manifest.json` records what the originals carry.",
        "- H08 defines FAC as faces of people in the background who are not the subject (one large subject in the",
        "  foreground, two small bystanders). Drawn faces are unreliable for vision models and for the NAS face index;",
        "  on the testing day re-shoot H08 as a real phone photo with consenting people (one subject close, two people",
        "  further back) and keep the drawn file only as a fallback.",
        "- Real-photo variant: the printable props (H01 ID card, B09 boarding pass, H03 package label, H02 payment card,",
        "  H05 Wi-Fi note, H07 prescription label) can be printed from the web copies or originals and photographed with",
        "  a phone on a table; expected verdicts stay the same. Everything printed is fictional and marked SPECIMEN.",
        "- H09 is a calculator screenshot with digits and operators only (no place names, no messages): Clear everywhere.",
        "",
        "## Web copies",
        "",
        "| Web file | Size |",
        "| --- | --- |",
    ]
    for name, (w, h) in web_sizes:
        lines.append(f"| `docs/assets/specimens/{name}` | {w}x{h} |")
    (HERE / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------

def main():
    WEB.mkdir(parents=True, exist_ok=True)
    print("Fonts:", ", ".join(f"{k}={v}" for k, v in fonts_in_use().items()))
    entries, web_sizes, digest = [], [], hashlib.sha256()
    for idx, spec in enumerate(SPECS):
        rng = random.Random(1000 + idx)
        img, boxes = spec["draw"](rng)
        out_dir = HERE / spec["set"]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / spec["file"]
        exif = make_exif(spec)
        if spec.get("screenshot"):
            assert img.size == (SW, SH)
            img.save(path, "PNG", optimize=True, exif=exif)
        else:
            assert img.size == (W, H)
            img.save(path, "JPEG", quality=JPEG_Q, optimize=True, exif=exif)
        read = verify_exif(path, spec)
        # web copy (no EXIF)
        ww = WEB_W_SHOT if spec.get("screenshot") else WEB_W
        wh = int(round(img.height * ww / img.width))
        web = img.resize((ww, wh), Image.LANCZOS)
        web_name = spec.get("web_file", spec["file"])
        web.save(WEB / web_name, "JPEG", quality=WEB_Q, optimize=True, progressive=True)
        web_sizes.append((web_name, (ww, wh)))
        # findings with positions
        findings = []
        for f in spec["findings"]:
            if f["readings"] == "metadata":
                findings.append({**f, "position": "metadata", "bbox": None})
                continue
            nb = norm_bbox(boxes[f["code"]], img.width, img.height)
            pos = grid_cell(nb)
            if spec.get("expect"):
                assert pos == spec["expect"], (spec["id"], pos, spec["expect"])
            findings.append({"code": f["code"], "label": f["label"], "position": pos, "bbox": nb, "readings": f["readings"]})
        entry = {
            "id": spec["id"], "file": web_name, "set": spec["set"], "title": spec["title"],
            "description": spec["description"], "risks": spec["risks"],
            "verdict": {"public": spec["verdict"][0], "private": spec["verdict"][1]},
            "findings": [{k: f[k] for k in ("code", "label", "position", "bbox", "readings")} for f in findings],
            "exif": {"gps": bool(spec.get("gps")), "place": GPS_PLACE if spec.get("gps") else None,
                     "owner": bool(spec.get("owner")), "serial": bool(spec.get("owner"))},
            "width": ww, "height": wh,
        }
        entries.append((entry, spec))
        digest.update(path.read_bytes())
        digest.update((WEB / web_name).read_bytes())
        pos_txt = ", ".join(f"{f['code']} {f['position']}" for f in entry["findings"]) or "-"
        print(f"{spec['id']}  {path.relative_to(REPO).as_posix():45s} {path.stat().st_size / 1024:7.1f} KB  "
              f"{pos_txt:28s} EXIF {read}")

    # expected verdict counts must match validation-plan.md
    for (set_name, aud), want in EXPECTED_COUNTS.items():
        got = {}
        for e, _ in entries:
            if e["set"] == set_name:
                v = e["verdict"][aud]
                got[v] = got.get(v, 0) + 1
        assert got == want, (set_name, aud, got, want)

    manifest = {"generated": GENERATED, "images": [e for e, _ in entries]}
    (WEB / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(entries, web_sizes)

    def total(p, pattern="*"):
        return sum(f.stat().st_size for f in p.rglob(pattern) if f.is_file())

    t_spec, t_web = total(HERE), total(WEB)
    print(f"tests/specimens total: {t_spec / 1024 / 1024:.2f} MB (budget 12 MB)")
    print(f"docs/assets/specimens total: {t_web / 1024 / 1024:.2f} MB (budget 2 MB)")
    print(f"content digest (sha256 of all images): {digest.hexdigest()}")
    if t_spec > 12 * 1024 * 1024 or t_web > 2 * 1024 * 1024:
        print("WARNING: size budget exceeded", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
