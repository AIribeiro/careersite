"""Public, aggregate-only reporting of the address actually used to enter the portfolio."""
from __future__ import annotations

import altair as alt
import streamlit as st

from page_analytics import _dashboard_payload
from page_content_intelligence import _fetch_rpc


_DOMAIN_NAMES = (
    "jairribeiro.com",
    "jairribeiro-ai.streamlit.app",
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
            "Verified sessions": max(0, int(by_domain.get(domain, {}).get("verified_sessions") or 0)),
            "Assigned sessions": max(0, int(by_domain.get(domain, {}).get("assigned_sessions") or 0)),
            "Assigned views": max(0, int(by_domain.get(domain, {}).get("assigned_views") or 0)),
        }
        for domain in _DOMAIN_NAMES
    ]


def branded_host_rows(report: dict) -> list[dict]:
    """Exact verified branded hosts, without promoting historical unknowns."""
    evidence: dict[str, dict[str, int]] = {}
    for item in report.get("host_source_evidence", []):
        if not isinstance(item, dict):
            continue
        host = str(item.get("host_label") or "")
        kind = str(item.get("source_evidence") or "")
        if kind in ("Tagged", "External referrer", "Direct / source unknown"):
            evidence.setdefault(host, {})[kind] = max(0, int(item.get("sessions") or 0))
    hosts: list[dict] = []
    for item in report.get("hosts", []):
        if not isinstance(item, dict) or item.get("domain_label") != "jairribeiro.com":
            continue
        host = str(item.get("host_label") or "")
        if host != "jairribeiro.com" and not host.endswith(".jairribeiro.com"):
            continue
        sources = evidence.get(host, {})
        hosts.append({
            "Entry hostname": host,
            "Sessions": max(0, int(item.get("sessions") or 0)),
            "Views": max(0, int(item.get("views") or 0)),
            "Tagged": sources.get("Tagged", 0),
            "External referral": sources.get("External referrer", 0),
            "Direct / unknown source": sources.get("Direct / source unknown", 0),
        })
    return sorted(hosts, key=lambda row: (-row["Sessions"], row["Entry hostname"]))


def campaign_attribution_rows(report: dict) -> list[dict]:
    """Aggregated declared marketing tags, grouped by observed hostname."""
    result: list[dict] = []
    for item in report.get("campaigns", []):
        if not isinstance(item, dict):
            continue
        result.append({
            "Entry hostname": str(item.get("host_label") or ""),
            "Declared source": item.get("attribution_source") or "—",
            "UTM source": item.get("utm_source") or "—",
            "Medium": item.get("utm_medium") or "—",
            "Campaign": item.get("utm_campaign") or "—",
            "Content": item.get("utm_content") or "—",
            "Sessions": max(0, int(item.get("sessions") or 0)),
        })
    return result


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
        "Root and branded subdomains roll up together; exact verified hostnames appear below. "\n        "Which address opened the portfolio is separate from where the visit came from. "
        "Both are reported per browser-tab session; views count content opens."
    )
    try:
        report = _fetch_rpc("careersite_entry_domain_report_v1", _dashboard_payload(window))
        rows = entry_domain_rows(report)
    except (RuntimeError, ValueError, TimeoutError) as exc:
        st.caption("Entry-address reporting is temporarily unavailable.")
        return

    branded, native = rows
    columns = st.columns(2, gap="small")
    with columns[0]:
        st.metric("jairribeiro.com · all subdomains", f'{branded["Sessions"]:,} sessions')
        st.caption(f'{branded["Views"]:,} verified-domain views · selected period')
    with columns[1]:
        st.metric("jairribeiro-ai.streamlit.app", f'{native["Sessions"]:,} sessions')
        st.caption(
            f'{native["Views"]:,} views · '
            f'{native["Assigned views"]:,} assigned from historical/unresolved records'
        )

    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption(
        "Historical and unresolved entry-address events are grouped under the "
        "Streamlit native address for continuity. This does not prove which domain "
        "those visits originally used; verified and assigned observations are "
        "shown separately. No original event records were changed."
    )

    branded_hosts = branded_host_rows(report)
    if branded_hosts:
        st.markdown("**Branded entry hostnames**")
        st.dataframe(branded_hosts, hide_index=True, use_container_width=True)
        st.caption(
            "Exact verified entry addresses, including go.jairribeiro.com, "
            "readers.jairribeiro.com and any other branded subdomains. "
            "These counts are already included in the jairribeiro.com total."
        )

    campaigns = campaign_attribution_rows(report)
    if campaigns:
        with st.expander("Campaign attribution by entry hostname", expanded=False):
            st.dataframe(campaigns, hide_index=True, use_container_width=True)
            st.caption(
                "Declared source (?source=) and UTM source (?utm_source=) are "
                "independent values. A masked page may conceal outer query "
                "parameters; values not visible to the browser remain unknown."
            )

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

    if expected_site_views is not None and report.get("total_views") is not None:
        if int(report["total_views"]) != int(expected_site_views):
            st.caption(
                "Domain-report views do not currently match the canonical site-wide "
                "content total; compare trends only after reviewing the reporting definitions."
            )
