"""Tiny slide layout engine: one layout description, two outputs.

``Deck`` collects shapes, text and images in inches. ``save_pptx`` writes them with python-pptx
(Arial, so it renders the same on any machine) and ``render_previews`` draws a PNG of every slide
with PIL using Liberation Sans, which has Arial's exact metrics. The same text-wrapping code
drives both the overflow check and the preview, so a box that fits in the preview fits in
PowerPoint. Used by ``src/make_full_deck.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

W, H = 13.333, 7.5
FONT = "Calibri"       # body text
HEAD_FONT = "Cambria"  # titles and big numbers, as in the reference deck
PX = 100  # preview pixels per inch
LINE = 1.2  # line height as a multiple of the font size (a little more than Arial's 1.15)
_FONT_DIRS = ["/run/host/fonts/liberation", "/usr/share/fonts/liberation-fonts", "/usr/share/fonts/liberation"]


def _font_path(bold, serif=False):
    base = "LiberationSerif" if serif else "LiberationSans"
    name = f"{base}-Bold.ttf" if bold else f"{base}-Regular.ttf"
    for d in _FONT_DIRS:
        if Path(d, name).exists():
            return str(Path(d, name))
    raise FileNotFoundError(name)


_FONT_CACHE: dict = {}


def _pil_font(size_pt, bold, serif=False):
    """Preview/measure font. Measuring always uses Liberation Sans (Arial metrics), which is wider than
    Calibri and Cambria, so a box that fits here also fits in PowerPoint."""
    key = (round(size_pt * 4), bold, serif)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(_font_path(bold, serif), max(1, round(size_pt * PX / 72)))
    return _FONT_CACHE[key]


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


@dataclass
class Para:
    """One paragraph: a list of ``(text, bold, color)`` runs sharing size and alignment."""
    runs: list
    size: float = 14
    align: str = "l"
    bullet: bool = False
    after: float = 4  # points of space after
    italic: bool = False
    head: bool = False   # Cambria (titles, big numbers) instead of Calibri
    track: float = 0.0   # letter spacing in points


def paras(spec, size, color, bold, align="l", bullet=False, after=4, head=False, track=0.0):
    """Accept a string, a list of strings, or a list of ``Para`` / ``(text, dict)`` items."""
    if isinstance(spec, (str, Para)):
        spec = [spec]
    out = []
    for item in spec:
        if isinstance(item, Para):
            out.append(item)
        elif isinstance(item, tuple):
            text, o = item
            runs = o.get("runs") or [(text, o.get("bold", bold), o.get("color", color))]
            out.append(Para(runs, o.get("size", size), o.get("align", align), o.get("bullet", bullet),
                            o.get("after", after), o.get("italic", False), o.get("head", head), o.get("track", track)))
        else:
            out.append(Para([(item, bold, color)], size, align, bullet, after, False, head, track))
    return out


@dataclass
class Shape:
    kind: str
    x: float
    y: float
    w: float
    h: float
    fill: str | None = None
    line: str | None = None
    line_w: float = 1.0
    radius: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    paras: list = field(default_factory=list)
    valign: str = "t"
    path: str = ""
    pad: float = 0.0
    name: str = ""


class Slide:
    def __init__(self, bg):
        self.bg, self.shapes, self.notes = bg, [], ""

    def rect(self, x, y, w, h, fill, line=None, radius=0.0, line_w=1.0, name=""):
        self.shapes.append(Shape("rect", x, y, w, h, fill, line, line_w, radius, name=name))

    def oval(self, x, y, w, h, fill, line=None, name=""):
        self.shapes.append(Shape("oval", x, y, w, h, fill, line, name=name))

    def line(self, x, y, x2, y2, color, width=1.0):
        self.shapes.append(Shape("line", x, y, 0, 0, None, color, width, x2=x2, y2=y2))

    def text(self, x, y, w, h, spec, size=14, color="1F2A37", bold=False, align="l", valign="t",
             bullet=False, after=4, pad=0.0, name="", head=False, track=0.0):
        self.shapes.append(Shape("text", x, y, w, h, paras=paras(spec, size, color, bold, align, bullet, after, head, track),
                                 valign=valign, pad=pad, name=name))

    def image(self, path, x, y, w, h, name=""):
        """Place ``path`` inside the box, keeping its aspect ratio and centring it."""
        iw, ih = Image.open(path).size
        s = min(w / iw, h / ih)
        nw, nh = iw * s, ih * s
        self.shapes.append(Shape("image", x + (w - nw) / 2, y + (h - nh) / 2, nw, nh, path=str(path), name=name))


class Deck:
    def __init__(self, bg="FFFFFF"):
        self.bg, self.slides = bg, []

    def slide(self, notes=""):
        s = Slide(self.bg)
        s.notes = notes
        self.slides.append(s)
        return s


# ---------------------------------------------------------------- text layout
def wrap(para, width_px):
    """Wrap one paragraph into lines of ``(text, bold, color)`` segments; returns (lines, line_height_px)."""
    words = []
    for text, bold, color in para.runs:
        for i, token in enumerate(text.split(" ")):
            if token or i == 0:
                words.append((token, bold, color))
    lines, cur, cur_w = [], [], 0.0
    tr = para.track * PX / 72
    space = _pil_font(para.size, False).getlength(" ") + tr
    for token, bold, color in words:
        w = _pil_font(para.size, bold).getlength(token) + tr * len(token)
        add = w if not cur else w + space
        if cur and cur_w + add > width_px:
            lines.append(cur)
            cur, cur_w = [(token, bold, color)], w
        else:
            cur.append((token, bold, color))
            cur_w += add
    lines.append(cur)
    return lines, para.size * PX / 72 * LINE


BULLET_INDENT = 0.2  # inches


def measure(shape):
    """Height in inches that the text needs inside ``shape``."""
    inner = (shape.w - 2 * shape.pad) * PX
    total = 0.0
    for p in shape.paras:
        avail = inner - (BULLET_INDENT * PX if p.bullet else 0)
        lines, lh = wrap(p, avail)
        total += len(lines) * lh + p.after * PX / 72
    return total / PX + 2 * shape.pad


def text_height(spec, width, size=14, color="1F2A37", bold=False, bullet=False, after=4):
    """Height in inches that ``spec`` needs in a box ``width`` inches wide (without trailing space)."""
    ps = paras(spec, size, color, bold, "l", bullet, after)
    return measure(Shape("text", 0, 0, width, 0, paras=ps)) - ps[-1].after / 72


def _longest_token(shape):
    widest = 0.0
    for p in shape.paras:
        for text, bold, _ in p.runs:
            for token in text.split(" "):
                widest = max(widest, _pil_font(p.size, bold).getlength(token) + p.track * PX / 72 * len(token))
    return widest / PX


def check_overflow(deck, tolerance=0.02):
    """List ``(slide_number, text_start, needed, available)`` for text that does not fit its box."""
    bad = []
    for n, s in enumerate(deck.slides, 1):
        for sh in s.shapes:
            if sh.kind != "text":
                continue
            need = measure(sh) - sh.paras[-1].after / 72  # trailing space is not visible
            if need > sh.h + tolerance:
                bad.append((n, sh.paras[0].runs[0][0][:50], round(need, 2), round(sh.h, 2)))
            elif _longest_token(sh) > sh.w - 2 * sh.pad + 0.01:
                bad.append((n, "WORD TOO WIDE: " + sh.paras[0].runs[0][0][:40], round(_longest_token(sh), 2), round(sh.w, 2)))
    return bad


def check_bounds(deck):
    bad = []
    for n, s in enumerate(deck.slides, 1):
        for sh in s.shapes:
            if sh.kind == "line":
                continue
            if sh.x < -0.01 or sh.y < -0.01 or sh.x + sh.w > W + 0.01 or sh.y + sh.h > H + 0.01:
                bad.append((n, sh.kind, round(sh.x, 2), round(sh.y, 2), round(sh.w, 2), round(sh.h, 2)))
    return bad


# ---------------------------------------------------------------- pptx output
def _rgb(h):
    return RGBColor(*hex_rgb(h))


def _set_bullet(p, on):
    pPr = p._p.get_or_add_pPr()
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    if on:
        pPr.set("marL", str(int(Inches(BULLET_INDENT))))
        pPr.set("indent", str(-int(Inches(BULLET_INDENT))))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        pPr.append(bu)
    else:
        pPr.set("marL", "0")
        pPr.set("indent", "0")
        pPr.append(pPr.makeelement(qn("a:buNone"), {}))


def save_pptx(deck, path, title="Stack Overflow in the AI Era"):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    prs.core_properties.title = title
    blank = prs.slide_layouts[6]
    for s in deck.slides:
        sl = prs.slides.add_slide(blank)
        fill = sl.background.fill
        fill.solid()
        fill.fore_color.rgb = _rgb(s.bg)
        for sh in s.shapes:
            if sh.kind in ("rect", "oval"):
                kind = MSO_SHAPE.OVAL if sh.kind == "oval" else (
                    MSO_SHAPE.ROUNDED_RECTANGLE if sh.radius > 0 else MSO_SHAPE.RECTANGLE)
                shp = sl.shapes.add_shape(kind, Inches(sh.x), Inches(sh.y), Inches(sh.w), Inches(sh.h))
                if sh.kind == "rect" and sh.radius > 0:
                    shp.adjustments[0] = min(0.5, sh.radius / min(sh.w, sh.h))
                shp.shadow.inherit = False
                if sh.fill:
                    shp.fill.solid()
                    shp.fill.fore_color.rgb = _rgb(sh.fill)
                else:
                    shp.fill.background()
                if sh.line:
                    shp.line.color.rgb = _rgb(sh.line)
                    shp.line.width = Pt(sh.line_w)
                else:
                    shp.line.fill.background()
                if sh.name:
                    shp.name = sh.name
            elif sh.kind == "line":
                ln = sl.shapes.add_connector(1, Inches(sh.x), Inches(sh.y), Inches(sh.x2), Inches(sh.y2))
                ln.line.color.rgb = _rgb(sh.line)
                ln.line.width = Pt(sh.line_w)
            elif sh.kind == "image":
                sl.shapes.add_picture(sh.path, Inches(sh.x), Inches(sh.y), Inches(sh.w), Inches(sh.h))
            elif sh.kind == "text":
                tb = sl.shapes.add_textbox(Inches(sh.x), Inches(sh.y), Inches(sh.w), Inches(sh.h))
                if sh.name:
                    tb.name = sh.name
                tf = tb.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_right = Inches(sh.pad)
                tf.margin_top = tf.margin_bottom = Inches(sh.pad)
                tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[sh.valign]
                for i, p in enumerate(sh.paras):
                    para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    para.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[p.align]
                    para.space_after = Pt(p.after)
                    _set_bullet(para, p.bullet)
                    for text, bold, color in p.runs:
                        r = para.add_run()
                        r.text = text
                        r.font.name, r.font.size, r.font.bold = (HEAD_FONT if p.head else FONT), Pt(p.size), bool(bold)
                        r.font.italic = p.italic
                        if p.track:
                            r._r.get_or_add_rPr().set("spc", str(int(p.track * 100)))
                        r.font.color.rgb = _rgb(color)
        if s.notes:
            sl.notes_slide.notes_text_frame.text = s.notes
    prs.save(path)


# ---------------------------------------------------------------- preview output
def render_previews(deck, outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for n, s in enumerate(deck.slides, 1):
        img = Image.new("RGB", (round(W * PX), round(H * PX)), hex_rgb(s.bg))
        d = ImageDraw.Draw(img)
        for sh in s.shapes:
            x, y, w, h = (round(v * PX) for v in (sh.x, sh.y, sh.w, sh.h))
            if sh.kind == "rect":
                box = [x, y, x + w, y + h]
                kw = dict(fill=hex_rgb(sh.fill) if sh.fill else None, outline=hex_rgb(sh.line) if sh.line else None,
                          width=max(1, round(sh.line_w)))
                if sh.radius > 0:
                    d.rounded_rectangle(box, radius=round(sh.radius * PX), **kw)
                else:
                    d.rectangle(box, **kw)
            elif sh.kind == "oval":
                d.ellipse([x, y, x + w, y + h], fill=hex_rgb(sh.fill) if sh.fill else None,
                          outline=hex_rgb(sh.line) if sh.line else None)
            elif sh.kind == "line":
                d.line([x, y, round(sh.x2 * PX), round(sh.y2 * PX)], fill=hex_rgb(sh.line), width=max(1, round(sh.line_w)))
            elif sh.kind == "image":
                im = Image.open(sh.path).convert("RGBA").resize((max(1, w), max(1, h)), Image.LANCZOS)
                img.paste(im, (x, y), im)
            elif sh.kind == "text":
                inner = (sh.w - 2 * sh.pad) * PX
                total = measure(sh) * PX - 2 * sh.pad * PX
                top = y + sh.pad * PX
                if sh.valign == "m":
                    top = y + (h - total) / 2
                elif sh.valign == "b":
                    top = y + h - total - sh.pad * PX
                cy = top
                for p in sh.paras:
                    indent = BULLET_INDENT * PX if p.bullet else 0
                    lines, lh = wrap(p, inner - indent)
                    for li, line in enumerate(lines):
                        fnt = lambda b, p=p: _pil_font(p.size, b, p.head)
                        tr = p.track * PX / 72
                        width = sum(fnt(b).getlength(t) + tr * len(t) for t, b, _ in line) + \
                            (fnt(False).getlength(" ") + tr) * (len(line) - 1)
                        cx = x + sh.pad * PX + indent
                        if p.align == "c":
                            cx = x + (w - width) / 2
                        elif p.align == "r":
                            cx = x + w - sh.pad * PX - width
                        if p.bullet and li == 0:
                            d.text((x + sh.pad * PX, cy), "•", font=_pil_font(p.size, False), fill=hex_rgb(line[0][2]))
                        for t, b, c in line:
                            if tr:
                                for ch_ in t:
                                    d.text((cx, cy), ch_, font=fnt(b), fill=hex_rgb(c))
                                    cx += fnt(b).getlength(ch_) + tr
                                cx += fnt(False).getlength(" ") + tr
                            else:
                                d.text((cx, cy), t, font=fnt(b), fill=hex_rgb(c))
                                cx += fnt(b).getlength(t + " ")
                        cy += lh
                    cy += p.after * PX / 72
        f = out / f"slide_{n:02d}.png"
        img.save(f)
        files.append(f)
    return files


def contact_sheet(files, path, cols=3, thumb_w=640):
    ims = [Image.open(f) for f in files]
    tw = thumb_w
    th = round(tw * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 10, rows * th + (rows + 1) * 10), (40, 40, 40))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), (10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 10)))
    sheet.save(path)
    return path
