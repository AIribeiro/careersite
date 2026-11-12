"""Public, aggregate-only reader registration KPI for Portfolio Analytics.

This module never requests reader profiles, email addresses or consent rows.
The Supabase RPC computes registrations using the canonical reporting-period
boundaries shared by the other Portfolio Analytics cards.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from page_analytics import REPORTING_WINDOW_LABELS, _dashboard_payload
from page_content_intelligence import _fetch_rpc
from portfolio_metric_cards import lifetime_comparison


@st.cache_data(ttl=90, show_spinner=False)
def reader_registration_totals(window: str) -> dict[str, int]:
    if window not in REPORTING_WINDOW_LABELS:
        raise ValueError("Unsupported reader reporting period.")
    payload = {
        "p_token": _dashboard_payload(window)["p_token"],
        "p_window": window,
    }
    data = _fetch_rpc("careersite_registered_reader_counts_v1", payload)
    current = data.get("registered")
    lifetime = data.get("lifetime")
    if current is None or lifetime is None:
        raise RuntimeError("Reader registration totals are unavailable.")
    registered = int(current)
    total = int(lifetime)
    if registered < 0 or total < 0 or registered > total:
        raise RuntimeError("Reader registration totals do not reconcile.")
    return {"registered": registered, "lifetime": total}


_READER_CARD_CSS = """
<style>
.pv-readers {
 display:flex;gap:22px;align-items:center;justify-content:space-between;
 flex-wrap:wrap;border:1px solid #dddfe2;border-radius:13px;
 background:linear-gradient(155deg,#fffdf8,#faf5ed);
 padding:24px 29px;margin:18px 0 8px;
 box-shadow:0 4px 15px rgba(14,31,50,.035);font-family:Inter,Arial,sans-serif;
}
.pv-readers__caption {
 color:#a25d39;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
 font-weight:800;margin:0 0 7px;
}
.pv-readers h3 {color:#15243b;font-size:18px;font-weight:760;margin:0 0 8px}
.pv-readers p {color:#647182;font-size:12px;line-height:1.5;margin:0}
.pv-readers__number {color:#15243b;font-size:clamp(30px,4vw,43px);
 letter-spacing:-.055em;font-weight:770;line-height:1.05;display:block}
.pv-readers__unit {display:block;font-size:11px;font-weight:750;color:#667589;margin-top:8px}
.pv-readers__lifetime {display:block;font-size:11px;color:#647182;margin-top:8px}
.pv-readers__value {text-align:right;max-width:390px}
@media(max-width:640px) {
 .pv-readers {padding:19px;align-items:flex-start}
 .pv-readers__value {text-align:left;max-width:100%}
}
</style>
"""


def reader_registration_kpi(window: str, data: dict[str, int] | None) -> str:
    period = escape(REPORTING_WINDOW_LABELS.get(window, "Selected period"))
    if data is None:
        value, lifetime = "—", "Registration service temporarily unavailable"
    else:
        value = f"{int(data['registered']):,}"
        lifetime = lifetime_comparison(
            int(data["registered"]), int(data["lifetime"]), unit="readers"
        )
    return (
        _READER_CARD_CSS +
        '<section class="pv-readers" aria-label="Registered readers analytics">'
        '<div><p class="pv-readers__caption">Audience · Verified membership</p>'
        '<h3>Registered Readers</h3>'
        '<p>New verified reader profiles created in the selected reporting period.'
        '<br>Individual reader identities and mailing preferences remain private.</p>'
        '</div><div class="pv-readers__value">'
        f'<strong class="pv-readers__number">{value}</strong>'
        f'<span class="pv-readers__unit">New registrations · {period}</span>'
        f'<span class="pv-readers__lifetime">{escape(lifetime)}</span>'
        '</div></section>'
    )
