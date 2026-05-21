---
name: ici-ppt
description: Generate editable ICI Lab style PowerPoint presentations from a topic, paper, report, outline, or raw notes. Use this skill when the user asks for an ICI Lab / Intelligent Creativity and Interaction Lab / Zhejiang University academic PPTX deck, especially when the output must be a .pptx with editable PowerPoint text and shapes.
---

# ici-ppt

Use this skill to create editable ICI Lab style `.pptx` files from user-provided themes, papers, reports, outlines, or notes.

## Inputs

Accept any of these inputs:

- A topic plus raw content.
- A paper abstract, introduction, method, results, and conclusion.
- A project report or product/prototype introduction.
- A Markdown outline with headings and bullets.
- A requested page count, audience, language, or title when provided.

If important information is missing, make reasonable academic defaults and keep the deck concise. Do not stop unless the missing information would make the deck factually risky.

## Output

Always produce a `.pptx` file. Default output uses the hybrid workflow: HTML/CSS defines each slide, Playwright renders PNG previews and extracts DOM layout, then `python-pptx` rebuilds the slide as editable PowerPoint text boxes and native shapes. The optional `--pptx-mode image` output preserves the full-slide PNG workflow; `--pptx-mode editable` uses the older native preset layout builder without HTML/DOM extraction.

1. Understand and condense the input.
2. Plan a deck structure.
3. Generate one HTML/CSS page per slide at `1920x1080`.
4. Render PNG previews and extract marked DOM element boxes, typography, and colors.
5. Use `python-pptx` to rebuild editable text boxes, cards, backgrounds, and decorations.
6. Apply Alibaba PuHuiTi font names to all text.
7. Run quality checks and report the final path.

When the source is an academic paper PDF, pass it with `--source-pdf`. The runner extracts likely large figures from the PDF, filters out tiny logos, and uses those figures to replace image-slide placeholders while keeping the rest of the deck editable.

For image mode only, generate one HTML/CSS page per slide at `1920x1080`, render each HTML slide to a PNG, then use `python-pptx` to insert each PNG as a full-slide image.

## Visual Rules

Follow the bundled ICI Lab template style:

- 16:9 widescreen slides.
- Cover, TOC, section, and closing slides use a blue-purple to cyan-green gradient:
  `linear-gradient(135deg, #25148A 0%, #006FD6 48%, #66E6C3 100%)`.
- Text on gradient slides must be white or pale blue. Never leave black text on cover, section, TOC, or closing slides.
- Content slides use white or very light backgrounds.
- Titles use deep blue (`#1B1464`) and strong hierarchy.
- Keep generous whitespace, clean alignment, and academic-report pacing.
- Use the three-color square motif near the bottom right on most pages.
- Use numbered sections such as `01 / 02 / 03` on TOC and section dividers.
- TOC items must exactly match the real section divider titles. Do not list body-slide topics as agenda items unless they also have matching section divider slides.
- Avoid dense paragraphs; use concise bullets, keywords, frameworks, comparisons, and process structures.
- The closing slide must include a summary, contribution, memorable statement, contact/homepage placeholder, or Q&A invitation. It must not be only “谢谢”.

Required visual font:

- Alibaba PuHuiTi, using bundled OTF files in `fonts/`.

Fallback fonts:

- Chinese: `Noto Sans SC`, `Source Han Sans SC`, `Microsoft YaHei`.
- English: `Helvetica Neue`, `Arial`.

## Page Types

Use these layouts as appropriate:

- `cover`: title, subtitle, presenter/lab metadata.
- `toc`: numbered agenda.
- `section`: large section number and title.
- `content`: one core idea with bullets/cards.
- `two_column`: comparison, before/after, challenge/solution.
- `process`: framework, pipeline, method, timeline.
- `image`: paper figure or image placeholder plus notes. Prefer extracted PDF figures when a source paper is available.
- `summary`: key takeaways or contributions.
- `closing`: final message, Q&A/contact placeholder.

## Quality Checks

Before returning the deck, verify PPTX existence and size, slide order, text density, no overlapping top-left lab/kicker text, no black text on gradient slides, and that TOC entries match the section divider titles. In hybrid and image modes, also verify PNG existence and size.

## Runtime Dependencies

The bundled runner auto-installs missing `python-pptx` on first use. Hybrid and image modes also auto-install missing `playwright`, `Pillow`, and Playwright Chromium. PDF figure extraction also auto-installs missing `pypdf`. This makes the skill usable after installation without a separate virtual environment setup.

Use `--no-auto-install` or set `ICI_PPT_AUTO_INSTALL=0` when automatic installation is not allowed. If automatic installation fails because the environment is offline or locked down, tell the user to run:

```bash
python3 -m pip install --user python-pptx playwright Pillow pypdf
python3 -m playwright install chromium
```
