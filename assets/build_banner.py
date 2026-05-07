"""
Generate the README banner.

Run:
    python assets/build_banner.py

Outputs assets/banner.png (1280x320 PNG, ~30KB) used as the README hero.
The banner is regenerable from the Unveil logo + Segoe UI system fonts.
"""
from __future__ import annotations
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "assets" / "unveil_logo.png"
OUT  = ROOT / "assets" / "banner.png"

W, H = 1280, 320

TITLE_TOP    = "Omniverse Viewport"
TITLE_BOTTOM = "Spout Sender"
TAGLINE      = "Real-time viewport streaming for NVIDIA Omniverse Kit 109  ·  Windows x64"
FOOTER       = "Unveil Studio  ·  MIT License"

# Accent color: NVIDIA / Omniverse green.
ACCENT = (118, 185, 0)


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    """Try Segoe UI Variable first (Win 11), fall back to classic Segoe UI."""
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


def main() -> None:
    img = Image.new("RGB", (W, H), (5, 8, 5))
    draw = ImageDraw.Draw(img)

    # Subtle radial-ish vignette behind the logo — green-tinted to match the brand.
    glow = Image.new("RGB", (W, H), (5, 8, 5))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-200, -100, 600, H + 100), fill=(20, 70, 15))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=120))
    img = Image.blend(img, glow, alpha=0.55)
    draw = ImageDraw.Draw(img)

    # Logo on the left, vertically centred.
    logo_target = 220
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((logo_target, logo_target), Image.LANCZOS)
    pad_left = 64
    img.paste(logo, (pad_left, (H - logo.height) // 2), logo)

    # Two-line stacked title on the right.
    text_x = pad_left + logo_target + 56
    title_font   = _font("bold", 64)
    title_font_b = _font("bold", 64)
    tagline_font = _font("regular", 24)
    footer_font  = _font("regular", 18)

    # Top line: "Omniverse Viewport" (white)
    bbox_top = draw.textbbox((0, 0), TITLE_TOP, font=title_font)
    h_top = bbox_top[3] - bbox_top[1]
    bbox_bot = draw.textbbox((0, 0), TITLE_BOTTOM, font=title_font_b)
    h_bot = bbox_bot[3] - bbox_bot[1]

    block_h = h_top + 6 + h_bot
    title_y = (H - block_h) // 2 - 16

    draw.text((text_x, title_y), TITLE_TOP, font=title_font, fill=(245, 245, 248))
    draw.text((text_x, title_y + h_top + 6), TITLE_BOTTOM, font=title_font_b, fill=ACCENT)

    # Underline accent bar under the second line.
    bot_y = title_y + h_top + 6 + h_bot
    draw.rectangle(
        (text_x, bot_y + 14, text_x + 110, bot_y + 18),
        fill=ACCENT,
    )

    # Tagline below the underline.
    draw.text(
        (text_x, bot_y + 32),
        TAGLINE,
        font=tagline_font,
        fill=(190, 200, 190),
    )

    # Footer bottom-right.
    fb = draw.textbbox((0, 0), FOOTER, font=footer_font)
    draw.text(
        (W - (fb[2] - fb[0]) - 40, H - (fb[3] - fb[1]) - 28),
        FOOTER,
        font=footer_font,
        fill=(110, 120, 110),
    )

    img.save(OUT, optimize=True)
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT}  ({W}x{H}, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
