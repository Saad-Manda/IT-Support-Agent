from __future__ import annotations

from typing import Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


OBSERVE_SCRIPT = r"""
(() => {
  const candidates = Array.from(
    document.querySelectorAll(
      [
        "button",
        "a[href]",
        "input",
        "textarea",
        "select",
        "[role='button']",
        "[contenteditable='true']",
        "table",
        "tr",
        "th",
        "td"
      ].join(",")
    )
  );

  function isVisible(el) {
    const style = window.getComputedStyle(el);
    if (!style) return false;
    if (style.visibility === "hidden" || style.display === "none") return false;
    const rect = el.getBoundingClientRect();
    if (!rect) return false;
    if (rect.width < 2 || rect.height < 2) return false;
    // If element is outside viewport entirely, skip.
    if (rect.bottom < 0 || rect.right < 0) return false;
    if (rect.top > (window.innerHeight || document.documentElement.clientHeight)) return false;
    if (rect.left > (window.innerWidth || document.documentElement.clientWidth)) return false;
    return true;
  }

  function isDisabled(el) {
    return !!(el.disabled || el.getAttribute("aria-disabled") === "true");
  }

  function normalize(s) {
    return (s || "").replace(/\s+/g, " ").trim();
  }

  function labelFor(el) {
    const aria = normalize(el.getAttribute("aria-label"));
    if (aria) return aria;

    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      const parts = labelledBy
        .split(/\s+/)
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((n) => normalize(n.innerText || n.textContent));
      const joined = normalize(parts.join(" "));
      if (joined) return joined;
    }

    const placeholder = normalize(el.getAttribute("placeholder"));
    if (placeholder) return placeholder;

    const id = el.getAttribute("id");
    if (id) {
      const lab = document.querySelector(`label[for='${CSS.escape(id)}']`);
      if (lab) {
        const txt = normalize(lab.innerText || lab.textContent);
        if (txt) return txt;
      }
    }

    const txt = normalize(el.innerText || el.textContent);
    if (txt) return txt;

    const name = normalize(el.getAttribute("name"));
    if (name) return name;

    const dataTest = normalize(el.getAttribute("data-testid") || el.getAttribute("data-test"));
    if (dataTest) return dataTest;

    return "";
  }

  let idCounter = 1;
  const elements = [];

  for (const el of candidates) {
    if (!isVisible(el)) continue;
    if (isDisabled(el)) continue;

    const tag = (el.tagName || "").toLowerCase();
    const type = normalize(el.getAttribute("type"));
    const role = normalize(el.getAttribute("role"));
    let label = labelFor(el);

    if (tag === 'select') {
      const opts = Array.from(el.querySelectorAll('option')).map(o => normalize(o.innerText || o.textContent));
      const optStr = opts.join(' | ');
      if (optStr) {
        label = label ? `${label} (Options: ${optStr})` : `Options: ${optStr}`;
      }
    }

    const assignedId = idCounter++;
    el.setAttribute("data-agent-id", String(assignedId));

    elements.push({
      id: assignedId,
      tag,
      role,
      type,
      label,
    });
  }

  const title = normalize(document.title);
  return { title, url: window.location.href, elements };
})()
"""


def _format_ui_description(snapshot: dict[str, Any]) -> str:
    title = snapshot.get("title") or ""
    url = snapshot.get("url") or ""
    elements = snapshot.get("elements") or []

    lines: list[str] = []
    if title:
        lines.append(f"TITLE: {title}")
    if url:
        lines.append(f"URL: {url}")
    lines.append("ELEMENTS:")

    for el in elements:
        el_id = el.get("id")
        tag = (el.get("tag") or "").upper()
        role = el.get("role") or ""
        typ = el.get("type") or ""
        label = el.get("label") or ""

        extra: list[str] = []
        if role:
            extra.append(f"role={role}")
        if typ:
            extra.append(f"type={typ}")
        extra_str = f" ({', '.join(extra)})" if extra else ""
        label_str = f" - {label}" if label else ""
        lines.append(f"[ID: {el_id}] {tag}{extra_str}{label_str}")

    return "\n".join(lines)


async def observe_ui(page) -> tuple[str, dict[str, Any]]:
    snapshot = await page.evaluate(OBSERVE_SCRIPT)
    ui_description = _format_ui_description(snapshot)
    meta = {
        "title": snapshot.get("title"),
        "url": snapshot.get("url"),
        "count": len(snapshot.get("elements") or []),
    }
    logger.debug("Observed UI", extra=meta)
    return ui_description, meta

