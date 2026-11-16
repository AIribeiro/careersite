"""Responsive evidence bars with complete, visible indicator names.

The values and labels are rendered as real HTML text rather than abbreviated
Vega y-axis ticks. Works at tablet and phone widths without requiring a hover
tooltip, scrolling a chart or expanding a separate legend.
"""
from __future__ import annotations

from html import escape
import math
import re
from typing import Sequence

_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

STYLE = """
<style>
.ms-labelled-bars {
  display:grid;gap:11px;width:100%;max-width:100%;min-width:0;
  margin:14px 0 20px;box-sizing:border-box;
}
.ms-bar-item {
  padding:13px 16px 12px;border:1px solid #E4DED6;
  background:#FFFDF9;min-width:0;max-width:100%;box-sizing:border-box;
}
.ms-bar-head {
  display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;
  column-gap:18px;row-gap:6px;min-width:0;
}
.ms-bar-label {
  color:#183149;font-size:14px;line-height:1.55;font-weight:700;
  flex:1 1 280px;min-width:0;max-width:100%;
  white-space:normal!important;word-break:normal;overflow-wrap:anywhere;
  overflow:visible!important;text-overflow:clip!important;
}
.ms-bar-amount {
  color:#15334B;font-size:17px;line-height:1.4;font-weight:800;
  font-variant-numeric:tabular-nums;flex:0 0 auto;white-space:normal;
  text-align:right;overflow-wrap:anywhere;max-width:100%;
}
.ms-bar-track {
  position:relative;width:100%;height:13px;margin-top:11px;
  background:#E8E7E2;border-radius:3px;overflow:hidden;
}
.ms-bar-fill {position:absolute;top:0;height:100%;border-radius:2px}
.ms-bar-zero {
  position:absolute;top:0;bottom:0;left:50%;border-left:1px solid #73808B;
}
.ms-bar-note {
  margin-top:8px;color:#677786;font-size:11px;line-height:1.5;
  white-space:normal!important;overflow-wrap:anywhere;
}
.ms-bar-scale {
  color:#657582;font-size:11px;line-height:1.5;
  white-space:normal;overflow-wrap:anywhere;
}
@media(max-width:640px) {
  .ms-bar-item {padding:12px 13px}
  .ms-bar-head {display:block}
  .ms-bar-label {display:block;width:100%;font-size:13px}
  .ms-bar-amount {display:block;text-align:left;margin-top:4px;font-size:16px}
  .ms-bar-track {height:12px}
}
</style>
"""


def _safe_color(color: str) -> str:
    if not _COLOR.fullmatch(color):
        raise ValueError("Chart color must be a six-digit hex color.")
    return color


def labelled_bars_html(
    rows: Sequence[dict], *, color: str = "#183149", unit_label: str = ""
) -> str:
    """Make an accessible bar collection with labels shown *above* every bar.

    Each row has label, value, display_value, period, source. The scale for each
    collection is based on its maximum absolute value; no values are combined.
    A signed dataset uses a visible zero line and separate left/right extents.
    HTML-escape all publisher-supplied strings; only bounded numeric widths and
    a validated color may reach inline style attributes.
    """
    if not rows:
        return ""
    color=_safe_color(color)
    values=[float(r["value"]) for r in rows]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("A chart cannot display non-finite observation values.")
    limit=max(max(abs(v) for v in values),1e-12)
    signed=any(v<0 for v in values)
    out=[STYLE,'<div class="ms-labelled-bars" role="group" aria-label="Market indicator comparison">']
    for r,v in zip(rows,values):
        if signed:
            size=min(50.,50.*abs(v)/limit)
            left=(50.-size) if v<0 else 50.
            zero='<span class="ms-bar-zero" aria-hidden="true"></span>'
        else:
            size=min(100.,100.*max(v,0.)/limit)
            left=0.
            zero=""
        label=escape(str(r["label"]),quote=True)
        shown=escape(str(r.get("display_value") or f"{v:g}"),quote=True)
        period=escape(str(r.get("period") or ""),quote=True)
        source=escape(str(r.get("source") or ""),quote=True)
        note=" · ".join(s for s in (period,source) if s)
        out.extend([
            '<section class="ms-bar-item">',
            '<div class="ms-bar-head"><span class="ms-bar-label">'+label+'</span>'
            '<strong class="ms-bar-amount">'+shown+'</strong></div>',
            '<div class="ms-bar-track" aria-hidden="true">'+zero+
            f'<span class="ms-bar-fill" style="left:{left:.2f}%;width:{size:.2f}%;'
            f'background:{color}"></span></div>',
            '<div class="ms-bar-note">'+note+'</div>' if note else "",
            '</section>',
        ])
    unit=escape(str(unit_label),quote=True)
    message=(
        "Signed scale; zero is the centre line. Bar lengths use the largest "
        "absolute value in this comparison."
        if signed else
        "Bar lengths are relative to the largest value in this comparison."
    )
    if unit:
        message+=" Original unit: "+unit+"."
    out.append('<div class="ms-bar-scale">'+escape(message)+'</div>')
    out.append("</div>")
    return "\n".join(out)
