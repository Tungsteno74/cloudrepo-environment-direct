"""Generate the CloudRepo brand icon using only a build-time Pillow dependency."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SIZE = 1024
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "plugins" / "cloudrepo-environment-direct" / "assets" / "icon.png"


def blend(top: tuple[int, int, int], bottom: tuple[int, int, int], fraction: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * fraction) for a, b in zip(top, bottom))


def cloud_mask() -> Image.Image:
    mask = Image.new("L", (SIZE, SIZE))
    draw = ImageDraw.Draw(mask)
    draw.ellipse((75, 365, 480, 790), fill=255)
    draw.ellipse((220, 115, 800, 790), fill=255)
    draw.ellipse((595, 360, 960, 795), fill=255)
    draw.rounded_rectangle((100, 440, 940, 820), radius=155, fill=255)
    return mask


def gradient(mask: Image.Image, start: tuple[int, int, int], end: tuple[int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(layer)
    for y in range(SIZE):
        t = min(1, max(0, (y - 150) / 720))
        draw.line((0, y, SIZE, y), fill=(*blend(start, end, t), 255))
    layer.putalpha(mask)
    return layer


def gear_vertices(cx: int, cy: int, teeth: int = 10) -> list[tuple[int, int]]:
    points = []
    step = 2 * math.pi / teeth
    for index in range(teeth):
        for offset, radius in (
            (0.00, 150), (0.13, 150), (0.21, 191),
            (0.42, 191), (0.51, 150), (0.79, 150)
        ):
            angle = index * step + offset * step - math.pi / 2
            points.append((
                round(cx + radius * math.cos(angle)),
                round(cy + radius * math.sin(angle)),
            ))
    return points


def make_icon() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE))
    mask = cloud_mask()

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(38)).point(lambda a: round(a * 0.45))
    shadow.paste((0, 53, 149, 0), (0, 0, SIZE, SIZE))
    shadow.putalpha(shadow_alpha)
    image.alpha_composite(shadow)

    rim_mask = mask.filter(ImageFilter.MaxFilter(19))
    rim = Image.new("RGBA", (SIZE, SIZE), (2, 146, 250, 255))
    rim.putalpha(rim_mask)
    image.alpha_composite(rim)
    image.alpha_composite(gradient(mask, (247, 253, 255), (0, 153, 248)))

    wave_mask = Image.new("L", (SIZE, SIZE))
    wave_draw = ImageDraw.Draw(wave_mask)
    wave_draw.polygon(
        [(80, 743), (190, 720), (350, 652), (520, 605),
         (690, 570), (850, 625), (980, 700), (980, 840), (70, 840)],
        fill=135
    )
    wave_mask = ImageChops.multiply(wave_mask, mask)
    wave = Image.new("RGBA", (SIZE, SIZE), (0, 126, 244, 255))
    wave.putalpha(wave_mask)
    image.alpha_composite(wave)

    sheen = Image.new("RGBA", (SIZE, SIZE))
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.arc((190, 168, 810, 740), 181, 346, fill=(255, 255, 255, 190), width=12)
    sheen_draw.arc((105, 425, 955, 839), 8, 163, fill=(255, 255, 255, 140), width=8)
    image.alpha_composite(sheen)

    details = Image.new("RGBA", (SIZE, SIZE))
    d = ImageDraw.Draw(details)
    d.line(((310, 678), (710, 678)), fill=(0, 70, 168, 195), width=20, joint="curve")
    for x in (310, 510, 710):
        d.line(((x, 645), (x, 724)), fill=(7, 112, 215, 215), width=15)
        d.ellipse((x - 25, 706, x + 25, 756), fill=(214, 250, 255), outline=(0, 77, 199), width=9)
    cx, cy = 510, 465
    shape = gear_vertices(cx, cy)
    d.polygon([(x + 14, y + 16) for x, y in shape], fill=(0, 36, 91, 105))
    d.polygon(shape, fill=(0, 76, 180), outline=(4, 164, 255), width=9)
    d.ellipse((cx - 134, cy - 134, cx + 134, cy + 134), fill=(5, 89, 200), outline=(99, 218, 255), width=13)
    d.ellipse((cx - 105, cy - 105, cx + 105, cy + 105), fill=(228, 251, 255), outline=(0, 76, 186), width=12)
    d.polygon(((cx - 42, cy - 70), (cx - 42, cy + 70), (cx + 90, cy)), fill=(0, 101, 213))
    image.alpha_composite(details)
    return image


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    make_icon().save(OUTPUT, optimize=True)
    print(str(OUTPUT))
