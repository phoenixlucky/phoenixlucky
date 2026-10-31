"""Build the layered WebP artwork used by the profile README."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from collections.abc import Callable
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "readme" / "source"
OUTPUT = ROOT / "assets" / "readme"


def load_tokens() -> dict[str, str | int]:
    root = ET.parse(SOURCE / "profile-board.svg").getroot()
    view_box = [int(float(value)) for value in root.attrib["viewBox"].split()]
    tokens: dict[str, str | int] = {
        "width": view_box[2],
        "height": view_box[3],
    }
    for name, value in root.attrib.items():
        if name.startswith("data-"):
            key = name.removeprefix("data-")
            tokens[key] = int(value) if value.isdigit() else value
    return tokens


def font(size: int, bold: bool = False, chinese: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"]
        if chinese
        else [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf"]
    )
    if not bold:
        candidates = candidates[::-1]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def paste_round(base: Image.Image, image: Image.Image, box: tuple[int, int, int, int], radius: int) -> None:
    x, y, width, height = box
    image = image.copy().convert("RGBA")
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    left = x + (width - image.width) // 2
    top = y + (height - image.height) // 2
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius, fill=255)
    base.paste(image, (left, top), mask)


def card(layer: Image.Image, box: tuple[int, int, int, int], radius: int = 24, alpha: int = 228) -> None:
    draw = ImageDraw.Draw(layer)
    x, y, width, height = box
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius,
        fill=(255, 255, 255, alpha),
        outline=(255, 255, 255, 210),
        width=2,
    )


def flame(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    outer = [(x, y + 52 * scale), (x + 17 * scale, y + 24 * scale), (x + 19 * scale, y),
             (x + 39 * scale, y + 24 * scale), (x + 37 * scale, y + 52 * scale),
             (x + 20 * scale, y + 67 * scale)]
    inner = [(x + 12 * scale, y + 53 * scale), (x + 24 * scale, y + 31 * scale),
             (x + 29 * scale, y + 48 * scale), (x + 22 * scale, y + 62 * scale)]
    draw.polygon(outer, fill="#F35B2C")
    draw.polygon(inner, fill="#FFD44A")


def text_center(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt: ImageFont.ImageFont, fill: str) -> None:
    draw.text(xy, value, font=fnt, fill=fill, anchor="mm")


def background(size: tuple[int, int], source: Image.Image) -> Image.Image:
    width, height = size
    ratio = width / source.width
    resized = source.resize((width, round(source.height * ratio)), Image.Resampling.LANCZOS)
    if resized.height < height:
        resized = resized.resize((width, height), Image.Resampling.LANCZOS)
    top = max(0, (resized.height - height) // 3)
    return resized.crop((0, top, width, top + height)).convert("RGBA")


def board_background(size: tuple[int, int], source: Image.Image) -> Image.Image:
    width, height = size
    canvas = Image.new("RGBA", size, "#F8F8FF")
    scenic_height = min(height, 760)
    scenic = source.resize((width, scenic_height), Image.Resampling.LANCZOS).convert("RGBA")
    canvas.alpha_composite(scenic)
    fade = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(fade)
    for y in range(440, height):
        progress = min(1.0, (y - 440) / max(1, height - 440))
        draw.line((0, y, width, y), fill=(248, 248, 255, round(225 * progress)))
    canvas.alpha_composite(fade)
    return canvas


def build_hero(tokens: dict[str, str | int], copy: dict, bg: Image.Image, base: Image.Image | None = None) -> Image.Image:
    width = int(tokens["width"])
    canvas = base.copy() if base is not None else background((width, 360), bg)
    layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    gutter = int(tokens["gutter"])
    card(layer, (gutter, 16, width - 2 * gutter, 65), 18, 232)
    flame(draw, 62, 26, 0.45)
    draw.text((99, 48), copy["brand"], font=font(21, True), fill="#162B55", anchor="lm")
    nav_x = 322
    for label in copy["navigation"]:
        draw.text((nav_x, 49), label, font=font(13), fill="#294C8D", anchor="lm")
        nav_x += max(87, len(label) * 9 + 38)
    draw.rounded_rectangle((1202, 28, 1386, 68), 20, fill="#D94ED1")
    draw.text((1293, 48), "Rise from Chaos  →", font=font(13, True), fill="white", anchor="mm")
    text_center(draw, (width // 2, 155), copy["brand"], font(58, True), "#4C28BF")
    text_center(draw, (width // 2, 216), copy["tagline"], font(21, True), "#2452A4")
    text_center(draw, (width // 2, 253), copy["tagline_zh"], font(18, True, True), "#2452A4")
    text_center(draw, (width // 2, 297), copy["hero_kicker"], font(12, True), "#6E76AD")
    draw.text((68, 198), "Build\nA Clearer\nTomorrow", font=font(20), fill=(255, 255, 255, 235), spacing=3)
    canvas.alpha_composite(layer)
    return canvas


def build_identity(tokens: dict[str, str | int], copy: dict, bg: Image.Image, usachi: Image.Image, base: Image.Image | None = None) -> Image.Image:
    width = int(tokens["width"])
    canvas = base.copy() if base is not None else background((width, 300), bg)
    layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    card(layer, (196, 15, 1056, 270), 28, 224)
    paste_round(layer, usachi, (223, 37, 250, 225), 24)
    flame(draw, 520, 54, 0.55)
    draw.text((572, 84), copy["brand"].lower(), font=font(28, True), fill="#162B55", anchor="lm")
    draw.line((518, 113, 1136, 113), fill="#8396C2", width=2)
    draw.text((518, 141), copy["about_en"], font=font(17), fill="#162B55")
    draw.text((518, 173), copy["about_zh"], font=font(17, True, True), fill="#162B55")
    x = 520
    for index, role in enumerate(copy["roles"]):
        color = ["#D9ECFF", "#E8DEFF", "#FFDDF0", "#D7F7E9"][index]
        width_tag = 128 if index < 2 else 154
        draw.rounded_rectangle((x, 208, x + width_tag, 246), 19, fill=color)
        text_center(draw, (x + width_tag // 2, 227), role, font(12, True), "#3159AE")
        x += width_tag + 12
    canvas.alpha_composite(layer)
    return canvas


def build_metrics(tokens: dict[str, str | int], copy: dict, bg: Image.Image, base: Image.Image | None = None) -> Image.Image:
    width = int(tokens["width"])
    canvas = base.copy() if base is not None else background((width, 126), bg)
    draw = ImageDraw.Draw(canvas)
    labels = copy["metrics"]
    colors = ["#F447B5", "#7B61FF", "#10A998", "#F5772D", "#2B72D6"]
    gutter = int(tokens["gutter"])
    gap = 14
    item_width = (width - 2 * gutter - gap * (len(labels) - 1)) // len(labels)
    for index, (title, subtitle) in enumerate(labels):
        x = gutter + index * (item_width + gap)
        card(canvas, (x, 12, item_width, 93), 18, 238)
        draw.ellipse((x + 19, 33, x + 59, 73), fill=colors[index])
        text_center(draw, (x + 39, 53), str(index + 1), font(18, True), "white")
        draw.text((x + 75, 39), title, font=font(13, True), fill="#183460")
        draw.text((x + 75, 65), subtitle, font=font(11), fill="#6979A8")
    return canvas


def build_navigation(tokens: dict[str, str | int], copy: dict, base: Image.Image | None = None) -> Image.Image:
    width = int(tokens["width"])
    canvas = base.copy() if base is not None else Image.new("RGBA", (width, 112), "#F8F8FF")
    draw = ImageDraw.Draw(canvas)
    gutter = int(tokens["gutter"])
    card(canvas, (gutter, 12, width - 2 * gutter, 82), 20, 236)
    x = 74
    for index, label in enumerate(copy["navigation"]):
        if index == 0:
            draw.rounded_rectangle((x - 15, 29, x + 100, 70), 21, fill="#FBE1F7")
        draw.ellipse((x, 43, x + 14, 57), fill="#2756AE" if index else "#F447B5")
        draw.text((x + 27, 50), label, font=font(14, index == 0), fill="#C72595" if index == 0 else "#274C96", anchor="lm")
        x += max(133, len(label) * 9 + 55)
    draw.line((1218, 51, 1260, 51), fill="#7B61FF", width=2)
    draw.text((1275, 42), "GOOD TOOLS", font=font(10, True), fill="#7580B6")
    draw.text((1275, 61), "BRIGHTER PEOPLE", font=font(10), fill="#7580B6")
    return canvas


def build_about(tokens: dict[str, str | int], copy: dict, bg: Image.Image, base: Image.Image | None = None) -> Image.Image:
    width = int(tokens["width"])
    canvas = base.copy() if base is not None else Image.new("RGBA", (width, 310), "#F8F8FF")
    layer = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    gutter = int(tokens["gutter"])
    card(layer, (gutter, 14, width - 2 * gutter, 282), 28, 240)
    flame(draw, 72, 42, 0.58)
    draw.text((128, 74), copy["about_title"], font=font(28, True), fill="#162B55", anchor="lm")
    draw.text((128, 106), copy["about_subtitle"], font=font(15), fill="#7380B2", anchor="lm")
    draw.line((128, 130, 183, 130), fill="#F447B5", width=3)
    draw.text((1028, 82), "PEOPLE  ×  TOOLS  ×  A BRIGHTER TOMORROW", font=font(10, True), fill="#7580B6", anchor="lm")
    strip = background((width - 2 * gutter - 56, 120), bg).filter(ImageFilter.GaussianBlur(0.2))
    strip = strip.crop((0, 30, strip.width, 150))
    mask = Image.new("L", strip.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, strip.width - 1, strip.height - 1), 18, fill=255)
    layer.paste(strip, (gutter + 28, 151), mask)
    draw = ImageDraw.Draw(layer)
    draw.text((1070, 221), "Small Automation", font=font(16), fill="#4D4B7F")
    draw.text((1112, 245), "Big Freedom  ♡", font=font(16), fill="#4D4B7F")
    canvas.alpha_composite(layer)
    return canvas


def save_webp(image: Image.Image, name: str, quality: int = 90) -> None:
    target = OUTPUT / name
    image.convert("RGB").save(target, "WEBP", quality=quality, method=6)
    size = target.stat().st_size
    if size > 250_000:
        raise RuntimeError(f"{target.name} is {size} bytes; keep each visual asset below 250KB")
    print(f"{target.name}: {image.width}x{image.height}, {size} bytes")


def glow_layer(size: int, draw_shape: Callable[[ImageDraw.ImageDraw], None], blur: float) -> Image.Image:
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_shape(ImageDraw.Draw(layer))
    return layer.filter(ImageFilter.GaussianBlur(blur))


def gradient_rgba(size: int, start: str, end: str, angle: int = 0) -> Image.Image:
    gradient = Image.linear_gradient("L").resize((size, size))
    if angle:
        gradient = gradient.rotate(angle, expand=False)
    return ImageOps.colorize(gradient, start, end).convert("RGBA")


def vignette(image: Image.Image, strength: int = 46, color: tuple[int, int, int] = (76, 29, 149)) -> Image.Image:
    mask = Image.radial_gradient("L").resize(image.size)
    alpha = mask.point(lambda value: int(value * strength / 255))
    layer = Image.new("RGBA", image.size, color + (0,))
    layer.putalpha(alpha)
    return Image.alpha_composite(image.convert("RGBA"), layer)


def build_avatar(usachi: Image.Image) -> Image.Image:
    """Round the mascot into a pastel-ringed avatar with a soft glow."""
    size, diameter, pos = 320, 248, 36
    crop = usachi.crop((270, 30, 810, 570)).resize((232, 232), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(
        glow_layer(size, lambda draw: draw.ellipse((18, 18, 302, 302), fill=(244, 71, 181, 48)), 26)
    )
    canvas.alpha_composite(
        glow_layer(size, lambda draw: draw.ellipse((42, 54, 278, 290), fill=(76, 40, 191, 78)), 18)
    )
    ring = gradient_rgba(size, "#F9A8D4", "#C4B5FD")
    ring_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(ring_mask).ellipse((pos, pos, pos + diameter - 1, pos + diameter - 1), fill=255)
    canvas.paste(ring, (0, 0), ring_mask)
    ImageDraw.Draw(canvas).ellipse(
        (pos + 4, pos + 4, pos + diameter - 5, pos + diameter - 5), fill="#FFFFFF"
    )
    mask = Image.new("L", (232, 232), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 231, 231), fill=255)
    canvas.paste(crop, (pos + 8, pos + 8), mask)
    return canvas


def build_phoenix_card(phoenix: Image.Image) -> Image.Image:
    """Frame the phoenix artwork in a glowing pastel card."""
    size, card, pos = 440, 400, 20
    image = vignette(phoenix.resize((384, 384), Image.Resampling.LANCZOS))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(
        glow_layer(size, lambda draw: draw.rounded_rectangle((10, 10, 429, 429), 44, fill=(244, 71, 181, 42)), 28)
    )
    canvas.alpha_composite(
        glow_layer(size, lambda draw: draw.rounded_rectangle((30, 40, 429, 439), 40, fill=(76, 40, 191, 72)), 22)
    )
    rim = gradient_rgba(size, "#F9A8D4", "#C4B5FD", angle=45)
    rim_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(rim_mask).rounded_rectangle(
        (pos, pos, pos + card - 1, pos + card - 1), 36, fill=255
    )
    canvas.paste(rim, (0, 0), rim_mask)
    ImageDraw.Draw(canvas).rounded_rectangle(
        (pos + 4, pos + 4, pos + card - 5, pos + card - 5), 32, fill="#FFFFFF"
    )
    mask = Image.new("L", (384, 384), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 383, 383), 28, fill=255)
    canvas.paste(image, (pos + 8, pos + 8), mask)
    return canvas


def save_webp_alpha(image: Image.Image, name: str, quality: int = 92) -> None:
    target = OUTPUT / name
    image.save(target, "WEBP", quality=quality, method=6)
    size = target.stat().st_size
    if size > 100_000:
        raise RuntimeError(f"{target.name} is {size} bytes; keep alpha assets below 100KB")
    print(f"{target.name}: {image.width}x{image.height}, {size} bytes")


def build_profile_board(parts: list[Image.Image]) -> Image.Image:
    width = parts[0].width
    height = sum(part.height for part in parts)
    board = Image.new("RGBA", (width, height), "#F8F8FF")
    y = 0
    for part in parts:
        board.alpha_composite(part, (0, y))
        y += part.height
    return board


def main() -> None:
    tokens = load_tokens()
    copy = json.loads((SOURCE / "copy.json").read_text(encoding="utf-8"))
    bg = Image.open(SOURCE / "background.webp").convert("RGB")
    usachi = Image.open(SOURCE / "usachi.webp").convert("RGBA")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    section_heights = (360, 300, 126, 112)
    board_base = board_background((int(tokens["width"]), sum(section_heights)), bg)
    offsets = [0]
    for height in section_heights[:-1]:
        offsets.append(offsets[-1] + height)
    hero = build_hero(tokens, copy, bg, board_base.crop((0, offsets[0], int(tokens["width"]), offsets[0] + section_heights[0])))
    identity = build_identity(tokens, copy, bg, usachi, board_base.crop((0, offsets[1], int(tokens["width"]), offsets[1] + section_heights[1])))
    metrics = build_metrics(tokens, copy, bg, board_base.crop((0, offsets[2], int(tokens["width"]), offsets[2] + section_heights[2])))
    navigation = build_navigation(tokens, copy, board_base.crop((0, offsets[3], int(tokens["width"]), offsets[3] + section_heights[3])))
    about = build_about(tokens, copy, bg)
    board = build_profile_board([hero, identity, metrics, navigation])

    save_webp(board, "profile-board.webp", quality=88)
    save_webp(hero, "hero.webp")
    save_webp(identity, "identity-card.webp")
    save_webp(metrics, "metrics.webp")
    save_webp(navigation, "navigation.webp")
    save_webp(about, "about-banner.webp")
    phoenix = bg.crop((1450, 0, 2150, 700))
    save_webp(phoenix, "phoenix.webp")
    save_webp(usachi, "usachi.webp")
    save_webp_alpha(build_avatar(usachi), "usachi-avatar.webp")
    save_webp_alpha(build_phoenix_card(phoenix), "phoenix-card.webp", quality=91)


if __name__ == "__main__":
    main()
