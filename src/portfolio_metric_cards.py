"""Aligned, responsive executive cards for portfolio readership summaries.

The same structure, number format and five-row ranking apply across all four
measurement groups. All dynamic article titles are HTML-escaped.
"""
from __future__ import annotations

from html import escape


_CARD_STYLES = """
<style>
.pv-grid-wrap {width:100%;container-type:inline-size}\n.pv-grid, .pv-grid * {box-sizing:border-box}
.pv-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  align-items:stretch;
  gap:10px;
  margin:10px 0 8px;
  font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:#172339;
}
.pv-card {
  display:flex;
  flex-direction:column;
  min-width:0;
  min-height:448px;
  padding:15px 14px 13px;
  background:linear-gradient(162deg,#ffffff 0%,#fbfaf7 100%);
  border:1px solid #dddfe2;
  border-radius:13px;
  box-shadow:0 4px 15px rgba(14,31,50,.035);
}
.pv-card__header {min-height:58px;border-bottom:1px solid #e5e7e9}
.pv-card__eyebrow {
  display:block;margin:0 0 5px;
  color:#a25d39;font-size:10px;font-weight:800;
  letter-spacing:.12em;text-transform:uppercase;
}
.pv-card__title {margin:0;font-size:17px;line-height:1.2;letter-spacing:-.025em;font-weight:720;color:#15243b}
.pv-card__metric {min-height:128px;padding:12px 0 10px;border-bottom:1px solid #e5e7e9}
.pv-card__metric-label {font-size:11px;font-weight:700;color:#687588;letter-spacing:.035em}
.pv-card__value {
  display:block;margin-top:7px;font-size:clamp(30px,2.7vw,39px);
  line-height:1;font-weight:750;letter-spacing:-.055em;
  font-variant-numeric:tabular-nums lining-nums;color:#12223a;
}
.pv-card__lifetime {display:block;margin-top:8px;font-size:11px;line-height:1.4;color:#687588;overflow-wrap:break-word}
.pv-card__activity {
  display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  min-height:66px;gap:9px;align-items:center;
  border-bottom:1px solid #e5e7e9;
}
.pv-card__activity-block {min-width:0}
.pv-card__activity-number {
  display:block;font-size:17px;line-height:1.1;
  letter-spacing:-.03em;font-weight:740;font-variant-numeric:tabular-nums;
}
.pv-card__activity-label {display:block;margin-top:3px;font-size:10px;line-height:1.35;color:#657286}
.pv-card__ranking {display:flex;flex-direction:column;flex:1;min-width:0;padding-top:12px}
.pv-card__ranking-title {
  min-height:30px;margin:0;font-weight:720;
  font-size:13px;line-height:1.35;color:#15243b;
}
.pv-card__list {display:grid;grid-template-rows:repeat(5,minmax(0,1fr));gap:5px;flex:1;padding:0;margin:0;list-style:none}
.pv-card__item {min-width:0;min-height:31px;display:flex;flex-direction:column;justify-content:flex-start}
.pv-card__item-head {display:flex;min-width:0;gap:7px;justify-content:space-between;align-items:baseline}
.pv-card__item-name {
  display:block;min-width:0;overflow:hidden;white-space:nowrap;
  text-overflow:ellipsis;font-size:11px;line-height:1.45;color:#526077;
}
.pv-card__item-count {flex:none;font-size:11px;font-weight:750;color:#273b54;font-variant-numeric:tabular-nums}
.pv-card__bar {display:block;height:4px;overflow:hidden;background:#e9edf1;border-radius:10px;margin-top:4px}
.pv-card__fill {display:block;height:100%;background:linear-gradient(90deg,#263f63,#447fa6);border-radius:10px}
.pv-card__empty {grid-row:1 / span 5;align-self:start;padding-top:9px;font-size:12px;line-height:1.55;color:#657286}
.pv-card__item--placeholder {visibility:hidden}
@container(max-width:1150px) {
  .pv-grid {grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .pv-card {min-height:440px}
  .pv-card__value {font-size:38px}
}
@container(max-width:580px) {
  .pv-grid {grid-template-columns:minmax(0,1fr)}
  .pv-card {min-height:436px;padding:15px 14px}
  .pv-card__value {font-size:38px}
}
@media(prefers-reduced-motion:reduce) {.pv-card__fill {transition:none}}
</style>
"""


def _formatted(value: int | None) -> str:
    return "—" if value is None else f"{max(0, int(value)):,}"


def lifetime_comparison(selected: int | None, total: int | None,
                        unit: str = "views") -> str:
    """Period-to-lifetime share using comparable view counts only.

    Zero/missing totals have no defined percentage. If the cached lifetime
    snapshot lags the current period, don't report an impossible share.
    """
    if total is None:
        return "Lifetime unavailable"
    total = max(0, int(total))
    if selected is None:
        return f"Lifetime · {total:,} {unit} (period unavailable)"
    selected = max(0, int(selected))
    label = f"{selected:,} of {total:,} lifetime {unit}"
    if total == 0:
        return f"{label} (share unavailable)"
    if selected > total:
        return f"{label} (share updating)"
    percent = selected * 100 / total
    if 0 < percent < 0.005:
        share = "<0.01%"
    else:
        share = f"{percent:.2f}".rstrip("0").rstrip(".") + "%"
    return f"{label} ({share} of total)"


def _ranked_items(rows: list[dict], *, available: bool) -> str:
    if not available:
        return '<li class="pv-card__empty">Content classification is temporarily unavailable.</li>'
    top = rows[:5]
    if not top:
        return '<li class="pv-card__empty">No recorded views in this reporting period.</li>'
    peak = max(int(row.get("Views") or 0) for row in top) or 1
    items = []
    for row in top:
        count = max(0, int(row.get("Views") or 0))
        title = escape(str(row.get("Content") or "Untitled"), quote=True)
        width = min(100, max(0, 100 * count / peak))
        items.append(
            '<li class="pv-card__item">'
            '<div class="pv-card__item-head">'
            f'<span class="pv-card__item-name" title="{title}">{title}</span>'
            f'<span class="pv-card__item-count">{count:,}</span>'
            '</div>'
            f'<span class="pv-card__bar" aria-hidden="true"><span class="pv-card__fill" style="width:{width:.1f}%"></span></span>'
            '</li>'
        )
    # Identical five slots prevent short rankings from shrinking a card.
    items.extend('<li class="pv-card__item pv-card__item--placeholder" aria-hidden="true"></li>'
                 for _ in range(5 - len(top)))
    return "".join(items)


def _card(spec: dict, index: int) -> str:
    available = bool(spec.get("available", True))
    primary_value = spec["views"] if available else None
    primary = _formatted(primary_value)
    lifetime_line = escape(lifetime_comparison(
        primary_value,
        spec.get("lifetime") if available else None,
        str(spec.get("lifetime_unit", "views")),
    ))
    sessions = _formatted(spec.get("sessions") if available else None)
    items = _formatted(spec.get("items") if available else None)
    if available and spec.get("total_items") is not None:
        items = f'{items} of {_formatted(spec["total_items"])}'
    title = escape(str(spec["title"]))
    category = escape(str(spec["category"]))
    measure = escape(str(spec["measure"]))
    period = escape(str(spec.get("period_label", "selected period")))
    unit = escape(str(spec["item_unit"]))
    sessions_label = escape(str(spec.get("sessions_label", "recorded sessions")))
    rank_title = escape(str(spec["rank_title"]))
    return (
        f'<section class="pv-card" aria-label="{title} analytics">'
        '<header class="pv-card__header">'
        f'<span class="pv-card__eyebrow">{index:02d} / {category}</span>'
        f'<h3 class="pv-card__title">{title}</h3>'
        '</header>'
        '<div class="pv-card__metric">'
        f'<span class="pv-card__metric-label">{measure} · {period}</span>'
        f'<strong class="pv-card__value">{primary}</strong>'
        f'<span class="pv-card__lifetime">{lifetime_line}</span>'
        '</div>'
        '<div class="pv-card__activity">'
        f'<div class="pv-card__activity-block"><strong class="pv-card__activity-number">{sessions}</strong>'
        f'<span class="pv-card__activity-label">{sessions_label}</span></div>'
        f'<div class="pv-card__activity-block"><strong class="pv-card__activity-number">{items}</strong>'
        f'<span class="pv-card__activity-label">{unit}</span></div>'
        '</div>'
        '<div class="pv-card__ranking">'
        f'<h4 class="pv-card__ranking-title">{rank_title}</h4>'
        f'<ol class="pv-card__list">{_ranked_items(spec["rows"], available=available)}</ol>'
        '</div>'
        '</section>'
    )


def portfolio_metric_grid(cards: list[dict]) -> str:
    """Build four equal-structure cards; keep every category independent."""
    if len(cards) != 4:
        raise ValueError("The portfolio overview requires exactly four metric groups.")
    return _CARD_STYLES + '<div class="pv-grid-wrap"><div class="pv-grid" aria-label="Portfolio readership overview">' + (
        "".join(_card(spec, index) for index, spec in enumerate(cards, 1))
    ) + '</div></div>'
