"""Aggregate-only content reporting; preserves legacy dashboards independently."""
from __future__ import annotations

import csv
import io
import json
from urllib import request, error

import streamlit as st

from page_analytics import _dashboard_payload, _bar_chart, _pct, _seconds
from page_article_analytics import _article_title
from site_analytics import ANALYTICS_URL, ANALYTICS_PUBLISHABLE_KEY


def fetch_intelligence(window: str) -> dict:
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/careersite_content_intelligence",
        data=json.dumps(_dashboard_payload(window)).encode(), method="POST",
        headers={"apikey": ANALYTICS_PUBLISHABLE_KEY, "Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            data = json.load(response)
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError("Content intelligence is temporarily unavailable; established reports remain below.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Content intelligence returned an unexpected response.")
    return data


def content_label(value: str) -> str:
    if value.startswith("article:"):
        return _article_title(value[8:])
    return value.replace("_", " ").title()


def performance_rows(data: dict, kind: str) -> list[dict]:
    rows = []
    for row in data.get("performance", []):
        if row.get("kind") != kind:
            continue
        n = int(row.get("sessions") or 0)
        depth_n = int(row.get("depth_measured_sessions") or 0)
        rows.append({
            "Content": _article_title(row["content"]) if kind == "article" else content_label(row["content"]),
            "Views": row["views"], "Sessions": n,
            "Engaged ≥10s": row["engaged_sessions"],
            "Avg visible time": _seconds(row.get("avg_active_seconds")),
            "Timing confirmed": row["confirmed_sessions"],
            "Depth measured": depth_n,
            "Reached 50%": _pct(row["halfway_sessions"], depth_n),
            "Reached 90%": _pct(row["bottom_sessions"], depth_n),
            "Deep reads ≥30s + 90%": row["deep_read_sessions"] if depth_n else None,
            "Share actions": row["shares"],
            "Share rate": _pct(row["sharing_sessions"], n),
            "Actions on content": row["action_sessions"],
            "Later CV sessions": row["later_cv_sessions"],
            "Later contact sessions": row["later_contact_sessions"],
            "Later portfolio sessions": row["later_portfolio_sessions"],
        })
    return rows


def export_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        # Neutralize spreadsheet formula injection from campaign/content labels.
        for row in rows:
            writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for k, v in row.items()})
    return output.getvalue()


def render_content_intelligence(kind: str, window: str) -> None:
    try:
        data = fetch_intelligence(window)
    except RuntimeError as exc:
        st.warning(str(exc))
        return
    quality = data.get("quality", {})
    a, b, c = st.columns(3)
    prefix = "article" if kind == "article" else "page"
    a.metric("Article views" if kind == "article" else "Portfolio page views", quality.get(prefix + "_views", 0))
    b.metric("Reader sessions" if kind == "article" else "Portfolio sessions", quality.get(prefix + "_sessions", 0))
    c.metric("Contact-intent sessions · whole site", quality.get("contact_sessions", 0))
    st.caption("Contact intent counts each session once across email and LinkedIn clicks; it does not confirm a message or hiring enquiry.")
    if kind == "page" and quality.get("legacy_thinking_views"):
        st.info(f"{quality['legacy_thinking_views']} historical Thinking views cannot be reliably separated into index and article visits. They remain in the established reports below.")
    performance, paths, acquisition, health = st.tabs(["Content performance", "Visitor paths", "Source quality", "Measurement health"])
    with performance:
        rows = performance_rows(data, kind)
        st.subheader("Reading depth & downstream actions" if kind == "article" else "Page attention & downstream actions")
        st.caption("Time is cumulative per content/session, confirmed at ≥5 seconds. Scroll depth measures content exposure, not comprehension. Deep reads combine ≥30 seconds with ≥90% exposure. Later actions are observed after the content opened, within the reporting window; they do not prove causation.")
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
            st.download_button("Download content report (CSV)", export_csv(rows), file_name=f"{prefix}-analytics-{window}.csv", mime="text/csv")
        else:
            st.info("No measured content views in this reporting window.")
    with paths:
        st.subheader("Where visitors go next")
        paths_rows = [dict(r, path=f"{content_label(r['from_content'])} → {content_label(r['to_content'])}") for r in data.get("journeys", []) if (r['from_content'].startswith('article:') if kind == 'article' else not r['from_content'].startswith('article:'))]
        _bar_chart(paths_rows, "path", value="sessions", limit=15, height=400)
        st.caption("Consecutive different content views in the same tab/session. Historical Thinking paths may include articles. Sessions already in progress at the window boundary may have earlier steps outside this report.")
        left, right = st.columns(2)
        with left:
            st.subheader("First observed content")
            _bar_chart([dict(r, label=content_label(r['content'])) for r in data.get('entrances', []) if r['content'].startswith('article:') == (kind == 'article')], 'label', limit=10)
        with right:
            st.subheader("Last observed content")
            _bar_chart([dict(r, label=content_label(r['content'])) for r in data.get('exits', []) if r['content'].startswith('article:') == (kind == 'article')], 'label', limit=10)
        st.caption("Last observed content is not a confirmed exit; a session may still be active.")
    with acquisition:
        st.subheader("Which sources bring attention and action?")
        st.caption("Whole-site session cohorts, using the first observed source/campaign in this window. Compare counts alongside rates: small samples can move sharply.")
        campaigns = []
        for row in data.get('campaigns', []):
            campaigns.append({"Source": row['channel'], "Campaign / role": row['campaign'], "Sessions": row['sessions'], "Reader sessions": row['reader_sessions'], "Engaged rate": _pct(row['engaged_sessions'], row['sessions']), "CV sessions": row['cv_sessions'], "Contact sessions": row['contact_sessions'], "CV rate": _pct(row['cv_sessions'], row['sessions']), "Contact rate": _pct(row['contact_sessions'], row['sessions'])})
        if campaigns:
            st.dataframe(campaigns, hide_index=True, use_container_width=True)
        else:
            st.info("No source activity in this window.")
    with health:
        st.write(f"Last received event: {quality.get('last_event_at') or 'No events in window'}")
        st.write(f"New measurement first seen in window: {quality.get('new_measurement_since') or 'Awaiting new visitor events'}")
        st.write(f"Content sessions with new instrumentation: {quality.get('measured_content_sessions', 0)} / {quality.get('content_sessions', 0)}")
        st.caption("New page timing and scroll measurements start with this release. Missing historical measurements are not zero engagement. Browser blocks, disabled JavaScript and failed requests can prevent collection. Sessions are not unique people; visible time is not proof of attention. Share actions indicate intent, not verified publication. No persistent visitor profiles are created.")
    st.caption(f"{data.get('period_label', window)} · since {data.get('period_since', '—')} · generated {data.get('generated_at', '—')}")
