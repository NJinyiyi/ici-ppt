from __future__ import annotations

from pathlib import Path
from typing import Any


def check_outputs(png_paths: list[Path], pptx_path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"png_count": len(png_paths), "pngs": [], "pptx": str(pptx_path)}
    try:
        from PIL import Image
    except Exception:
        Image = None  # type: ignore

    for path in png_paths:
        item = {"path": str(path), "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}
        if Image and path.exists():
            with Image.open(path) as img:
                item["width"], item["height"] = img.size
                item["valid_size"] = img.size == (1920, 1080)
        report["pngs"].append(item)

    report["pptx_exists"] = pptx_path.exists()
    report["pptx_size"] = pptx_path.stat().st_size if pptx_path.exists() else 0
    report["pptx_reasonable"] = report["pptx_size"] > 50_000

    bad_pngs = [p for p in report["pngs"] if not p.get("exists") or p.get("valid_size") is False]
    if bad_pngs:
        raise RuntimeError(f"Quality check failed for PNG files: {bad_pngs}")
    if not report["pptx_exists"] or not report["pptx_reasonable"]:
        raise RuntimeError(f"Quality check failed for PPTX: {pptx_path}")
    return report
