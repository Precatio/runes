"""T-shirtdesign: Vitkis bindruna (web/public/vitki_logo.png, avläst i originalets 137 × 114-rutnät), ordmärket Vitki i
Helvetica Neue fet med tät spärrning som i appen, och en rad text. Tryckyta 4500 × 4800 px (15 × 16 tum vid 300 dpi).
Skriver vitki_tshirt.jpg (vit bakgrund, kvalitet 95), vitki_tshirt_transparent.png (för tryckerier) och en förhandsbild.
    .venv/bin/python utdata/design/tshirt.py [--text "…"]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RUST = (183, 65, 14)
W, H = 4500, 4800
TEXT = sys.argv[sys.argv.index("--text") + 1] if "--text" in sys.argv else "Läser runor med siffror."

# the bind rune's strokes in the logo's own pixel grid (x, y), stroke width 6 of 137
STAVE = ((70, 19), (71, 80))
STROKES = [STAVE, ((69, 19), (53, 36)), ((69, 19), (85, 35)),   # ᛏ: the stave and its two arms
           ((71, 37), (89, 43)), ((71, 46), (89, 54)),           # two more branches to the right
           ((70, 56), (53, 69))]                                 # one branch to the left
LOGO_W = 6.0


def face(name_part, style):
    """A face in the system's Helvetica Neue collection by family and style."""
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    for i in range(40):
        try:
            f = ImageFont.truetype(path, 100, index=i)
        except OSError:
            break
        fam, sty = f.getname()
        if name_part in fam and sty == style:
            return path, i
    raise SystemExit(f"hittar inte {name_part} {style}")


def draw_rune(img, cx, top, height):
    """The bind rune scaled so that its stave is `height` tall, centred on cx."""
    s = height / (STAVE[1][1] - STAVE[0][1])
    ox, oy = cx - STAVE[0][0] * s, top - STAVE[0][1] * s
    d = ImageDraw.Draw(img)
    w = int(LOGO_W * s)
    r = w // 2
    for (x1, y1), (x2, y2) in STROKES:
        p1, p2 = (ox + x1 * s, oy + y1 * s), (ox + x2 * s, oy + y2 * s)
        d.line([p1, p2], fill=RUST, width=w)
        for (x, y) in (p1, p2):
            d.ellipse([x - r, y - r, x + r, y + r], fill=RUST)  # round ends, as in the logo


def text_block(img, y, text, fontspec, size, colour, tracking):
    path, idx = fontspec
    f = ImageFont.truetype(path, size, index=idx)
    d = ImageDraw.Draw(img)
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (img.width - total) / 2
    for ch, wch in zip(text, widths):
        d.text((x, y), ch, font=f, fill=colour)
        x += wch + tracking
    return f.getbbox(text)[3] - f.getbbox(text)[1]


def compose(background):
    img = Image.new("RGBA", (W, H), background)
    draw_rune(img, W / 2, 420, 2050)
    bold = face("Helvetica Neue", "Bold")
    y = 2750
    h = text_block(img, y, "Vitki", bold, 720, (15, 23, 42, 255), -22)  # slate-900, tight tracking like the app
    regular = face("Helvetica Neue", "Regular")
    text_block(img, y + 980, TEXT, regular, 150, RUST + (255,), 6)
    return img


png = compose((0, 0, 0, 0))
png.save(os.path.join(HERE, "vitki_tshirt_transparent.png"), dpi=(300, 300))
jpg = compose((255, 255, 255, 255)).convert("RGB")
jpg.save(os.path.join(HERE, "vitki_tshirt.jpg"), quality=95, dpi=(300, 300), subsampling=0)
jpg.resize((W // 6, H // 6), Image.LANCZOS).save(os.path.join(HERE, "vitki_tshirt_preview.png"))
print("skrivet:", os.path.join(HERE, "vitki_tshirt.jpg"), jpg.size, "300 dpi")
