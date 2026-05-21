from __future__ import annotations

import asyncio
import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from planner import Slide


SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080


def render_html_files(slides: list[Slide], project_dir: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    html_paths: list[Path] = []
    styles = (project_dir / "styles" / "ici-theme.css").read_text(encoding="utf-8") + "\n" + font_face_css(project_dir)
    for index, slide in enumerate(slides, start=1):
        layout_path = project_dir / "layouts" / f"{slide.layout}.html"
        if not layout_path.exists():
            raise FileNotFoundError(f"Missing layout template: {layout_path}")
        body = fill_template(layout_path.read_text(encoding="utf-8"), slide)
        doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{styles}</style></head><body>{body}</body></html>"
        path = out_dir / f"slide-{index:02d}.html"
        path.write_text(doc, encoding="utf-8")
        html_paths.append(path)
    return html_paths


def font_face_css(project_dir: Path) -> str:
    fonts = {
        300: "Alibaba-PuHuiTi-Light.otf",
        400: "Alibaba-PuHuiTi-Regular.otf",
        600: "Alibaba-PuHuiTi-Medium.otf",
        700: "Alibaba-PuHuiTi-Bold.otf",
        850: "Alibaba-PuHuiTi-Heavy.otf",
    }
    rules = []
    for weight, filename in fonts.items():
        path = project_dir / "fonts" / filename
        if path.exists():
            rules.append(
                '@font-face { font-family: "Alibaba PuHuiTi"; '
                f'src: url("{path.resolve().as_uri()}") format("opentype"); '
                f"font-weight: {weight}; font-style: normal; }}"
            )
    return "\n".join(rules)


def fill_template(template: str, slide: Slide) -> str:
    data = dict(slide.data)
    data["title"] = slide.title
    data.setdefault("subtitle", "")
    data.setdefault("meta", "")
    data.setdefault("kicker", "ICI Lab Report")
    data.setdefault("footer", "ICI Lab · Zhejiang University")
    data.setdefault("highlight", slide.title)

    if "items" in data:
        data["bullets"] = bullet_html(data["items"])
    data.setdefault("bullets", "")

    if slide.layout == "toc":
        data["toc_items"] = toc_html(data.get("items", []))
    if slide.layout == "two_column":
        data["left_items"] = bullet_html(data.get("left_items", []))
        data["right_items"] = bullet_html(data.get("right_items", []))
    if slide.layout == "process":
        steps = data.get("steps", [])
        data["step_count"] = max(1, min(4, len(steps)))
        data["steps"] = process_html(steps)
    if slide.layout == "summary":
        data["summary_cards"] = summary_cards_html(data.get("cards", []))
    if slide.layout == "image":
        data["figure_html"] = figure_html(data)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return str(data.get(key, ""))

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, template)


def bullet_html(items: Iterable[str]) -> str:
    return "".join(f"<li data-ppt='bullet'>{html.escape(str(item))}</li>" for item in items)


def toc_html(items: Iterable[str]) -> str:
    cells = []
    for idx, item in enumerate(items, start=1):
        cells.append(
            "<div data-ppt='group' data-ppt-role='toc-item' style='display:grid;grid-template-columns:92px 1fr;gap:24px;align-items:start;'>"
            f"<div data-ppt='text' data-ppt-role='toc-number' style='font-size:46px;font-weight:850;color:rgba(255,255,255,0.92);'>{idx:02d}</div>"
            f"<div data-ppt='text' data-ppt-role='toc-title' style='font-size:34px;line-height:1.3;color:rgba(255,255,255,0.86);font-weight:650;padding-top:7px;'>{html.escape(str(item))}</div>"
            "</div>"
        )
    return "".join(cells)


def process_html(steps: Iterable[str]) -> str:
    cards = []
    for idx, step in enumerate(list(steps)[:4], start=1):
        cards.append(
            "<div data-ppt='card' class='card' style='min-height:300px;padding:34px;border-top:8px solid var(--ici-main-blue);'>"
            f"<div data-ppt='text' data-ppt-role='process-number' style='font-size:42px;font-weight:850;color:var(--ici-main-blue);margin-bottom:28px;'>{idx:02d}</div>"
            f"<div data-ppt='text' data-ppt-role='process-step' style='font-size:30px;line-height:1.34;font-weight:700;color:var(--ici-deep-blue);'>{html.escape(str(step))}</div>"
            "</div>"
        )
    return "".join(cards)


def summary_cards_html(cards: Iterable[tuple[str, str]]) -> str:
    html_cards = []
    for title, body in list(cards)[:3]:
        html_cards.append(
            "<div data-ppt='card' class='card' style='height:438px;padding:42px;border-top:8px solid var(--ici-cyan-green);'>"
            f"<h2 data-ppt='text' data-ppt-role='summary-title' style='font-size:36px;margin:0 0 30px;color:var(--ici-main-blue);'>{html.escape(title)}</h2>"
            f"<p data-ppt='text' data-ppt-role='summary-body' style='font-size:31px;line-height:1.35;margin:0;color:var(--ici-dark-text);font-weight:620;'>{html.escape(body)}</p>"
            "</div>"
        )
    return "".join(html_cards)


def figure_html(data: dict) -> str:
    figure_path = str(data.get("figure_path", "")).strip()
    if figure_path:
        src = Path(figure_path).resolve().as_uri()
        caption = html.escape(str(data.get("figure_caption") or data.get("figure_note") or "Paper figure"))
        return (
            f"<img data-ppt='image' data-ppt-role='paper-figure' src='{src}' "
            "style='max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain;display:block;' />"
            f"<div data-ppt='text' data-ppt-role='figure-caption' "
            "style='position:absolute;left:34px;bottom:26px;width:1032px;font-size:20px;line-height:1.25;color:#64748B;'>"
            f"{caption}</div>"
        )
    return (
        "<div style='text-align:center;color:#64748B;'>"
        f"<div data-ppt='text' data-ppt-role='figure-title' style='font-size:42px;font-weight:800;color:var(--ici-deep-blue);'>{html.escape(str(data.get('figure_title', 'Figure / Prototype / Result')))}</div>"
        f"<div data-ppt='text' data-ppt-role='figure-note' style='font-size:28px;margin-top:22px;'>{html.escape(str(data.get('figure_note', 'Replace this placeholder with a diagram, experiment image, or system screenshot.')))}</div>"
        "</div>"
    )


def render_pngs(html_paths: list[Path], png_dir: Path, slides: list[Slide] | None = None, renderer: str = "auto") -> list[Path]:
    png_dir.mkdir(parents=True, exist_ok=True)
    if renderer == "pil":
        if slides is None:
            raise ValueError("Pillow fallback requires slide data.")
        return render_with_pillow(slides, png_dir)
    try:
        import playwright.async_api  # type: ignore
    except Exception:
        try:
            return render_with_chrome_cli(html_paths, png_dir)
        except Exception as exc:
            if slides is None or renderer == "browser":
                raise
            print(f"HTML browser rendering unavailable, using Pillow fallback: {exc}")
            return render_with_pillow(slides, png_dir)
    return asyncio.run(render_with_playwright(html_paths, png_dir))


async def render_with_playwright(html_paths: list[Path], png_dir: Path) -> list[Path]:
    from playwright.async_api import async_playwright

    png_paths: list[Path] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT}, device_scale_factor=1)
        for html_path in html_paths:
            out = png_dir / f"{html_path.stem}.png"
            await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            await page.screenshot(path=str(out), full_page=False)
            png_paths.append(out)
        await browser.close()
    return png_paths


def render_with_chrome_cli(html_paths: list[Path], png_dir: Path) -> list[Path]:
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("No renderer available. Install Playwright Chromium or Google Chrome/Chromium.")

    png_paths: list[Path] = []
    for idx, html_path in enumerate(html_paths, start=1):
        out = png_dir / f"{html_path.stem}.png"
        user_data = Path(tempfile.mkdtemp(prefix=f"ici-ppt-chrome-{idx}-"))
        try:
            run_chrome_screenshot(chrome, user_data, html_path, out)
        finally:
            shutil.rmtree(user_data, ignore_errors=True)
        png_paths.append(out)
    return png_paths


def run_chrome_screenshot(chrome: str, user_data: Path, html_path: Path, out: Path) -> None:
    common_flags = [
        "--disable-gpu",
        "--no-first-run",
        "--no-sandbox",
        "--disable-background-networking",
        "--disable-extensions",
        "--hide-scrollbars",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=1000",
        f"--user-data-dir={user_data}",
        f"--window-size={SLIDE_WIDTH},{SLIDE_HEIGHT}",
        f"--screenshot={out}",
        html_path.resolve().as_uri(),
    ]
    attempts = [["--headless=new"], ["--headless"]]
    last_error: str | None = None
    for headless_flag in attempts:
        cmd = [chrome, *headless_flag, *common_flags]
        try:
            completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
            if out.exists():
                return
            last_error = completed.stderr.decode("utf-8", errors="ignore")
        except subprocess.TimeoutExpired:
            last_error = f"Chrome screenshot timed out for {html_path.name}"
        except subprocess.CalledProcessError as exc:
            last_error = exc.stderr.decode("utf-8", errors="ignore") or str(exc)
    raise RuntimeError(last_error or f"Chrome screenshot failed for {html_path}")


def find_chrome() -> str | None:
    candidates = [
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def render_with_pillow(slides: list[Slide], png_dir: Path) -> list[Path]:
    from PIL import Image, ImageDraw, ImageFont

    png_paths: list[Path] = []
    fonts = load_fonts()
    for idx, slide in enumerate(slides, start=1):
        img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), "white")
        draw = ImageDraw.Draw(img)
        if slide.layout in {"cover", "toc", "section", "closing"}:
            draw_gradient(draw)
            draw.text((120, 72), "ICI Lab · Zhejiang University", fill=(255, 255, 255), font=fonts["small_bold"])
            draw_tri_squares(draw, gradient=True)
        else:
            draw.rectangle((0, 0, SLIDE_WIDTH, SLIDE_HEIGHT), fill=(248, 250, 252))
            draw.text((120, 72), "ICI Lab", fill=(27, 20, 100), font=fonts["small_bold"])
            draw_tri_squares(draw, gradient=False)

        if slide.layout == "cover":
            draw_wrapped(draw, slide.title, (120, 285), 1260, fonts["hero"], (255, 255, 255), 96)
            draw_wrapped(draw, slide.data.get("subtitle", ""), (120, 535), 1220, fonts["subtitle"], (230, 245, 255), 48)
            draw.text((120, 930), slide.data.get("meta", ""), fill=(220, 240, 255), font=fonts["body"])
        elif slide.layout == "toc":
            draw.text((120, 180), "Contents", fill=(255, 255, 255), font=fonts["title"])
            x_positions = [120, 980]
            for i, item in enumerate(slide.data.get("items", []), start=1):
                x = x_positions[(i - 1) % 2]
                y = 330 + ((i - 1) // 2) * 120
                draw.text((x, y), f"{i:02d}", fill=(255, 255, 255), font=fonts["toc_no"])
                draw_wrapped(draw, str(item), (x + 110, y + 8), 620, fonts["toc"], (235, 250, 255), 42)
        elif slide.layout == "section":
            draw.text((120, 250), slide.data.get("section_no", "01"), fill=(255, 255, 255), font=fonts["giant"])
            draw_wrapped(draw, slide.title, (120, 455), 1220, fonts["title"], (255, 255, 255), 84)
            draw_wrapped(draw, slide.data.get("subtitle", ""), (120, 650), 1120, fonts["subtitle"], (225, 245, 255), 46)
        elif slide.layout == "closing":
            draw_wrapped(draw, slide.title, (120, 245), 1320, fonts["title"], (255, 255, 255), 84)
            draw_wrapped(draw, slide.data.get("message", ""), (120, 470), 1180, fonts["subtitle"], (230, 245, 255), 50)
            draw.text((120, 900), slide.data.get("contact", ""), fill=(225, 245, 255), font=fonts["body"])
        else:
            draw_content_like(draw, slide, fonts)

        out = png_dir / f"slide-{idx:02d}.png"
        img.save(out)
        png_paths.append(out)
    return png_paths


def load_fonts():
    from PIL import ImageFont

    project_fonts = Path(__file__).resolve().parents[1] / "fonts"
    candidates = [
        str(project_fonts / "Alibaba-PuHuiTi-Regular.otf"),
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    def font(size: int, preferred: str = "Alibaba-PuHuiTi-Regular.otf"):
        preferred_path = project_fonts / preferred
        for path in [str(preferred_path), *candidates]:
            if Path(path).exists():
                return ImageFont.truetype(path, size=size)
        return ImageFont.load_default()

    return {
        "hero": font(88, "Alibaba-PuHuiTi-Heavy.otf"),
        "title": font(76, "Alibaba-PuHuiTi-Heavy.otf"),
        "content_title": font(52, "Alibaba-PuHuiTi-Heavy.otf"),
        "subtitle": font(34, "Alibaba-PuHuiTi-Regular.otf"),
        "body": font(30, "Alibaba-PuHuiTi-Regular.otf"),
        "small_bold": font(24, "Alibaba-PuHuiTi-Bold.otf"),
        "toc_no": font(46, "Alibaba-PuHuiTi-Heavy.otf"),
        "toc": font(34, "Alibaba-PuHuiTi-Bold.otf"),
        "giant": font(190, "Alibaba-PuHuiTi-Heavy.otf"),
    }


def draw_gradient(draw) -> None:
    c1 = (37, 20, 138)
    c2 = (0, 111, 214)
    c3 = (102, 230, 195)
    for y in range(SLIDE_HEIGHT):
        for x in range(0, SLIDE_WIDTH, 4):
            t = (x / SLIDE_WIDTH * 0.65) + (y / SLIDE_HEIGHT * 0.35)
            if t < 0.48:
                k = t / 0.48
                color = lerp(c1, c2, k)
            else:
                k = (t - 0.48) / 0.52
                color = lerp(c2, c3, k)
            draw.rectangle((x, y, x + 3, y), fill=color)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_tri_squares(draw, gradient: bool) -> None:
    colors = [(255, 255, 255), (230, 245, 255), (205, 235, 235)] if gradient else [(37, 20, 138), (0, 111, 214), (102, 230, 195)]
    for i, color in enumerate(colors):
        x = 1710 + i * 40
        draw.rectangle((x, 988, x + 28, 1016), fill=color)


def draw_content_like(draw, slide: Slide, fonts) -> None:
    draw.text((120, 74), slide.data.get("kicker", "ICI Lab Report"), fill=(0, 111, 214), font=fonts["small_bold"])
    draw_wrapped(draw, slide.title, (120, 110), 1260, fonts["content_title"], (27, 20, 100), 58)
    draw.rectangle((120, 198, 270, 204), fill=(0, 111, 214))
    items = slide.data.get("items", [])
    if slide.layout == "two_column":
        draw_card(draw, (120, 290, 910, 850), slide.data.get("left_title", "Challenge"), slide.data.get("left_items", []), fonts)
        draw_card(draw, (1010, 290, 1800, 850), slide.data.get("right_title", "Response"), slide.data.get("right_items", []), fonts)
    elif slide.layout == "process":
        steps = slide.data.get("steps", [])[:4]
        for i, step in enumerate(steps):
            x0 = 120 + i * 425
            draw_card(draw, (x0, 336, x0 + 390, 650), f"{i+1:02d}", [step], fonts)
        draw_wrapped(draw, slide.data.get("note", ""), (120, 790), 1180, fonts["body"], (75, 85, 99), 42)
    elif slide.layout == "image":
        draw.rectangle((120, 282, 1220, 892), fill=(238, 246, 255), outline=(221, 231, 243), width=2)
        draw_wrapped(draw, slide.data.get("figure_title", "Figure"), (360, 520), 620, fonts["content_title"], (27, 20, 100), 58)
        draw_bullets(draw, items, (1320, 330), 430, fonts)
    elif slide.layout == "summary":
        for i, card in enumerate(slide.data.get("cards", [])[:3]):
            x0 = 120 + i * 570
            draw_card(draw, (x0, 298, x0 + 530, 736), card[0], [card[1]], fonts)
    else:
        draw_bullets(draw, items, (120, 280), 1180, fonts)
        draw_card(draw, (1420, 280, 1800, 700), "Key Point", [slide.data.get("highlight", slide.title)], fonts)
    draw.text((120, 998), slide.data.get("footer", "ICI Lab · Zhejiang University"), fill=(100, 116, 139), font=fonts["small_bold"])


def draw_card(draw, box, title, items, fonts) -> None:
    draw.rectangle(box, fill=(255, 255, 255), outline=(221, 231, 243), width=2)
    x0, y0, x1, _ = box
    draw_wrapped(draw, str(title), (x0 + 34, y0 + 34), x1 - x0 - 68, fonts["subtitle"], (27, 20, 100), 44)
    draw_bullets(draw, items, (x0 + 34, y0 + 130), x1 - x0 - 68, fonts, max_items=3)


def draw_bullets(draw, items, pos, width, fonts, max_items: int = 5) -> None:
    x, y = pos
    for item in list(items)[:max_items]:
        draw.rectangle((x, y + 14, x + 12, y + 26), fill=(0, 111, 214))
        used = draw_wrapped(draw, str(item), (x + 32, y), width - 32, fonts["body"], (17, 24, 39), 40)
        y += max(52, used + 20)


def draw_wrapped(draw, text: str, pos, max_width: int, font, fill, line_height: int) -> int:
    x, y = pos
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if draw.textlength(trial, font=font) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    for i, line in enumerate(lines[:7]):
        draw.text((x, y + i * line_height), line, fill=fill, font=font)
    return min(len(lines), 7) * line_height
