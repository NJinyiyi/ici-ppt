# ici-ppt

`ici-ppt` is a ChatGPT/Codex Skill project for generating ICI Lab style PowerPoint decks from Markdown notes, papers, reports, outlines, or raw content.

The pipeline is:

```text
Markdown input -> deck plan -> HTML/CSS slides -> 1920x1080 PNGs -> 16:9 PPTX
```

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

On first run, the script checks for `playwright`, `Pillow`, and Playwright Chromium. If something is missing, it runs:

```bash
python3 -m pip install --user playwright Pillow
python3 -m playwright install chromium
```

To install manually instead:

```bash
python3 -m pip install --user playwright Pillow
python3 -m playwright install chromium
```

To disable automatic installation:

```bash
python3 src/main.py --input examples/example_input.md --output output/demo.pptx --no-auto-install
```

If Playwright is not available but local Chrome/Chromium is installed, the renderer tries that as a fallback. If browser rendering is unavailable in a restricted environment, use `--renderer pil`.

## Run Demo

```bash
cd ici-ppt
python src/main.py --input examples/example_input.md --output output/demo.pptx --title "AI Generated Creativity Never Ends"
```

In a local environment where browser automation is unavailable, use the constrained-environment fallback:

```bash
python src/main.py --input examples/example_input.md --output output/demo.pptx --title "AI Generated Creativity Never Ends" --renderer pil
```

For production Skill use, keep the default browser renderer after installing Playwright; the `pil` renderer is only a local fallback for environments where Chromium cannot run.

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

The generated `.pptx` is 16:9 widescreen. Every slide is a full-page `1920x1080` PNG rendered from HTML/CSS, so the deck preserves visual fidelity across PowerPoint installations.

## Common Issues

- `No renderer available`: install Playwright and Chromium, or install Google Chrome/Chromium locally.
- `PNG size mismatch`: rerun with Playwright; some Chrome CLI installations ignore `--window-size` under unusual display settings.
- `PPTX too small`: inspect `output/rendered` and verify the slide PNGs were generated.

## Package as a ChatGPT Skill

1. Keep `SKILL.md` at the root of the `ici-ppt` folder.
2. Keep code and assets in the same folder.
3. Zip the entire `ici-ppt` directory or copy it into the skills directory used by your ChatGPT/Codex environment.
4. Instruct the model to use `src/main.py` for deterministic generation and to preserve the HTML-to-PNG-to-PPTX workflow.
