from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Slide:
    layout: str
    title: str
    data: dict = field(default_factory=dict)


def read_input(path: str | Path) -> str:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return input_path.read_text(encoding="utf-8")


def infer_title(markdown: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return explicit_title.strip()
    match = re.search(r"^\s*#\s+(.+)$", markdown, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r"主题[:：]\s*(.+)", markdown)
    if match:
        return match.group(1).strip()
    return "ICI Lab Academic Presentation"


def extract_sections(markdown: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for raw in markdown.splitlines():
        line = raw.strip()
        h2 = re.match(r"^##\s+(.+)$", line)
        if h2:
            if current_title:
                sections.append((current_title, current_lines))
            current_title = h2.group(1).strip()
            current_lines = []
            continue
        if current_title and line:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, current_lines))

    if not sections:
        bullets = []
        for line in markdown.splitlines():
            line = line.strip(" -*\t")
            if len(line) > 8 and not line.startswith("#"):
                bullets.append(line)
        if bullets:
            sections.append(("Core Ideas", bullets[:8]))
    return sections


def _clean_item(text: str) -> str:
    text = re.sub(r"^[\-*+\d\.\s]+", "", text.strip())
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text[:120].strip()


def _items(lines: list[str], fallback: list[str], limit: int = 4) -> list[str]:
    cleaned = [_clean_item(line) for line in lines if _clean_item(line)]
    return (cleaned or fallback)[:limit]


def _is_project(markdown: str) -> bool:
    keywords = ["项目", "prototype", "原型", "用户", "设计", "product", "system"]
    lowered = markdown.lower()
    return any(k.lower() in lowered for k in keywords)


def _default_topics(markdown: str) -> list[str]:
    if _is_project(markdown):
        return [
            "项目背景",
            "设计目标",
            "设计过程",
            "系统 / 原型",
            "用户反馈",
            "结果",
        ]
    return [
        "研究背景",
        "问题与挑战",
        "方法 / 框架",
        "系统或实验设计",
        "结果与发现",
        "讨论",
    ]


def plan_deck(markdown: str, title: str, page_count: int | None = None) -> list[Slide]:
    sections = extract_sections(markdown)
    requested = page_count or 10
    requested = max(5, min(20, requested))

    body_slots = max(1, requested - 5)
    topics = [s[0] for s in sections] or _default_topics(markdown)
    default_topics = _default_topics(markdown)
    while len(topics) < body_slots:
        topics.append(default_topics[len(topics) % len(default_topics)])
    topics = topics[:body_slots]

    section_map = {title_: lines for title_, lines in sections}
    toc_items = topics[:6]

    slides: list[Slide] = [
        Slide(
            "cover",
            title,
            {
                "subtitle": "An ICI Lab style academic presentation generated from structured notes",
                "meta": "Intelligent Creativity and Interaction Lab · Zhejiang University",
            },
        ),
        Slide("toc", "Contents", {"items": toc_items}),
        Slide("section", topics[0], {"section_no": "01", "subtitle": "Context, motivation, and core question"}),
    ]

    body_layouts = ["content", "two_column", "process", "image", "content", "two_column"]
    for idx, topic in enumerate(topics):
        lines = section_map.get(topic, [])
        fallback = [
            f"Clarify the role of {topic} in the overall argument",
            "Condense evidence into a small set of memorable points",
            "Connect design decisions with research goals",
            "Prepare the audience for the next step of the report",
        ]
        items = _items(lines, fallback, 5)
        layout = body_layouts[idx % len(body_layouts)]
        if idx == 0:
            layout = "content"
        if idx == 2:
            layout = "process"
        slides.append(_make_body_slide(layout, topic, items, idx + 1))

    slides.append(
        Slide(
            "summary",
            "Key Takeaways",
            {
                "cards": [
                    ("Contribution", "A structured perspective that links creativity, interaction, and system design."),
                    ("Method", "A compact framework for turning ambiguous ideas into communicable artifacts."),
                    ("Value", "A presentation rhythm suited for academic review, discussion, and iteration."),
                ]
            },
        )
    )
    slides.append(
        Slide(
            "closing",
            "AI Generated Creativity Never Ends",
            {
                "message": "谢谢您的聆听，期待您的提问与交流。让生成式智能成为创造力研究与交互设计的新起点。",
                "contact": "Lab Homepage / Contact / QR Code Placeholder",
            },
        )
    )
    return slides


def _make_body_slide(layout: str, topic: str, items: List[str], number: int) -> Slide:
    base = {"kicker": f"{number:02d} · ICI Lab Report", "items": items, "footer": "ICI Lab · Zhejiang University"}
    if layout == "two_column":
        mid = max(1, len(items) // 2)
        return Slide(
            "two_column",
            topic,
            {
                **base,
                "left_title": "Challenge",
                "right_title": "Response",
                "left_items": items[:mid] or items[:1],
                "right_items": items[mid:] or items[-2:],
            },
        )
    if layout == "process":
        return Slide(
            "process",
            topic,
            {
                **base,
                "steps": items[:4],
                "note": "The framework keeps one core claim per step, making the logic easy to follow during an academic presentation.",
            },
        )
    if layout == "image":
        return Slide(
            "image",
            topic,
            {
                **base,
                "figure_title": "Figure / Prototype / Result",
                "figure_note": "Replace this placeholder with a diagram, experiment image, or system screenshot.",
            },
        )
    return Slide("content", topic, {**base, "highlight": items[0] if items else topic})
