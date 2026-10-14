"""Visual market evidence without combining incompatible units or populations."""
from __future__ import annotations

import math

import altair as alt
import streamlit as st


def trend_cards(groups: dict) -> list[dict]:
    cards = []
    for key, rows in groups.items():
        points = []
        for row in rows:
            try:
                value = float(row.get("metric_value"))
            except (TypeError, ValueError):
                continue
            date = row.get("period_end") or row.get("observation_date")
            if date and math.isfinite(value):
                points.append({"Date": str(date), "Value": value, "row": row})
        points.sort(key=lambda p: p["Date"])
        if len(points) < 2:
            continue
        # Never draw a continuous series across a change in measurement units.
        units = {p["row"].get("metric_unit") for p in points}
        if len(units) != 1:
            continue
        previous, latest = points[-2:]
        row = latest["row"]
        change = latest["Value"] - previous["Value"]
        direction = "Higher" if change > 0 else "Lower" if change < 0 else "Unchanged"
        cards.append({
            "key": key, "title": row.get("indicator_name") or str(key),
            "direction": direction, "change": change, "latest": latest["Value"],
            "unit": str(row.get("metric_unit") or "source units").replace("_", " "),
            "period": row.get("period_label") or latest["Date"],
            "previous_period": previous["row"].get("period_label") or previous["Date"],
            "source": row.get("source_organization") or "Source not recorded",
            "scope": " · ".join(str(row[k]) for k in ("region", "sector", "frequency") if row.get(k)),
            "points": [{"Date": p["Date"], "Value": p["Value"]} for p in points],
        })
    return cards


def render_market_trends(model: dict) -> None:
    st.subheader("Market trends at a glance")
    st.caption("Independent releases only · each chart keeps its own units and reporting period. "
               "Higher or lower describes the measure, not your probability of getting a job.")
    cards = trend_cards(model.get("groups", {}))
    if not cards:
        st.info("Not enough comparable independent periods for a visual trend yet. "
                "Single observations are not evidence of momentum.")
    else:
        counts = {label: sum(c["direction"] == label for c in cards)
                  for label in ("Higher", "Lower", "Unchanged")}
        st.markdown(f"**What changed in the latest releases?** {counts['Higher']} measures rose, "
                    f"{counts['Lower']} fell and {counts['Unchanged']} were unchanged.")
        st.caption("This is a coverage summary, not a composite market score. Series may overlap "
                   "and their releases cover different dates; movement is not necessarily a sustained trend.")
        choices = {c["key"]: c for c in cards}
        selected = st.multiselect(
            "Indicators to explore", list(choices), default=list(choices)[:6],
            format_func=lambda key: f"{choices[key]['title']} — {choices[key]['scope']}",
            key="admin_market_trend_cards",
        )
        columns = st.columns(2)
        for index, key in enumerate(selected):
            card = choices[key]
            with columns[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{card['title']}**")
                    st.caption(card["scope"])
                    value = f"{card['latest']:,.3f}".rstrip("0").rstrip(".")
                    delta = f"{card['change']:+,.3f}".rstrip("0").rstrip(".")
                    st.metric(card["direction"], value,
                              delta=f"{delta} {card['unit']}", delta_color="off")
                    st.caption(f"{card['period']} versus {card['previous_period']}")
                    st.altair_chart(
                        alt.Chart(alt.Data(values=card["points"])).mark_line(
                            point=True, color="#38bdf8", strokeWidth=3,
                        ).encode(
                            x=alt.X("Date:T", title=None),
                            y=alt.Y("Value:Q", title=card["unit"], scale=alt.Scale(zero=False)),
                            tooltip=[alt.Tooltip("Date:T", title="Period end"),
                                     alt.Tooltip("Value:Q", format=",.3f")],
                        ).properties(height=170), width="stretch",
                    )
                    st.caption(f"{len(card['points'])} independent periods · {card['source']}. "
                               "Axis is fitted to this series; compare values, not chart heights.")
        if not selected:
            st.info("Choose an indicator above to display its trend.")
    with st.expander("Exact figures", expanded=False):
        if model.get("trends"):
            st.dataframe(model["trends"], hide_index=True, width="stretch")
        else:
            st.caption("No comparable trend figures yet.")
        st.caption("Source documents and measurement notes remain available under Sources & measurement.")
