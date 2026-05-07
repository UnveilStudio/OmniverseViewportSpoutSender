"""
Generate the 16:9 Patreon / social cover image (1920x1080).

Run:
    python assets/build_banner_16x9.py

Outputs assets/banner_16x9.png — uses assets/demo.png as the hero
background, darkened, with a Unveil Studio overlay (logo + title +
URL + tag stripe).
"""
from __future__ import annotations
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "assets" / "demo.png"
LOGO = ROOT / "assets" / "unveil_logo.png"
OUT  = ROOT / "assets" / "banner_16x9.png"

W, H = 1920, 1080

ACCENT = (118, 185, 0)            # NVIDIA / Omniverse green
TEXT_0 = (245, 245, 248)
TEXT_1 = (200, 210, 200)
TEXT_2 = (140, 150, 140)


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "bold":    ["seguivb.ttf", "segoeuib.ttf", "arialbd.ttf"],
        "regular": ["seguivar.ttf", "segoeui.ttf", "arial.ttf"],
        "light":   ["seguivar.ttf", "segoeuil.ttf", "arial.ttf"],
    }[weight]
    for name in candidates:
        path = os.path.join(r"C:\Windows\Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _mono(size: int) -> ImageFont.FreeTypeFont:
    for name in ("consola.ttf", "cour.ttf"):
        path = os.path.join(r"C:\Windows\Fonts", name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main() -> None:
    # ── Hero: the demo screenshot, cover-fitted to 1920x1080 ──────────
    hero = Image.open(DEMO).convert("RGB")
    hw, hh = hero.size
    target_ratio = W / H
    src_ratio = hw / hh
    if src_ratio > target_ratio:
        new_h = H
        new_w = int(H * src_ratio)
    else:
        new_w = W
        new_h = int(W / src_ratio)
    hero = hero.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    hero = hero.crop((left, top, left + W, top + H))

    # Darken the hero so the overlay reads (left-heavy: gradient).
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        # opaque-ish on the left, near-transparent on the right
        a = int(220 * max(0.0, 1.0 - (x / (W * 0.65))))
        gd.line((x, 0, x, H), fill=a)
    dark = Image.new("RGB", (W, H), (4, 8, 4))
    img = Image.composite(dark, hero, grad)

    # ── Subtle radial green wash behind title area ────────────────────
    wash = Image.new("RGB", (W, H), (5, 8, 5))
    wd = ImageDraw.Draw(wash)
    wd.ellipse((-300, 100, 900, H + 200), fill=(20, 75, 15))
    wash = wash.filter(ImageFilter.GaussianBlur(radius=200))
    img = Image.blend(img, wash, alpha=0.30)
    draw = ImageDraw.Draw(img)

    # ── Header strip: brand mark + accent dot row, top-left ───────────
    f_brand   = _mono(24)
    f_brand_b = _font("bold", 96)
    f_sub     = _mono(28)
    f_url     = _mono(30)
    f_tag     = _mono(24)
    f_foot    = _mono(20)

    pad_l = 80
    pad_r = 80

    draw.text((pad_l, 56), "UNVEIL  ·  STUDIO", font=f_brand, fill=TEXT_0)
    draw.text((pad_l, 90),
              "open source for live performance",
              font=f_sub, fill=TEXT_2)

    # divider under header
    draw.line((pad_l, 150, W - pad_r, 150), fill=(60, 80, 60), width=1)

    # ── Title: stacked, big ───────────────────────────────────────────
    title_top = "Omniverse Viewport"
    title_bot = "Spout Sender"

    bbox_top = draw.textbbox((0, 0), title_top, font=f_brand_b)
    h_top = bbox_top[3] - bbox_top[1]
    bbox_bot = draw.textbbox((0, 0), title_bot, font=f_brand_b)
    h_bot = bbox_bot[3] - bbox_bot[1]

    title_y = 240

    # Title text shadow for readability
    for dx, dy in ((3, 3), (-2, 2), (2, -2)):
        draw.text((pad_l + dx, title_y + dy), title_top,
                  font=f_brand_b, fill=(0, 0, 0))
        draw.text((pad_l + dx, title_y + h_top + 8 + dy), title_bot,
                  font=f_brand_b, fill=(0, 0, 0))

    draw.text((pad_l, title_y), title_top, font=f_brand_b, fill=TEXT_0)
    draw.text((pad_l, title_y + h_top + 8), title_bot,
              font=f_brand_b, fill=ACCENT)

    # accent stripe
    bot_y = title_y + h_top + 8 + h_bot
    draw.rectangle((pad_l, bot_y + 24, pad_l + 200, bot_y + 30), fill=ACCENT)

    # tagline
    f_tagline = _font("regular", 36)
    tagline = "Real-time viewport streaming for NVIDIA Omniverse Kit 109"
    for dx, dy in ((2, 2),):
        draw.text((pad_l + dx, bot_y + 56 + dy), tagline,
                  font=f_tagline, fill=(0, 0, 0))
    draw.text((pad_l, bot_y + 56), tagline, font=f_tagline, fill=TEXT_1)

    sub2 = "Kit 109  ·  Spout 2.007.017  ·  Windows x64  ·  MIT"
    draw.text((pad_l + 2, bot_y + 110 + 2), sub2, font=f_tag, fill=(0, 0, 0))
    draw.text((pad_l, bot_y + 110), sub2, font=f_tag, fill=TEXT_2)

    # ── Footer strip: stacked URL (top) + perf tag (below) ────────────
    foot_y = H - 140
    draw.line((pad_l, foot_y, W - pad_r, foot_y), fill=(60, 80, 60), width=1)

    url = "github.com/UnveilStudio/OmniverseViewportSpoutSender"
    for dx, dy in ((2, 2),):
        draw.text((pad_l + dx, foot_y + 28 + dy), url,
                  font=f_url, fill=(0, 0, 0))
    draw.text((pad_l, foot_y + 28), url, font=f_url, fill=TEXT_0)

    perf = "RTX Real-Time 2.0  ·  74 FPS  ·  GPU shared texture  ·  zero file I/O"
    draw.text((pad_l + 2, foot_y + 78 + 2), perf,
              font=f_tag, fill=(0, 0, 0))
    draw.text((pad_l, foot_y + 78), perf, font=f_tag, fill=TEXT_1)

    # tiny logo bottom-right corner of header strip
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        logo.thumbnail((110, 110), Image.LANCZOS)
        img.paste(logo, (W - pad_r - logo.width, 36), logo)

    img.save(OUT, optimize=True)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT}  ({W}x{H}, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
