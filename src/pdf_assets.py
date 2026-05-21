from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractedFigure:
    path: Path
    page: int
    width: int
    height: int
    caption: str


def extract_pdf_figures(pdf_path: str | Path, out_dir: str | Path, limit: int = 8) -> list[ExtractedFigure]:
    """Extract likely paper figures from a PDF for image-placeholder slides.

    Small logos and publisher marks are ignored by size. The remaining images
    are ranked by area so experimental figures outrank tiny decorative assets.
    """
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("PDF figure extraction requires pypdf. Install it with: python3 -m pip install --user pypdf") from exc

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf_path))
    candidates: list[tuple[int, ExtractedFigure, bytes, str]] = []

    for page_index, page in enumerate(reader.pages, start=1):
        for image_index, image_file in enumerate(getattr(page, "images", []), start=1):
            pil_image = getattr(image_file, "image", None)
            if pil_image is None:
                continue
            width, height = pil_image.size
            area = width * height
            if width < 600 or height < 350 or area < 350_000:
                continue
            extension = image_extension(image_file.name)
            filename = f"paper-figure-p{page_index:02d}-{image_index:02d}{extension}"
            figure = ExtractedFigure(
                path=out_path / filename,
                page=page_index,
                width=width,
                height=height,
                caption=f"Extracted from paper page {page_index}",
            )
            candidates.append((area, figure, image_file.data, extension))

    candidates.sort(key=lambda item: item[0], reverse=True)
    figures: list[ExtractedFigure] = []
    for _, figure, data, _ in candidates[:limit]:
        figure.path.write_bytes(data)
        figures.append(figure)
    return figures


def image_extension(name: str) -> str:
    suffix = Path(name).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def attach_figures_to_slides(slides, figures: list[ExtractedFigure]) -> int:
    if not figures:
        return 0
    ensure_image_slide(slides)
    attached = 0
    figure_index = 0
    for slide in slides:
        if slide.layout != "image":
            continue
        figure = figures[figure_index % len(figures)]
        slide.data["figure_path"] = str(figure.path)
        slide.data["figure_title"] = "Paper Figure"
        slide.data["figure_note"] = figure.caption
        slide.data["figure_caption"] = f"Source: {figure.caption}"
        figure_index += 1
        attached += 1
    return attached


def ensure_image_slide(slides) -> None:
    if any(slide.layout == "image" for slide in slides):
        return
    for slide in slides:
        if slide.layout in {"content", "two_column", "process"} and is_good_figure_host(slide.title):
            slide.layout = "image"
            slide.data.setdefault("items", slide.data.get("items") or slide.data.get("left_items") or slide.data.get("steps") or [])
            return
    for slide in slides:
        if slide.layout in {"content", "two_column", "process"}:
            slide.layout = "image"
            slide.data.setdefault("items", slide.data.get("items") or slide.data.get("left_items") or slide.data.get("steps") or [])
            return


def is_good_figure_host(title: str) -> bool:
    lowered = title.lower()
    keywords = ["结果", "实验", "study", "figure", "系统", "方法", "验证", "result", "method", "framework"]
    return any(keyword in lowered for keyword in keywords)
