---
name: ici-ppt
description: Generate ICI Lab style PowerPoint presentations from a topic, paper, report, outline, or raw notes. Use this skill when the user asks for an ICI Lab / Intelligent Creativity and Interaction Lab / Zhejiang University academic PPTX deck, especially when the output must be a .pptx built from HTML/CSS rendered slides.
---

# ici-ppt

Use this skill to create ICI Lab style `.pptx` files from user-provided themes, papers, reports, outlines, or notes.

## Inputs

Accept any of these inputs:

- A topic plus raw content.
- A paper abstract, introduction, method, results, and conclusion.
- A project report or product/prototype introduction.
- A Markdown outline with headings and bullets.
- A requested page count, audience, language, or title when provided.

If important information is missing, make reasonable academic defaults and keep the deck concise. Do not stop unless the missing information would make the deck factually risky.

## Output

Always produce a `.pptx` file. The standard pipeline is:

1. Understand and condense the input.
2. Plan a deck structure.
3. Generate one HTML/CSS page per slide at `1920x1080`.
4. Render each HTML slide to a PNG.
5. Insert each PNG as a full-slide image in a 16:9 PPTX.
6. Run quality checks and report the final path.

## Visual Rules

Follow the bundled ICI Lab template style:

- 16:9 widescreen slides.
- Cover, TOC, section, and closing slides use a blue-purple to cyan-green gradient:
  `linear-gradient(135deg, #25148A 0%, #006FD6 48%, #66E6C3 100%)`.
- Content slides use white or very light backgrounds.
- Titles use deep blue (`#1B1464`) and strong hierarchy.
- Keep generous whitespace, clean alignment, and academic-report pacing.
- Use the three-color square motif near the bottom right on most pages.
- Use numbered sections such as `01 / 02 / 03` on TOC and section dividers.
- Avoid dense paragraphs; use concise bullets, keywords, frameworks, comparisons, and process structures.
- The closing slide must include a summary, contribution, memorable statement, contact/homepage placeholder, or Q&A invitation. It must not be only “谢谢”.

Preferred fonts:

- Chinese: `Noto Sans SC`, `Source Han Sans SC`, `Microsoft YaHei`.
- English: `Inter`, `Helvetica Neue`, `Arial`.

## Page Types

Use these layouts as appropriate:

- `cover`: title, subtitle, presenter/lab metadata.
- `toc`: numbered agenda.
- `section`: large section number and title.
- `content`: one core idea with bullets/cards.
- `two_column`: comparison, before/after, challenge/solution.
- `process`: framework, pipeline, method, timeline.
- `image`: figure or image placeholder plus notes.
- `summary`: key takeaways or contributions.
- `closing`: final message, Q&A/contact placeholder.

## Quality Checks

Before returning the deck, verify PNG existence and size, PPTX existence and size, slide order, and text density.

## Runtime Dependencies

The bundled runner auto-installs missing `playwright`, `Pillow`, and Playwright Chromium into the current Python environment on first use. This makes the skill usable after installation without a separate virtual environment setup.

Use `--no-auto-install` or set `ICI_PPT_AUTO_INSTALL=0` when automatic installation is not allowed. If automatic installation fails because the environment is offline or locked down, tell the user to run:

```bash
python3 -m pip install --user playwright Pillow
python3 -m playwright install chromium
```
