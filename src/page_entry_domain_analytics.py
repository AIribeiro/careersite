"""Public, aggregate-only reporting of the address actually used to enter the portfolio."""
from __future__ import annotations

import altair as alt
import streamlit as st

from page_analytics import _dashboard_payload
from page_content_intelligence import _fetch_rpc


_DOMAIN_NAMES = (
    "jairribeiro.com",
    "jairibeiro-ai.streamlit.app",
    "Unresolved embedded address",
    "Not measured (historical)",
)


def entry_domain_rows(report: dict) -> list[dict]:
    """Keep absent categories visible; never reinterpret historical unknowns."""
    by_domain = {
        str(row.get("domain_label")): row
        for row in report.get("domains", [])
        if isinstance(row, dict)
    }
    return [
        {
            "Entry address": domain,
            "Sessions": max(0, int(by_domain.get(domain, {}).get("sessions") or 0)),
            "Views": max(0, int(by_domain.get(domain, {}).get("views") or 0)),
        }
        for domain in _DOMAIN_NAMES
    ]


def source_evidence_rows(report: dict) -> list[dict]:
    """A domain is not a referring channel; source evidence is a separate split."""
    grouped: dict[str, dict] = {}
    for source in report.get("source_evidence", []):
        if not isinstance(source, dict):
            continue
        domain = str(source.get("domain_label") or "")
        kind = str(source.get("source_evidence") or "")
        if domain not in _DOMAIN_NAMES or kind not in (
            "Tagged", "External referrer", "Direct / source unknown"
        ):
            continue
        grouped.setdefault(domain, {"Entry address": domain,
                                    "Tagged": 0, "External referrer": 0,
                                    "Direct / unknown": 0})
        grouped[domain][{
            "Tagged": "Tagged", "External referrer": "External referrer",
            "Direct / source unknown": "Direct / unknown"
        }[kind]] += max(0, int(source.get("sessions") or 0))
    return [grouped[d] for d in _DOMAIN_NAMES if d in grouped]


def render_entry_domain_report(window: str, *, expected_site_views: int | None = None) -> None:
    st.subheader("Entry address & traffic origins")
    st.caption(
        "Which address opened the portfolio is separate from where the visit came from. "
        "Both are reported per browser-tab session; views count content opens."
    )
    try:
        report = _fetch_rpc("careersite_entry_domain_report_v1", _dashboard_payload(window))
        rows = entry_domain_rows(report)
    except (RuntimeError, ValueError, TimeoutError) as exc:
        st.caption("Entry-address reporting is temporarily unavailable.")
        return

    named = rows[:2]
    unresolved = rows[2:]
    columns = st.columns(3, gap="small")
    for col, row in zip(columns[:2], named):
        with col:
            st.metric(row["Entry address"], f'{row["Sessions"]:,} sessions')
            st.caption(f'{row["Views"]:,} views · selected period')
    with columns[2]:
        st.metric("Unresolved / historical",
                  f'{sum(row["Sessions"] for row in unresolved):,} sessions')
        st.caption(
            f'{sum(row["Views"] for row in unresolved):,} views without verified entry address'
        )

    st.dataframe(rows, hide_index=True, use_container_width=True)
    evidence_rows = source_evidence_rows(report)
    if evidence_rows:
        st.markdown("**How those sessions were attributed**")
        st.dataframe(evidence_rows, hide_index=True, use_container_width=True)
        st.caption(
            "Tagged = a source declared in the portfolio URL. External referrer = "
            "a different site observed by the browser, without a tag. "
            "Direct / unknown also includes bookmarks, privacy-restricted and masked "
            "visits whose original referring website cannot be verified."
        )

    daily = [
        {"Date": row["day"], "Entry address": row["domain_label"],
         "Views": max(0, int(row.get("views") or 0))}
        for row in report.get("daily", [])
        if isinstance(row, dict) and row.get("domain_label") in _DOMAIN_NAMES
        and isinstance(row.get("day"), str)
    ]
    if daily:
        with st.expander("Daily entry-address trend", expanded=False):
            st.altair_chart(
                alt.Chart(alt.Data(values=daily)).mark_line(point=True).encode(
                    x=alt.X("Date:T", title="Date (Stockholm)"),
                    y=alt.Y("Views:Q", title="Content views"),
                    color=alt.Color("Entry address:N", title="Entry address"),
                    tooltip=["Date:T", "Entry address:N", "Views:Q"],
                ), use_container_width=True,
            )

    observed = sum(row["Sessions"] for row in named)
    if not observed:
        st.caption(
            "Verified entry-domain measurement begins with the new browser collector. "
            "Older records remain 'Not measured'; the historical split cannot be "
            "reconstructed from Streamlit hostname or untagged referrers."
        )
    else:
        st.caption(
            "Branded-domain visits are recognized only when the enclosing frame "
            "is confirmed through browser ancestor-origin or referrer evidence. "
            "Frames that conceal both remain unresolved, not misclassified as direct Streamlit."
        )
    if expected_site_views is not None and report.get("total_views") is not None:
        if int(report["total_views"]) != int(expected_site_views):
            st.caption(
                "Domain-report views do not currently match the canonical site-wide "
                "content total; compare trends only after reviewing the reporting definitions."
            )
