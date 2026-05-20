from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from dependencies import ensure_dependencies
from editable_pptx_builder import build_editable_pptx
from html_renderer import render_html_files, render_pngs
from planner import infer_title, plan_deck, read_input
from pptx_builder import build_pptx_from_pngs
from quality import check_outputs


def safe_name(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", title).strip("_")
    return f"ici_presentation_{slug[:48] or 'deck'}.pptx"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an ICI Lab style PPTX from Markdown input.")
    parser.add_argument("--input", required=True, help="Markdown input file.")
    parser.add_argument("--output", help="Output PPTX path.")
    parser.add_argument("--title", help="Deck title.")
    parser.add_argument("--pages", type=int, default=10, help="Target slide count, default 10.")
    parser.add_argument("--workdir", default="output/build", help="Intermediate HTML/PNG directory.")
    parser.add_argument("--renderer", choices=["auto", "browser", "pil"], default="auto", help="PNG renderer. Use pil only as a constrained-environment fallback.")
    parser.add_argument("--pptx-mode", choices=["editable", "image"], default="editable", help="editable creates native PowerPoint text/shapes; image uses rendered PNG slides.")
    parser.add_argument("--no-auto-install", action="store_true", help="Disable automatic dependency installation.")
    args = parser.parse_args()

    ensure_dependencies(renderer=args.renderer, pptx_mode=args.pptx_mode, auto_install=not args.no_auto_install)

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

    slides = plan_deck(markdown, title, args.pages)
    if args.pptx_mode == "editable":
        build_editable_pptx(slides, output_path, title)
        report = {
            "pptx": str(output_path),
            "pptx_mode": "editable",
            "slide_count": len(slides),
            "pptx_exists": output_path.exists(),
            "pptx_size": output_path.stat().st_size if output_path.exists() else 0,
            "font_family": "Alibaba PuHuiTi",
        }
        if not report["pptx_exists"] or report["pptx_size"] < 20_000:
            raise RuntimeError(f"Editable PPTX quality check failed: {output_path}")
    else:
        html_paths = render_html_files(slides, project_dir, html_dir)
        png_paths = render_pngs(html_paths, png_dir, slides, renderer=args.renderer)
        build_pptx_from_pngs(png_paths, output_path, title)
        report = check_outputs(png_paths, output_path)

    report_path = output_path.with_suffix(".quality.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated PPTX: {output_path}")
    print(f"Slides: {len(slides)}")
    print(f"Quality report: {report_path}")


if __name__ == "__main__":
    main()
