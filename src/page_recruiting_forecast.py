"""Owner-only hiring next-step calendar and uncertainty-aware planning view."""
from __future__ import annotations

from datetime import date, timedelta

import altair as alt
import streamlit as st

from recruiting_next_steps import LABELS, make_plan
from site_cms import _request_json, _rest_url


def fetch_step_signals(token: str) -> list[dict]:
    path = (
        "careersite_recruiting_step_signals?"
        "select=id,opportunity_id,signal_key,kind,event_label,anchor_date,"
        "window_start,window_end,source_kind,source_reference,evidence_note,"
        "recorded_at&order=anchor_date.desc,id.desc&limit=250"
    )
    response = _request_json("GET", _rest_url(path), token=token)
    return [x for x in response if isinstance(x, dict)] if isinstance(response, list) else []


def _when(item: dict) -> str:
    a, b = item["start"], item["end"]
    return a.strftime("%d %b %Y") if a == b else (
        f"{a:%d %b} – {b:%d %b %Y}"
        if a.year == b.year else f"{a:%d %b %Y} – {b:%d %b %Y}"
    )


def _schedule_chart(plan: dict) -> None:
    records = []
    for row in plan["items"]:
        if row["end"] < plan["as_of"] - timedelta(days=7):
            continue
        kind = row["kind"]
        label = (
            f"{row['employer']}"
            if kind != "action" else f"{row['employer']} · follow-up"
        )
        if any(r["Lane"] == label for r in records):
            label = f"{row['employer']} · {row['label']}"
        records.append({
            "Lane": label,
            "Start": row["start"].isoformat(),
            # Use a 24-hour-width mark for single-day events; the tooltip
            # and source table retain the original exact date.
            "End": (row["end"] + timedelta(days=1)).isoformat(),
            "Event": row["label"],
            "Evidence tier": LABELS[kind],
            "Dates": _when(row),
            "Why": row["evidence"],
            "Condition": row["conditional"] or "—",
            "kind": kind,
        })
    if not records:
        st.info("No forthcoming steps to plot.")
        return
    rows_by_label = [r["Lane"] for r in records]
    palette = alt.Scale(
        domain=list(LABELS.values()),
        range=["#287fba", "#287c69", "#be8b40", "#7c8798"],
    )
    chart = (
        alt.Chart(alt.Data(values=records))
        .mark_bar(cornerRadius=4, height=14)
        .encode(
            x=alt.X("Start:T", title="Date · Europe/Stockholm",
                    axis=alt.Axis(format="%d %b")),
            x2="End:T",
            y=alt.Y("Lane:N", sort=rows_by_label, title=None,
                    axis=alt.Axis(labelLimit=270)),
            color=alt.Color("Evidence tier:N", scale=palette,
                            legend=alt.Legend(title=None, orient="bottom")),
            tooltip=[
                alt.Tooltip("Lane:N", title="Process"),
                alt.Tooltip("Event:N", title="Next action / event"),
                alt.Tooltip("Dates:N", title="Timing"),
                alt.Tooltip("Evidence tier:N", title="Basis"),
                alt.Tooltip("Why:N", title="Evidence"),
                alt.Tooltip("Condition:N", title="Condition"),
            ],
        )
        .properties(height=max(230, 35 * len(records)))
    )
    today_line = (
        alt.Chart(alt.Data(values=[{"Today": plan["as_of"].isoformat()}]))
        .mark_rule(color="#718096", strokeWidth=1.5, strokeDash=[5, 5])
        .encode(x="Today:T")
    )
    st.altair_chart(chart + today_line, use_container_width=True)
    st.caption(
        "Horizontal bands show timing windows; a one-day mark indicates a "
        "specific date. Dashed vertical line = as-of date. The displayed "
        "width does not express probability. No conditional interview is "
        "presented as booked."
    )


def _primary_event(events: list[dict], today: date) -> dict | None:
    applicable = [r for r in events if r["kind"] != "action"
                  and r["end"] >= today]
    if applicable:
        return sorted(
            applicable, key=lambda e: (
                {"confirmed": 0, "indicated": 1, "estimated": 2}[e["kind"]],
                e["start"],
            ),
        )[0]
    if events:
        return min(events, key=lambda e: (
            0 if e["end"] >= today else 1,
            0 if e["kind"] == "action" else 1,
            abs((e["start"] - today).days),
        ))
    return None


def render_next_steps(opportunities: list[dict], meetings: list[dict],
                      signals: list[dict], today: date) -> dict:
    plan = make_plan(opportunities, meetings, signals, today)
    st.subheader("Next-step planner")
    st.caption(
        f"Forecast as of {today:%d %b %Y} · Europe/Stockholm · "
        "confirmed appointments, employer indications, estimates, "
        "and candidate follow-ups are different evidence tiers."
    )
    sample = plan["historical"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Processes with active evidence", len(plan["active"]))
    c2.metric("Confirmed future interviews", sum(
        r["kind"] == "confirmed" for r in plan["items"]
    ))
    c3.metric("Observed timing sample", sample["n"],
              help="A small, selected set of completed stage transitions and "
              "interview-to-decision intervals; not representative market data.")

    _schedule_chart(plan)
    active_rows = []
    for op in plan["active"]:
        events = [r for r in plan["items"] if r["opportunity_id"] == int(op["id"])]
        primary = _primary_event(events, today)
        followup = next(
            (r for r in sorted(events, key=lambda r: r["start"])
             if r["kind"] == "action" and r["end"] >= today), None
        )
        active_rows.append({
            "Employer": op["employer"],
            "Role": op["role_title"],
            "Next step": primary["label"] if primary else "No new milestone evidenced",
            "Window": _when(primary) if primary else "Not established",
            "Evidence": LABELS[primary["kind"]] if primary else "Unknown",
            "Your checkpoint": _when(followup) if followup else "—",
            "_sort": primary["start"] if primary else date.max,
        })
    active_rows.sort(key=lambda x: x["_sort"])
    st.markdown("**Planning table — by next expected milestone**")
    st.dataframe(
        [{k: v for k, v in row.items() if not k.startswith("_")}
         for row in active_rows],
        hide_index=True, use_container_width=True,
    )
    with st.expander("Evidence, assumptions and conditional next interviews"):
        for op in sorted(plan["active"], key=lambda o: o["employer"]):
            st.markdown(f"**{op['employer']} · {op['role_title']}**")
            for e in plan["items"]:
                if e["opportunity_id"] != int(op["id"]):
                    continue
                st.write(f"{_when(e)} — {e['label']} ({LABELS[e['kind']]})")
                st.caption(f"Basis: {e['evidence']}")
                if e["conditional"]:
                    st.caption(e["conditional"])
            conditional = [
                s for s in signals if int(s["opportunity_id"]) == int(op["id"])
                and s.get("kind") == "conditional_stage"
            ]
            if conditional:
                st.caption(
                    "Possible later step, **not scheduled**: " +
                    "; ".join(s["event_label"] for s in conditional)
                )
            if int(op["id"]) == 2:
                st.caption(
                    "If the Sportsbook director advances the application, "
                    "a director interview and possibly a case may follow; "
                    "no dates are confirmed."
                )
    with st.expander(f"Older processes requiring status verification ({len(plan['watch'])})"):
        st.caption(
            "Processes with an unknown outcome but no current confirmed "
            "appointment or explicit active-status evidence are **not** "
            "assigned hypothetical interview dates. Verify their status "
            "before scheduling preparation."
        )
        for op in plan["watch"]:
            st.write(f"{op['employer']} · {op['role_title']}")

    st.caption(
        f"Method {plan['version']}: from {sample['decision_n']} observed employer "
        f"decision delays and {sample['progression_n']} observed stage transitions "
        f"(combined n={sample['n']}), median {sample['typical']:g} calendar days "
        f"and middle sample range {sample['lower']}–{sample['upper']} days. "
        "Small, selective data cannot justify probabilities or calibrated "
        "prediction intervals. Estimated timing is conditional on the process "
        "continuing, **not** a probability of an offer. Candidate checkpoints "
        "use a separate weekday rule. Source evidence is a saved snapshot; "
        "this page does not continuously synchronize connected inboxes."
    )
    return plan
