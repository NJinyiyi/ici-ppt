from __future__ import annotations

import zipfile
from pathlib import Path

from planner import Slide
from pptx_builder import (
    SLIDE_CX,
    SLIDE_CY,
    app_props,
    core_props,
    escape_xml,
    presentation_rels,
    presentation_xml,
    root_rels,
    slide_layout_rels,
    slide_layout_xml,
    slide_master_rels,
    slide_master_xml,
    theme_xml,
)


EMU_PER_PX = 6350

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
    if not slides:
        raise ValueError("No slides supplied for editable PPTX generation.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types(len(slides)))
        z.writestr("_rels/.rels", root_rels())
        z.writestr("docProps/core.xml", core_props(title))
        z.writestr("docProps/app.xml", app_props(len(slides)))
        z.writestr("ppt/presentation.xml", presentation_xml(len(slides)))
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels(len(slides)))
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels())
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels())
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        for idx, slide in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{idx}.xml", editable_slide_xml(slide))
            z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", editable_slide_rels())
    return output_path


def content_types(count: int) -> str:
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, count + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>'''


def editable_slide_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''


def editable_slide_xml(slide: Slide) -> str:
    shape_id = 2
    parts: list[str] = []
    if slide.layout in {"cover", "toc", "section", "closing"}:
        parts.extend(gradient_background(shape_id))
        shape_id += 4
        parts.append(textbox(shape_id, 120, 72, 760, 40, "ICI Lab · Zhejiang University", 18, WHITE, bold=True))
        shape_id += 1
        parts.extend(tri_squares(shape_id, gradient=True))
        shape_id += 3
    else:
        parts.append(rect(shape_id, 0, 0, 1920, 1080, LIGHT_BG, line="none"))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 72, 320, 34, "ICI Lab", 18, DEEP_BLUE, bold=True))
        shape_id += 1
        parts.extend(tri_squares(shape_id, gradient=False))
        shape_id += 3

    if slide.layout == "cover":
        parts.append(textbox(shape_id, 120, 285, 1280, 220, slide.title, 52, WHITE, bold=True))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 535, 1220, 100, slide.data.get("subtitle", ""), 25, "E6F5FF"))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 930, 980, 46, slide.data.get("meta", ""), 19, "DCF0FF"))
    elif slide.layout == "toc":
        parts.append(textbox(shape_id, 120, 178, 640, 86, "Contents", 48, WHITE, bold=True))
        shape_id += 1
        for idx, item in enumerate(slide.data.get("items", [])[:6], start=1):
            col = 0 if idx <= 3 else 1
            row = idx - 1 if idx <= 3 else idx - 4
            x = 120 + col * 860
            y = 330 + row * 120
            parts.append(textbox(shape_id, x, y, 90, 62, f"{idx:02d}", 30, WHITE, bold=True))
            shape_id += 1
            parts.append(textbox(shape_id, x + 110, y + 6, 620, 80, str(item), 25, "EBFAFF", bold=True))
            shape_id += 1
    elif slide.layout == "section":
        parts.append(textbox(shape_id, 120, 240, 520, 190, slide.data.get("section_no", "01"), 104, WHITE, bold=True))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 455, 1220, 190, slide.title, 46, WHITE, bold=True))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 650, 1120, 90, slide.data.get("subtitle", ""), 24, "E1F5FF"))
    elif slide.layout == "closing":
        parts.append(textbox(shape_id, 120, 245, 1370, 190, slide.title, 50, WHITE, bold=True))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 470, 1180, 180, slide.data.get("message", ""), 26, "E6F5FF"))
        shape_id += 1
        parts.append(textbox(shape_id, 120, 900, 980, 46, slide.data.get("contact", ""), 20, "E1F5FF"))
    else:
        parts.extend(content_header(shape_id, slide))
        shape_id += 3
        body, shape_id = body_layout(shape_id, slide)
        parts.extend(body)
        parts.append(textbox(shape_id, 120, 998, 700, 32, slide.data.get("footer", "ICI Lab · Zhejiang University"), 16, "64748B"))

    return slide_shell("\n".join(parts))


def content_header(shape_id: int, slide: Slide) -> list[str]:
    return [
        textbox(shape_id, 120, 74, 640, 30, slide.data.get("kicker", "ICI Lab Report"), 16, MAIN_BLUE, bold=True),
        textbox(shape_id + 1, 120, 110, 1260, 90, slide.title, 34, DEEP_BLUE, bold=True),
        rect(shape_id + 2, 120, 198, 150, 6, MAIN_BLUE, line="none"),
    ]


def body_layout(shape_id: int, slide: Slide) -> tuple[list[str], int]:
    if slide.layout == "two_column":
        parts = [
            card(shape_id, 120, 290, 790, 560, slide.data.get("left_title", "Challenge"), slide.data.get("left_items", [])),
            card(shape_id + 1, 1010, 290, 790, 560, slide.data.get("right_title", "Response"), slide.data.get("right_items", []), accent=CYAN_GREEN),
        ]
        return parts, shape_id + 2
    if slide.layout == "process":
        parts = []
        for idx, step in enumerate(slide.data.get("steps", [])[:4], start=1):
            parts.append(card(shape_id, 120 + (idx - 1) * 425, 336, 390, 300, f"{idx:02d}", [step], accent=MAIN_BLUE))
            shape_id += 1
        parts.append(textbox(shape_id, 120, 790, 1180, 90, slide.data.get("note", ""), 22, SECONDARY_TEXT))
        return parts, shape_id + 1
    if slide.layout == "image":
        return [
            rect(shape_id, 120, 282, 1100, 610, "EEF6FF", line=SOFT_LINE),
            textbox(shape_id + 1, 320, 520, 700, 62, slide.data.get("figure_title", "Figure / Prototype / Result"), 30, DEEP_BLUE, bold=True),
            textbox(shape_id + 2, 360, 600, 640, 54, slide.data.get("figure_note", ""), 19, SECONDARY_TEXT),
            bullet_box(shape_id + 3, 1320, 330, 430, 430, slide.data.get("items", [])),
        ], shape_id + 4
    if slide.layout == "summary":
        parts = []
        for idx, item in enumerate(slide.data.get("cards", [])[:3]):
            title, body = item
            parts.append(card(shape_id, 120 + idx * 570, 298, 530, 438, title, [body], accent=CYAN_GREEN))
            shape_id += 1
        return parts, shape_id
    return [
        bullet_box(shape_id, 120, 280, 1180, 520, slide.data.get("items", [])),
        card(shape_id + 1, 1420, 280, 380, 420, "Key Point", [slide.data.get("highlight", slide.title)], accent=MAIN_BLUE),
    ], shape_id + 2


def gradient_background(shape_id: int) -> list[str]:
    return [
        rect(shape_id, 0, 0, 1920, 1080, PURPLE_BLUE, line="none"),
        rect(shape_id + 1, 620, 0, 800, 1080, MAIN_BLUE, line="none"),
        rect(shape_id + 2, 1320, 0, 600, 1080, CYAN_GREEN, line="none"),
        rect(shape_id + 3, 0, 0, 1920, 1080, "000000", alpha=86000, line="none"),
    ]


def tri_squares(shape_id: int, gradient: bool) -> list[str]:
    colors = [WHITE, "E6F5FF", "CDEBEB"] if gradient else [PURPLE_BLUE, MAIN_BLUE, CYAN_GREEN]
    return [rect(shape_id + idx, 1710 + idx * 40, 988, 28, 28, color, line="none") for idx, color in enumerate(colors)]


def card(shape_id: int, x: int, y: int, w: int, h: int, title: str, items: list[str], accent: str | None = None) -> str:
    parts = [rect(shape_id, x, y, w, h, WHITE, line=SOFT_LINE)]
    if accent:
        parts.append(rect(shape_id + 1000, x, y, w, 8, accent, line="none"))
    parts.append(textbox(shape_id + 2000, x + 34, y + 34, w - 68, 64, str(title), 26, DEEP_BLUE, bold=True))
    parts.append(bullet_box(shape_id + 3000, x + 34, y + 130, w - 68, h - 160, items[:4]))
    return "\n".join(parts)


def bullet_box(shape_id: int, x: int, y: int, w: int, h: int, items: list[str]) -> str:
    text = "\n".join(f"• {item}" for item in items[:5])
    return textbox(shape_id, x, y, w, h, text, 22, DARK_TEXT)


def rect(shape_id: int, x: int, y: int, w: int, h: int, fill: str, line: str | None = SOFT_LINE, alpha: int | None = None) -> str:
    alpha_xml = f'<a:alpha val="{alpha}"/>' if alpha else ""
    line_xml = "<a:ln><a:noFill/></a:ln>" if line == "none" else f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{line or SOFT_LINE}"/></a:solidFill></a:ln>'
    return f'''<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="Shape {shape_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{px(x)}" y="{px(y)}"/><a:ext cx="{px(w)}" cy="{px(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}">{alpha_xml}</a:srgbClr></a:solidFill>{line_xml}</p:spPr>
</p:sp>'''


def textbox(shape_id: int, x: int, y: int, w: int, h: int, text: str, size: int, color: str, bold: bool = False) -> str:
    paragraphs = []
    for line in str(text).splitlines() or [""]:
        paragraphs.append(paragraph(line, size, color, bold))
    return f'''<p:sp>
  <p:nvSpPr><p:cNvPr id="{shape_id}" name="Text {shape_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="{px(x)}" y="{px(y)}"/><a:ext cx="{px(w)}" cy="{px(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
  <p:txBody><a:bodyPr wrap="square" anchor="t"><a:spAutoFit/></a:bodyPr><a:lstStyle/>{"".join(paragraphs)}</p:txBody>
</p:sp>'''


def paragraph(text: str, size: int, color: str, bold: bool) -> str:
    b = ' b="1"' if bold else ""
    return f'''<a:p><a:r><a:rPr lang="zh-CN" sz="{size * 100}"{b}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Inter"/><a:ea typeface="Noto Sans SC"/></a:rPr><a:t>{escape_xml(text)}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="{size * 100}"/></a:p>'''


def slide_shell(shapes: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_CX}" cy="{SLIDE_CY}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_CX}" cy="{SLIDE_CY}"/></a:xfrm></p:grpSpPr>
      {shapes}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def px(value: int) -> int:
    return int(value * EMU_PER_PX)
