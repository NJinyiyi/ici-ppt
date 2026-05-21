from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from html_renderer import SLIDE_HEIGHT, SLIDE_WIDTH


async def extract_layout_with_playwright(html_paths: list[Path]) -> list[dict[str, Any]]:
    from playwright.async_api import async_playwright

    layouts: list[dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT}, device_scale_factor=1)
        for html_path in html_paths:
            await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            layouts.append(await page.evaluate(EXTRACT_SCRIPT))
        await browser.close()
    return layouts


def extract_layouts(html_paths: list[Path]) -> list[dict[str, Any]]:
    if not html_paths:
        raise ValueError("No HTML paths supplied for layout extraction.")
    return asyncio.run(extract_layout_with_playwright(html_paths))


EXTRACT_SCRIPT = """
() => {
  const slide = document.querySelector('.slide');
  const slideStyle = getComputedStyle(slide);
  const slideRect = slide.getBoundingClientRect();

  function colorToHex(value) {
    if (!value || value === 'transparent' || value === 'rgba(0, 0, 0, 0)') return null;
    const match = value.match(/rgba?\\(([^)]+)\\)/);
    if (!match) return null;
    const parts = match[1].split(',').map((p) => p.trim());
    const alpha = parts.length >= 4 ? Number(parts[3]) : 1;
    if (alpha === 0) return null;
    return parts.slice(0, 3).map((p) => Math.max(0, Math.min(255, Math.round(Number(p))))).map((n) => n.toString(16).padStart(2, '0')).join('').toUpperCase();
  }

  function boxOf(el) {
    const r = el.getBoundingClientRect();
    return {
      x: r.left - slideRect.left,
      y: r.top - slideRect.top,
      w: r.width,
      h: r.height
    };
  }

  function textBoxOf(el, style) {
    const box = boxOf(el);
    const pt = parseFloat(style.fontSize || '24') * 0.5;
    const lineHeight = style.lineHeight === 'normal' ? parseFloat(style.fontSize || '24') * 1.2 : parseFloat(style.lineHeight || style.fontSize || '24');
    const minHeight = Math.max(box.h, lineHeight + 8);
    return {...box, h: minHeight + 6};
  }

  function itemFor(el) {
    const style = getComputedStyle(el);
    const pptType = el.dataset.ppt || 'text';
    const box = pptType === 'text' || pptType === 'bullet' ? textBoxOf(el, style) : boxOf(el);
    const rect = {
      type: pptType,
      role: el.dataset.pptRole || '',
      text: (el.innerText || '').replace(/\\s+\\n/g, '\\n').trim(),
      box,
      style: {
        color: colorToHex(style.color),
        backgroundColor: colorToHex(style.backgroundColor),
        borderColor: colorToHex(style.borderTopColor),
        fontSize: parseFloat(style.fontSize || '24') * 0.5,
        fontWeight: Number(style.fontWeight) || 400,
        lineHeight: style.lineHeight === 'normal' ? 1.2 : parseFloat(style.lineHeight) / Math.max(1, parseFloat(style.fontSize || '24')),
        textAlign: style.textAlign || 'left',
        borderTopWidth: parseFloat(style.borderTopWidth || '0'),
        borderWidth: parseFloat(style.borderWidth || '0'),
        borderRadius: parseFloat(style.borderRadius || '0'),
        opacity: parseFloat(style.opacity || '1')
      }
    };
    return rect;
  }

  const items = [...document.querySelectorAll('[data-ppt]')]
    .filter((el) => el.dataset.ppt !== 'group')
    .map(itemFor)
    .filter((item) => item.box.w > 0 && item.box.h > 0 && (item.type !== 'text' || item.text.length > 0));

  return {
    slide: {
      width: slideRect.width,
      height: slideRect.height,
      classes: [...slide.classList],
      background: slideStyle.background
    },
    items
  };
}
"""
