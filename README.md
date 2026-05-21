# ici-ppt

`ici-ppt` is a ChatGPT/Codex Skill project for generating editable ICI Lab style PowerPoint decks from Markdown notes, papers, reports, outlines, or raw content.

The pipeline is:

```text
Markdown input -> deck plan -> HTML/CSS slides -> PNG preview -> DOM layout extraction -> editable PowerPoint text/shapes -> 16:9 PPTX
```

This default `hybrid` mode uses HTML/CSS as the visual source of truth, renders PNGs for visual checking, then rebuilds the slide as editable PowerPoint objects. The older native preset workflow is still available with `--pptx-mode editable`; the full-slide PNG workflow is available with `--pptx-mode image`.

The planner keeps the agenda and chapter dividers synchronized: every TOC item is a real section divider title, and body-slide topics sit under those chapters.

## Structure

```text
ici-ppt/
├── SKILL.md
├── skill.md
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   ├── planner.py
│   ├── dom_extractor.py
│   ├── hybrid_pptx_builder.py
│   ├── editable_pptx_builder.py
│   ├── html_renderer.py
│   ├── pptx_builder.py
│   ├── quality.py
│   └── template_analyzer.py
├── layouts/
│   ├── cover.html
│   ├── toc.html
│   ├── section.html
│   ├── content.html
│   ├── two_column.html
│   ├── process.html
│   ├── image.html
│   ├── summary.html
│   └── closing.html
├── styles/
│   └── ici-theme.css
├── assets/
│   └── template.pptx
├── fonts/
│   ├── Alibaba-PuHuiTi-Regular.otf
│   ├── Alibaba-PuHuiTi-Medium.otf
│   ├── Alibaba-PuHuiTi-Bold.otf
│   ├── Alibaba-PuHuiTi-Heavy.otf
│   └── Alibaba-PuHuiTi-Light.otf
├── examples/
│   └── example_input.md
└── output/
```

## Install

`ici-ppt` can auto-install missing runtime dependencies into the current Python environment on first run. No virtual environment is required.

```bash
cd ici-ppt
python3 src/main.py --input examples/example_input.md --output output/demo.pptx --title "AI Generated Creativity Never Ends"
```

On first run, the default hybrid mode checks for `python-pptx`, `Pillow`, `playwright`, and Playwright Chromium. If something is missing, it runs:

```bash
python3 -m pip install --user python-pptx Pillow playwright
python3 -m playwright install chromium
```

To install manually instead:

```bash
python3 -m pip install --user python-pptx Pillow playwright
python3 -m playwright install chromium
```

To disable automatic installation:

```bash
python3 src/main.py --input examples/example_input.md --output output/demo.pptx --no-auto-install
```

If browser rendering is unavailable in a restricted environment, use `--pptx-mode editable`. Image mode can use the constrained-environment Pillow fallback with `--renderer pil`, but hybrid mode requires Playwright because it extracts DOM layout.

## Run Demo

```bash
cd ici-ppt
python src/main.py --input examples/example_input.md --output output/demo.pptx --title "AI Generated Creativity Never Ends"
```

To use the high-fidelity rendered-image workflow:

```bash
python src/main.py --input examples/example_input.md --output output/demo-image.pptx --title "AI Generated Creativity Never Ends" --pptx-mode image
```

To use the older native editable preset workflow without HTML/DOM extraction:

```bash
python src/main.py --input examples/example_input.md --output output/demo-editable.pptx --title "AI Generated Creativity Never Ends" --pptx-mode editable
```

In a local environment where browser automation is unavailable, image mode can use the constrained-environment fallback:

```bash
python src/main.py --input examples/example_input.md --output output/demo-image.pptx --title "AI Generated Creativity Never Ends" --pptx-mode image --renderer pil
```

Analyze the reference template:

```bash
python src/template_analyzer.py --template assets/template.pptx --output output/template_profile.json
```

## Input Format

Markdown is preferred:

```markdown
# Topic

## Background
- point
- point

## Method
- point
- point
```

The first level-1 heading is used as the title when `--title` is not provided. Level-2 headings become candidate slide topics.

## Output

The generated `.pptx` is 16:9 widescreen. Default output uses HTML/CSS-derived coordinates to create editable PowerPoint text boxes and native shapes with Alibaba PuHuiTi font names applied. Image mode renders each slide as a full-page `1920x1080` PNG and uses `python-pptx` to assemble the final deck.

PowerPoint does not automatically install or embed fonts from the Skill folder. To see the editable deck exactly as designed on another machine, install the bundled Alibaba PuHuiTi OTF files from `fonts/`.

## Common Issues

- `Font fallback appears`: install the bundled Alibaba PuHuiTi OTF files from `fonts/`.
- `No renderer available`: hybrid mode needs Playwright and Chromium; use `--pptx-mode editable` if browser automation is unavailable.
- `PowerPoint asks to repair the file`: make sure this version is using `python-pptx`; run `python3 -m pip install --user python-pptx` and regenerate the deck.
- `PNG size mismatch`: rerun with Playwright; some Chrome CLI installations ignore `--window-size` under unusual display settings.
- `PPTX too small`: inspect `output/rendered` and verify the slide PNGs were generated.

## Package as a ChatGPT Skill

1. Keep `SKILL.md` at the root of the `ici-ppt` folder.
2. Keep code and assets in the same folder.
3. Zip the entire `ici-ppt` directory or copy it into the skills directory used by your ChatGPT/Codex environment.
4. Instruct the model to use `src/main.py` for deterministic generation. Default to hybrid PPTX mode; use `--pptx-mode image` only when exact rendered visual fidelity matters more than editability.
