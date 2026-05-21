from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dependencies import ensure_dependencies
from dom_extractor import extract_layouts
from editable_pptx_builder import build_editable_pptx
from hybrid_pptx_builder import build_hybrid_pptx
from html_renderer import render_html_files, render_pngs
from pdf_assets import attach_figures_to_slides, extract_pdf_figures
from planner import infer_title, plan_deck, read_input, validate_slide_plan
from pptx_builder import build_pptx_from_pngs
from quality import check_outputs


def safe_name(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", title).strip("_")
    return f"ici_presentation_{slug[:48] or 'deck'}.pptx"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an ICI Lab style PPTX from Markdown input.")
    parser.add_argument("--input", required=True, help="Markdown input file.")
    parser.add_argument("--source-pdf", help="Optional source paper PDF. When supplied, likely figures are extracted and used on image slides.")
    parser.add_argument("--output", help="Output PPTX path.")
    parser.add_argument("--title", help="Deck title.")
    parser.add_argument("--pages", type=int, default=10, help="Target slide count, default 10.")
    parser.add_argument("--workdir", default="output/build", help="Intermediate HTML/PNG directory.")
    parser.add_argument("--renderer", choices=["auto", "browser", "pil"], default="auto", help="PNG renderer. Use pil only as a constrained-environment fallback.")
    parser.add_argument(
        "--pptx-mode",
        choices=["hybrid", "editable", "image"],
        default="hybrid",
        help="hybrid uses HTML layout plus editable PPT shapes; editable uses native preset layouts; image uses rendered PNG slides.",
    )
    parser.add_argument("--no-auto-install", action="store_true", help="Disable automatic dependency installation.")
    args = parser.parse_args()

    ensure_dependencies(renderer=args.renderer, pptx_mode=args.pptx_mode, auto_install=not args.no_auto_install, source_pdf=bool(args.source_pdf))

    project_dir = Path(__file__).resolve().parents[1]
    markdown = read_input(args.input)
    title = infer_title(markdown, args.title)
    output_path = Path(args.output) if args.output else project_dir / "output" / safe_name(title)
    if not output_path.is_absolute():
        output_path = project_dir / output_path

    workdir = Path(args.workdir)
    if not workdir.is_absolute():
        workdir = project_dir / workdir
    html_dir = workdir / "html"
    png_dir = workdir / "png"
    figure_dir = workdir / "figures"

    slides = plan_deck(markdown, title, args.pages)
    extracted_figures = []
    attached_figures = 0
    if args.source_pdf:
        extracted_figures = extract_pdf_figures(args.source_pdf, figure_dir)
        attached_figures = attach_figures_to_slides(slides, extracted_figures)
    validate_slide_plan(slides)
    toc_items = slides[1].data.get("items", []) if len(slides) > 1 and slides[1].layout == "toc" else []
    section_titles = [slide.title for slide in slides if slide.layout == "section"]
    if args.pptx_mode == "hybrid":
        if args.renderer == "pil":
            raise RuntimeError("Hybrid mode requires Playwright or a browser renderer; --renderer pil cannot extract HTML DOM layout.")
        html_paths = render_html_files(slides, project_dir, html_dir)
        png_paths = render_pngs(html_paths, png_dir, slides, renderer=args.renderer)
        html_layouts = extract_layouts(html_paths)
        build_hybrid_pptx(html_layouts, output_path, title)
        report = {
            "pptx": str(output_path),
            "pptx_mode": "hybrid",
            "pipeline": "Markdown -> HTML/CSS -> PNG preview -> DOM layout extraction -> editable python-pptx",
            "slide_count": len(slides),
            "toc_items": toc_items,
            "section_titles": section_titles,
            "png_count": len(png_paths),
            "dom_item_count": sum(len(layout.get("items", [])) for layout in html_layouts),
            "extracted_figures": len(extracted_figures),
            "attached_figures": attached_figures,
            "pptx_exists": output_path.exists(),
            "pptx_size": output_path.stat().st_size if output_path.exists() else 0,
            "font_family": "Alibaba PuHuiTi",
        }
        if not report["pptx_exists"] or report["pptx_size"] < 20_000 or report["png_count"] != len(slides):
            raise RuntimeError(f"Hybrid PPTX quality check failed: {output_path}")
    elif args.pptx_mode == "editable":
        build_editable_pptx(slides, output_path, title)
        report = {
            "pptx": str(output_path),
            "pptx_mode": "editable",
            "slide_count": len(slides),
            "toc_items": toc_items,
            "section_titles": section_titles,
            "pptx_exists": output_path.exists(),
            "pptx_size": output_path.stat().st_size if output_path.exists() else 0,
            "font_family": "Alibaba PuHuiTi",
            "extracted_figures": len(extracted_figures),
            "attached_figures": attached_figures,
        }
        if not report["pptx_exists"] or report["pptx_size"] < 20_000:
            raise RuntimeError(f"Editable PPTX quality check failed: {output_path}")
    else:
        html_paths = render_html_files(slides, project_dir, html_dir)
        png_paths = render_pngs(html_paths, png_dir, slides, renderer=args.renderer)
        build_pptx_from_pngs(png_paths, output_path, title)
        report = check_outputs(png_paths, output_path)
        report["toc_items"] = toc_items
        report["section_titles"] = section_titles
        report["extracted_figures"] = len(extracted_figures)
        report["attached_figures"] = attached_figures

    report_path = output_path.with_suffix(".quality.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated PPTX: {output_path}")
    print(f"Slides: {len(slides)}")
    print(f"Quality report: {report_path}")


if __name__ == "__main__":
    main()
