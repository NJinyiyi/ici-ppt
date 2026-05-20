from __future__ import annotations

from pathlib import Path
from typing import Iterable

from planner import Slide


FONT_LIGHT = "Alibaba PuHuiTi Light"
FONT_REGULAR = "Alibaba PuHuiTi"
FONT_MEDIUM = "Alibaba PuHuiTi Medium"
FONT_BOLD = "Alibaba PuHuiTi Bold"
FONT_HEAVY = "Alibaba PuHuiTi Heavy"

DEEP_BLUE = "1B1464"
PURPLE_BLUE = "25148A"
MAIN_BLUE = "006FD6"
CYAN_GREEN = "66E6C3"
DARK_TEXT = "111827"
SECONDARY_TEXT = "4B5563"
LIGHT_BG = "F8FAFC"
WHITE = "FFFFFF"
SOFT_LINE = "DDE7F3"


def build_editable_pptx(slides: list[Slide], output_path: Path, title: str) -> Path:
    """Build a stable editable deck using python-pptx native shapes and text."""
    if not slides:
        raise ValueError("No slides supplied for editable PPTX generation.")

    from pptx import Presentation
    from pptx.util import Inches

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    prs.core_properties.title = title
    prs.core_properties.author = "ici-ppt"
    prs.core_properties.last_modified_by = "ici-ppt"

    blank = prs.slide_layouts[6]
    for slide_model in slides:
        slide = prs.slides.add_slide(blank)
        draw_slide(slide, slide_model)

    prs.save(output_path)
    return output_path


def draw_slide(slide, model: Slide) -> None:
    layout = model.layout
    if layout in {"cover", "toc", "section", "closing"}:
        draw_gradient_background(slide)
        add_text(slide, "ICI Lab · Zhejiang University", 120, 72, 760, 38, 18, WHITE, FONT_BOLD)
        add_tri_squares(slide, gradient=True)
    else:
        add_rect(slide, 0, 0, 1920, 1080, LIGHT_BG, no_line=True)
        add_text(slide, "ICI Lab", 120, 72, 260, 34, 18, DEEP_BLUE, FONT_BOLD)
        add_tri_squares(slide, gradient=False)

    if layout == "cover":
        add_text(slide, model.title, 120, 286, 1280, 240, 52, WHITE, FONT_HEAVY)
        add_text(slide, model.data.get("subtitle", ""), 120, 548, 1210, 88, 25, "E6F5FF", FONT_REGULAR)
        add_text(slide, model.data.get("meta", ""), 120, 930, 980, 46, 19, "DCEFFF", FONT_REGULAR)
    elif layout == "toc":
        add_text(slide, "Contents", 120, 176, 640, 92, 48, WHITE, FONT_HEAVY)
        draw_toc(slide, model.data.get("items", []))
    elif layout == "section":
        add_text(slide, model.data.get("section_no", "01"), 120, 236, 500, 190, 104, WHITE, FONT_HEAVY)
        add_text(slide, model.title, 120, 456, 1220, 174, 46, WHITE, FONT_HEAVY)
        add_text(slide, model.data.get("subtitle", ""), 120, 656, 1120, 80, 24, "E1F5FF", FONT_REGULAR)
    elif layout == "closing":
        add_text(slide, model.title, 120, 245, 1370, 180, 50, WHITE, FONT_HEAVY)
        add_text(slide, model.data.get("message", ""), 120, 470, 1180, 180, 26, "E6F5FF", FONT_REGULAR)
        add_text(slide, model.data.get("contact", ""), 120, 900, 980, 48, 20, "E1F5FF", FONT_REGULAR)
    else:
        draw_content_header(slide, model)
        draw_body(slide, model)
        add_text(slide, model.data.get("footer", "ICI Lab · Zhejiang University"), 120, 998, 700, 32, 16, "64748B", FONT_REGULAR)


def draw_content_header(slide, model: Slide) -> None:
    add_text(slide, model.data.get("kicker", "ICI Lab Report"), 120, 74, 640, 30, 16, MAIN_BLUE, FONT_BOLD)
    add_text(slide, model.title, 120, 108, 1260, 94, 34, DEEP_BLUE, FONT_HEAVY)
    add_rect(slide, 120, 198, 150, 6, MAIN_BLUE, no_line=True)


def draw_body(slide, model: Slide) -> None:
    if model.layout == "two_column":
        add_card(slide, 120, 290, 790, 560, model.data.get("left_title", "Challenge"), model.data.get("left_items", []))
        add_card(slide, 1010, 290, 790, 560, model.data.get("right_title", "Response"), model.data.get("right_items", []), accent=CYAN_GREEN)
    elif model.layout == "process":
        steps = model.data.get("steps", [])[:4]
        for idx, step in enumerate(steps, start=1):
            add_card(slide, 120 + (idx - 1) * 425, 336, 390, 300, f"{idx:02d}", [step], accent=MAIN_BLUE)
        add_text(slide, model.data.get("note", ""), 120, 790, 1180, 90, 22, SECONDARY_TEXT, FONT_REGULAR)
    elif model.layout == "image":
        add_rect(slide, 120, 282, 1100, 610, "EEF6FF", line=SOFT_LINE)
        add_text(slide, model.data.get("figure_title", "Figure / Prototype / Result"), 310, 518, 720, 72, 30, DEEP_BLUE, FONT_HEAVY, align="center")
        add_text(slide, model.data.get("figure_note", ""), 300, 604, 760, 58, 19, SECONDARY_TEXT, FONT_REGULAR, align="center")
        add_bullets(slide, model.data.get("items", []), 1320, 330, 430, 430, 22)
    elif model.layout == "summary":
        for idx, card in enumerate(model.data.get("cards", [])[:3]):
            card_title, body = card
            add_card(slide, 120 + idx * 570, 298, 530, 438, card_title, [body], accent=CYAN_GREEN)
    else:
        add_bullets(slide, model.data.get("items", []), 120, 280, 1180, 520, 23)
        add_card(slide, 1420, 280, 380, 420, "Key Point", [model.data.get("highlight", model.title)], accent=MAIN_BLUE)


def draw_toc(slide, items: Iterable[str]) -> None:
    for idx, item in enumerate(list(items)[:6], start=1):
        col = 0 if idx <= 3 else 1
        row = idx - 1 if idx <= 3 else idx - 4
        x = 120 + col * 860
        y = 330 + row * 120
        add_text(slide, f"{idx:02d}", x, y, 90, 62, 30, WHITE, FONT_HEAVY)
        add_text(slide, str(item), x + 110, y + 6, 620, 80, 25, "EBFAFF", FONT_BOLD)


def draw_gradient_background(slide) -> None:
    add_gradient_rect(
        slide,
        0,
        0,
        1920,
        1080,
        stops=[(0, PURPLE_BLUE), (48000, MAIN_BLUE), (100000, CYAN_GREEN)],
        angle=135,
    )


def add_tri_squares(slide, gradient: bool) -> None:
    colors = [WHITE, "E6F5FF", "CDEBEB"] if gradient else [PURPLE_BLUE, MAIN_BLUE, CYAN_GREEN]
    for idx, color in enumerate(colors):
        add_rect(slide, 1710 + idx * 40, 988, 28, 28, color, no_line=True)


def add_card(slide, x: int, y: int, w: int, h: int, title: str, items: Iterable[str], accent: str | None = None) -> None:
    add_rect(slide, x, y, w, h, WHITE, line=SOFT_LINE)
    if accent:
        add_rect(slide, x, y, w, 8, accent, no_line=True)
    add_text(slide, str(title), x + 34, y + 34, w - 68, 70, 26, DEEP_BLUE, FONT_HEAVY)
    add_bullets(slide, list(items)[:4], x + 34, y + 132, w - 68, h - 160, 21)


def add_bullets(slide, items: Iterable[str], x: int, y: int, w: int, h: int, size: int) -> None:
    text = "\n".join(f"• {item}" for item in list(items)[:5])
    add_text(slide, text, x, y, w, h, size, DARK_TEXT, FONT_REGULAR, line_spacing=1.18)


def add_rect(slide, x: int, y: int, w: int, h: int, fill: str, line: str | None = None, no_line: bool = False):
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.dml.color import RGBColor

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if no_line:
        shape.line.fill.background()
    elif line:
        shape.line.color.rgb = RGBColor.from_string(line)
        shape.line.width = px(1)
    else:
        shape.line.fill.background()
    return shape


def add_gradient_rect(slide, x: int, y: int, w: int, h: int, stops: list[tuple[int, str]], angle: int = 135):
    shape = add_rect(slide, x, y, w, h, stops[0][1], no_line=True)
    apply_gradient_fill(shape, stops, angle)
    return shape


def apply_gradient_fill(shape, stops: list[tuple[int, str]], angle: int) -> None:
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.oxml.ns import qn

    sp_pr = shape._element.spPr
    for fill_tag in ("a:solidFill", "a:gradFill", "a:noFill", "a:pattFill", "a:blipFill"):
        node = sp_pr.find(qn(fill_tag))
        if node is not None:
            sp_pr.remove(node)

    grad_fill = OxmlElement("a:gradFill")
    grad_fill.set("rotWithShape", "1")

    gs_lst = OxmlElement("a:gsLst")
    for position, color in stops:
        gs = OxmlElement("a:gs")
        gs.set("pos", str(position))
        srgb = OxmlElement("a:srgbClr")
        srgb.set("val", color)
        gs.append(srgb)
        gs_lst.append(gs)
    grad_fill.append(gs_lst)

    lin = OxmlElement("a:lin")
    lin.set("ang", str(angle * 60000))
    lin.set("scaled", "1")
    grad_fill.append(lin)

    children = list(sp_pr)
    ln = sp_pr.find(qn("a:ln"))
    if ln is not None:
        sp_pr.insert(children.index(ln), grad_fill)
    else:
        sp_pr.append(grad_fill)


def add_text(
    slide,
    text: str,
    x: int,
    y: int,
    w: int,
    h: int,
    size: int,
    color: str,
    font_name: str,
    align: str = "left",
    line_spacing: float | None = None,
):
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
    from pptx.util import Pt

    box = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.margin_left = Pt(0)
    tf.margin_right = Pt(0)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)

    lines = str(text).splitlines() or [""]
    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = ""
        p.alignment = PP_ALIGN.CENTER if align == "center" else PP_ALIGN.LEFT
        if line_spacing:
            p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font_name
        run.font.size = Pt(size)
        run.font.color.rgb = RGBColor.from_string(color)
        if font_name in {FONT_BOLD, FONT_HEAVY}:
            run.font.bold = True
        set_east_asian_font(run, font_name)
    return box


def set_east_asian_font(run, font_name: str) -> None:
    from pptx.oxml.xmlchemy import OxmlElement
    from pptx.oxml.ns import qn

    r_pr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        node = r_pr.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            r_pr.append(node)
        node.set("typeface", font_name)


def px(value: float):
    from pptx.util import Inches

    return Inches(value / 144)
