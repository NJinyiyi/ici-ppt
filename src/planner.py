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
    lowered = markdown.lower()
    strong_project_keywords = [
        "项目介绍",
        "项目背景",
        "项目目标",
        "产品",
        "原型",
        "用户反馈",
        "用户研究",
        "prototype",
        "product",
        "roadmap",
        "mvp",
    ]
    academic_keywords = [
        "论文",
        "研究",
        "实验",
        "方法",
        "框架",
        "结果",
        "讨论",
        "conclusion",
        "experiment",
        "method",
        "research",
    ]
    project_score = sum(1 for keyword in strong_project_keywords if keyword.lower() in lowered)
    academic_score = sum(1 for keyword in academic_keywords if keyword.lower() in lowered)
    return project_score > 0 and project_score >= academic_score


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

    topics = [s[0] for s in sections] or _default_topics(markdown)
    default_topics = _default_topics(markdown)
    while len(topics) < 3:
        topics.append(default_topics[len(topics) % len(default_topics)])

    section_map = {title_: lines for title_, lines in sections}
    chapter_count = _chapter_count(requested, len(topics))
    chapter_groups = _group_topics(topics, chapter_count)
    chapter_titles = _chapter_titles(chapter_groups, markdown)
    body_slots = max(chapter_count, requested - chapter_count - 4)
    body_distribution = _distribute_body_slots(chapter_count, body_slots)

    slides: list[Slide] = [
        Slide(
            "cover",
            title,
            {
                "subtitle": "An ICI Lab style academic presentation generated from structured notes",
                "meta": "Intelligent Creativity and Interaction Lab · Zhejiang University",
            },
        ),
        Slide("toc", "Contents", {"items": chapter_titles}),
    ]

    body_layouts = ["content", "two_column", "process", "image", "content", "two_column"]
    body_index = 0
    for chapter_idx, (chapter_title, group, slide_count) in enumerate(zip(chapter_titles, chapter_groups, body_distribution), start=1):
        slides.append(
            Slide(
                "section",
                chapter_title,
                {
                    "section_no": f"{chapter_idx:02d}",
                    "subtitle": " / ".join(group[:3]),
                },
            )
        )
        for local_idx in range(slide_count):
            topic = group[local_idx % len(group)]
            lines = section_map.get(topic, [])
            fallback = [
                f"Clarify the role of {topic} in the overall argument",
                "Condense evidence into a small set of memorable points",
                "Connect design decisions with research goals",
                "Prepare the audience for the next step of the report",
            ]
            items = _items(lines, fallback, 5)
            layout = body_layouts[body_index % len(body_layouts)]
            if body_index == 0:
                layout = "content"
            if "方法" in topic or "框架" in topic or body_index == 2:
                layout = "process"
            slides.append(_make_body_slide(layout, topic, items, body_index + 1))
            body_index += 1

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


def validate_slide_plan(slides: list[Slide]) -> None:
    toc_slides = [slide for slide in slides if slide.layout == "toc"]
    if not toc_slides:
        raise ValueError("Deck plan is missing a table-of-contents slide.")

    toc_items = [str(item).strip() for item in toc_slides[0].data.get("items", []) if str(item).strip()]
    section_titles = [slide.title.strip() for slide in slides if slide.layout == "section" and slide.title.strip()]
    if toc_items != section_titles:
        raise ValueError(
            "TOC entries must match section divider titles exactly: "
            f"toc={toc_items}, sections={section_titles}"
        )


def _chapter_count(requested: int, topic_count: int) -> int:
    max_by_pages = max(1, (requested - 4) // 2)
    preferred = 4 if requested >= 12 else 3 if requested >= 10 else 2
    return max(1, min(preferred, max_by_pages, max(1, topic_count)))


def _group_topics(topics: list[str], chapter_count: int) -> list[list[str]]:
    groups: list[list[str]] = []
    for idx in range(chapter_count):
        start = round(idx * len(topics) / chapter_count)
        end = round((idx + 1) * len(topics) / chapter_count)
        group = topics[start:end] or [topics[min(idx, len(topics) - 1)]]
        groups.append(group)
    return groups


def _chapter_titles(groups: list[list[str]], markdown: str) -> list[str]:
    if all(len(group) == 1 for group in groups):
        return [group[0] for group in groups]

    if _is_project(markdown):
        presets = {
            2: ["项目背景与目标", "设计结果与总结"],
            3: ["项目背景与目标", "设计过程与系统", "用户反馈与总结"],
            4: ["项目背景", "设计目标与过程", "系统验证", "结果与展望"],
        }
    else:
        presets = {
            2: ["研究问题与方法", "结果、讨论与贡献"],
            3: ["研究背景与问题", "方法设计与框架", "结果、讨论与贡献"],
            4: ["研究背景与问题", "方法与系统设计", "结果与验证", "讨论与贡献"],
        }
    return presets.get(len(groups), [group[0] for group in groups])


def _distribute_body_slots(chapter_count: int, body_slots: int) -> list[int]:
    slots = [1] * chapter_count
    remaining = max(0, body_slots - chapter_count)
    idx = 0
    while remaining:
        slots[idx % chapter_count] += 1
        idx += 1
        remaining -= 1
    return slots


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
