from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def analyze_template(template_path: Path) -> dict:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    profile = {
        "template": str(template_path),
        "file_size": template_path.stat().st_size,
        "slide_count": 0,
        "slide_size": None,
        "theme_colors": [],
        "fixed_style_rules": {
            "aspect_ratio": "16:9",
            "gradient": "linear-gradient(135deg, #25148A 0%, #006FD6 48%, #66E6C3 100%)",
            "content_background": "#FFFFFF / #F8FAFC",
            "title_color": "#1B1464",
            "motif": "three small color squares near the lower-right corner",
        },
    }
    with zipfile.ZipFile(template_path) as z:
        names = z.namelist()
        profile["slide_count"] = len([n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)])
        if "ppt/presentation.xml" in names:
            root = ET.fromstring(z.read("ppt/presentation.xml"))
            ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
            sld_sz = root.find("p:sldSz", ns)
            if sld_sz is not None:
                profile["slide_size"] = {
                    "cx": int(sld_sz.attrib.get("cx", "0")),
                    "cy": int(sld_sz.attrib.get("cy", "0")),
                    "type": sld_sz.attrib.get("type", ""),
                }
        theme_names = [n for n in names if n.startswith("ppt/theme/") and n.endswith(".xml")]
        if theme_names:
            theme_xml = z.read(theme_names[0]).decode("utf-8", errors="ignore")
            colors = re.findall(r"<a:srgbClr[^>]+val=\"([0-9A-Fa-f]{6})\"", theme_xml)
            profile["theme_colors"] = sorted(set(f"#{c.upper()}" for c in colors))[:24]
    return profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze an ICI Lab PPTX template.")
    parser.add_argument("--template", default="assets/template.pptx")
    parser.add_argument("--output", default="output/template_profile.json")
    args = parser.parse_args()

    profile = analyze_template(Path(args.template))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote template profile: {output}")


if __name__ == "__main__":
    main()
