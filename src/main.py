from __future__ import annotations

import argparse
import json
import re
import shutil
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
    parser.add_argument("--html-preview-dir", help="Directory for exported slide HTML previews. Defaults to <output_stem>_html_preview.")
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
    html_preview_dir = Path(args.html_preview_dir) if args.html_preview_dir else output_path.with_name(f"{output_path.stem}_html_preview")
    if not html_preview_dir.is_absolute():
        html_preview_dir = project_dir / html_preview_dir

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
        exported_html_paths = export_html_preview(html_paths, html_preview_dir, title)
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
            "html_preview_dir": str(html_preview_dir),
            "html_preview_index": str(html_preview_dir / "index.html"),
            "html_preview_count": len(exported_html_paths),
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
        exported_html_paths = export_html_preview(html_paths, html_preview_dir, title)
        png_paths = render_pngs(html_paths, png_dir, slides, renderer=args.renderer)
        build_pptx_from_pngs(png_paths, output_path, title)
        report = check_outputs(png_paths, output_path)
        report["toc_items"] = toc_items
        report["section_titles"] = section_titles
        report["html_preview_dir"] = str(html_preview_dir)
        report["html_preview_index"] = str(html_preview_dir / "index.html")
        report["html_preview_count"] = len(exported_html_paths)
        report["extracted_figures"] = len(extracted_figures)
        report["attached_figures"] = attached_figures

    report_path = output_path.with_suffix(".quality.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated PPTX: {output_path}")
    print(f"Slides: {len(slides)}")
    print(f"Quality report: {report_path}")
    if "html_preview_index" in report:
        print(f"HTML preview: {report['html_preview_index']}")


def export_html_preview(html_paths: list[Path], preview_dir: Path, title: str) -> list[Path]:
    if not html_paths:
        return []
    preview_dir.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []
    for html_path in html_paths:
        target = preview_dir / html_path.name
        shutil.copy2(html_path, target)
        exported.append(target)
    write_preview_index(exported, preview_dir / "index.html", title)
    return exported


def write_preview_index(html_paths: list[Path], index_path: Path, title: str) -> None:
    links = "\n".join(
        f"<button data-src='{path.name}'>Slide {idx:02d}</button>" for idx, path in enumerate(html_paths, start=1)
    )
    first = html_paths[0].name if html_paths else ""
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    index_path.write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{safe_title} · HTML Preview</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; background: #111827; color: white; }}
    .bar {{ height: 52px; display: flex; gap: 8px; align-items: center; padding: 0 14px; overflow-x: auto; border-bottom: 1px solid rgba(255,255,255,.16); }}
    button {{ border: 1px solid rgba(255,255,255,.22); background: rgba(255,255,255,.08); color: white; padding: 7px 11px; border-radius: 6px; cursor: pointer; white-space: nowrap; }}
    button.active {{ background: #006FD6; border-color: #66E6C3; }}
    iframe {{ width: 100vw; height: calc(100vh - 52px); border: 0; background: white; }}
  </style>
</head>
<body>
  <div class="bar">{links}</div>
  <iframe src="{first}"></iframe>
  <script>
    const frame = document.querySelector('iframe');
    const buttons = [...document.querySelectorAll('button')];
    function activate(btn) {{
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      frame.src = btn.dataset.src;
    }}
    buttons.forEach(btn => btn.addEventListener('click', () => activate(btn)));
    if (buttons[0]) activate(buttons[0]);
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
