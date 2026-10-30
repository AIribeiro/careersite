"""Owner-only Salary Intelligence: Swedish market pay benchmarks and negotiation decisions.

Live reads use the verified owner JWT and RLS-protected security-invoker views.
No assessment is cached across users; contractor invoicing is never employee pay.
"""
from __future__ import annotations

from datetime import date, datetime
from html import escape
from urllib.parse import urlencode

import streamlit as st

from site_cms import _request_json, _rest_url

ALIGNMENT_VIEW = "careersite_salary_market_alignment_v1"
SOURCE_TABLE = "careersite_salary_market_sources"
DUE_VIEW = "careersite_salary_market_due_v1"
STOCKHOLM_TIMEZONE = "Europe/Stockholm"

FIELDS = (
    "opportunity_id,process_key,employer,role_title,current_process_outcome,"
    "employment_model,comparability_group,comparison_basis,role_family,seniority_bucket,"
    "assessment_id,assessment_date,minimum_sek,expected_sek,ideal_sek,"
    "career_floor_gross_monthly_sek,negotiation_anchor_gross_monthly_sek,"
    "employer_reported_band_min_sek,employer_reported_band_max_sek,employer_band_confirmation,"
    "benchmark_id,benchmark_on,market_low_sek,market_central_sek,market_high_sek,"
    "expected_vs_market_central_sek,expected_vs_market_central_pct,expected_market_position,"
    "benchmark_freshness,benchmark_confidence,benchmark_source_count,source_check_on,"
    "next_review_on,source_reference_year,decision_data_status,salary_evidence_count,"
    "salary_assessment_stale,inference_method,observed_market_statistics,"
    "research_limitations,estimate_rationale,negotiation_guidance,comparison_caveats,"
    "daily_rate_amount,daily_rate_currency,fx_to_sek,monthly_billable_days_expected,"
    "expected_invoice_monthly_sek,contract_term_invoice_estimate_sek,estimated_duration_months"
)
SOURCE_FIELDS = (
    "benchmark_id,publisher,title,source_url,reference_year,checked_on,"
    "observed_range_low_sek,observed_range_high_sek,observed_mean_sek,"
    "observed_measure_kind,occupational_proxy,relevance,source_notes"
)
CLOSED = {"rejected", "withdrawn", "closed", "hired", "offer_accepted"}
SORTS = {
    "Expected pay (high to low)": lambda r: (-_number(r.get("expected_sek"), -1), str(r.get("employer"))),
    "Market gap (highest first)": lambda r: (-_number(r.get("expected_vs_market_central_pct"), -999), str(r.get("employer"))),
    "Salary floor margin": lambda r: (-(_number(r.get("expected_sek")) - _number(r.get("career_floor_gross_monthly_sek"))), str(r.get("employer"))),
    "Benchmark review date": lambda r: (str(r.get("next_review_on") or "9999-12-31"), str(r.get("employer"))),
    "Seniority / employer": lambda r: (str(r.get("seniority_bucket") or ""), str(r.get("employer"))),
}


def _number(value: object, default: float = 0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _sek(value: object, *, compact: bool = True) -> str:
    if value is None:
        return "—"
    value = _number(value)
    return f"{value / 1000:,.0f}k" if compact else f"{value:,.0f} SEK"


def _day(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def _direct(row: dict) -> bool:
    return (row.get("comparability_group") == "employee_base_gross"
            and row.get("comparison_basis") == "employee_base_gross"
            and row.get("employment_model") == "permanent")


def _benchmarked(row: dict) -> bool:
    return (row.get("benchmark_id") is not None
            and _number(row.get("benchmark_source_count")) > 0)


def _needs_review(row: dict, today: date) -> bool:
    due = _day(row.get("next_review_on"))
    return (not _benchmarked(row)
            or str(row.get("benchmark_confidence") or "").lower() == "low"
            or (due is not None and due <= today)
            or str(row.get("benchmark_freshness") or "") not in ("current", "historical_closed"))


def _position(row: dict) -> str:
    if not _direct(row) or not _benchmarked(row):
        return "Not comparable"
    if not all(row.get(k) is not None for k in ("market_low_sek", "market_high_sek", "expected_sek")):
        return "Unknown"
    value = _number(row["expected_sek"])
    if value < _number(row["market_low_sek"]):
        return "Below inferred band"
    if value > _number(row["market_high_sek"]):
        return "Above inferred band"
    return "Inside inferred band"


def _pct(row: dict) -> str:
    if not _direct(row) or row.get("expected_vs_market_central_pct") is None:
        return "N/A"
    pct = _number(row["expected_vs_market_central_pct"])
    if abs(pct) <= 3:
        return f"{pct:+.1f}% · near model center"
    return f"{pct:+.1f}% vs model center"


def _question(row: dict, today: date) -> str:
    if row.get("employment_model") == "contract_umbrella":
        return ("Can you confirm the umbrella provider's full payroll breakdown, including "
                "fees, employer contributions, pension, holiday pay and billable-day assumptions?")
    if not _direct(row):
        return ("Is this a permanent employee role or a contract? Please confirm the end client, "
                "payroll jurisdiction, salary or day rate, benefits and travel terms.")
    if _day(row.get("next_review_on")) and _day(row.get("next_review_on")) <= today:
        return "Has the hiring team confirmed a salary band or grading for the position since the last market review?"
    if row.get("benchmark_confidence") == "low":
        return ("Could you share the approved base-salary band and level for this exact role, "
                "along with bonus and pension arrangements?")
    if row.get("expected_sek") is not None and row.get("career_floor_gross_monthly_sek") is not None and _number(row["expected_sek"]) < _number(row["career_floor_gross_monthly_sek"]):
        return "Could the grade, base salary, pension or guaranteed compensation support my minimum threshold?"
    return "What is the approved base-salary range for this grade, and how are pension and annual bonus structured?"


def _priority(row: dict, today: date) -> tuple[int, str]:
    if not _direct(row):
        return (0, "Confirm employment economics")
    if not _benchmarked(row):
        return (0, "Research needed")
    due = _day(row.get("next_review_on"))
    if due and due <= today:
        return (0, "Benchmark refresh due")
    if row.get("expected_sek") is not None and row.get("career_floor_gross_monthly_sek") is not None and _number(row["expected_sek"]) < _number(row["career_floor_gross_monthly_sek"]):
        return (1, "Below personal salary floor")
    if row.get("benchmark_confidence") == "low":
        return (2, "Verify employer range")
    if (_number(row.get("negotiation_anchor_gross_monthly_sek")) > _number(row.get("expected_sek"))
            and _number(row.get("negotiation_anchor_gross_monthly_sek")) <= _number(row.get("market_high_sek"))):
        return (3, "Salary anchor supported by model")
    return (4, "Confirm compensation structure")


def _process_url(process_key: str, *, view: str = "stages") -> str:
    return "?" + urlencode({"page": "analytics", "workspace": "private",
                            "view": view, "process": process_key})


def _get_rows(token: str, status: str) -> list[dict]:
    if not token:
        raise PermissionError("Authenticated owner access is required.")
    selector = {
        "Active": "current_process_outcome=eq.in_progress",
        "Historical": "current_process_outcome=neq.in_progress",
        "Unconfirmed": "current_process_outcome=eq.unknown",
    }[status]
    uri = (f"{ALIGNMENT_VIEW}?select={FIELDS}&{selector}"
           "&order=expected_sek.desc.nullslast,employer.asc&limit=250")
    payload = _request_json("GET", _rest_url(uri), token=token)
    if not isinstance(payload, list) or any(not isinstance(r, dict) for r in payload):
        raise RuntimeError("Unexpected owner salary assessment response.")
    if len(payload) == 250:
        raise RuntimeError("Salary result exceeds 250 rows; add pagination before reviewing.")
    return payload


def _get_sources(token: str, benchmark_id: object) -> list[dict]:
    if not token:
        raise PermissionError("Authenticated owner access is required.")
    if benchmark_id is None:
        return []
    bid = int(benchmark_id)
    payload = _request_json(
        "GET", _rest_url(
            f"{SOURCE_TABLE}?select={SOURCE_FIELDS}&benchmark_id=eq.{bid}"
            "&order=checked_on.desc&limit=50"
        ), token=token,
    )
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected market source response.")
    return payload


def _get_due(token: str) -> list[dict]:
    if not token:
        raise PermissionError("Authenticated owner access is required.")
    payload = _request_json(
        "GET", _rest_url(
            f"{DUE_VIEW}?select=opportunity_id,employer,role_title,due_action,"
            "benchmark_freshness,benchmark_next_due_on,benchmark_status"
            "&order=priority.asc&limit=100"
        ), token=token,
    )
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected benchmark research queue response.")
    return payload


def _summary(rows: list[dict], today: date) -> tuple[int, int, int, int]:
    active = [r for r in rows if r.get("current_process_outcome") == "in_progress"]
    return (len(active),
            sum(_benchmarked(r) and r.get("assessment_id") is not None for r in active),
            sum(_direct(r) for r in active),
            sum(_needs_review(r, today) for r in active))


def _plot(rows: list[dict]) -> str:
    """Semantic, responsive interval plot; never ranks contract revenue beside pay."""
    data = [r for r in rows if _direct(r) and _benchmarked(r)
            and all(r.get(k) is not None for k in (
                "market_low_sek", "market_central_sek", "market_high_sek",
                "minimum_sek", "expected_sek", "ideal_sek"))]
    if not data:
        return ""
    values = [_number(r[k]) for r in data for k in (
        "market_low_sek", "market_high_sek", "minimum_sek", "ideal_sek",
        "expected_sek")]
    lower = max(0, int(min(values) // 10000 * 10000 - 10000))
    upper = int(max(values) // 10000 * 10000 + 20000)
    extent = max(1, upper - lower)

    def pos(value: object) -> float:
        return max(0.0, min(100.0, 100 * (_number(value) - lower) / extent))

    lines = ['<section class="salary-plot" aria-label="Monthly gross salary versus inferred market interval">']
    for r in data:
        low, mid, high = (pos(r[k]) for k in (
            "market_low_sek", "market_central_sek", "market_high_sek"))
        candlo, expected, candhi = (pos(r[k]) for k in (
            "minimum_sek", "expected_sek", "ideal_sek"))
        anchor = r.get("negotiation_anchor_gross_monthly_sek")
        title = escape(str(r.get("role_title") or "Untitled role"))
        employer = escape(str(r.get("employer") or "Unknown employer"))
        url = escape(_process_url(str(r.get("process_key") or "")), quote=True)
        text_alt = escape(
            f"{r.get('employer')}: expected {_sek(r['expected_sek'])}, "
            f"candidate minimum to ideal {_sek(r['minimum_sek'])}–{_sek(r['ideal_sek'])}, "
            f"inferred Swedish market {_sek(r['market_low_sek'])}–{_sek(r['market_high_sek'])}, "
            f"modeled center {_sek(r['market_central_sek'])} SEK monthly gross."
        , quote=True)
        lines.append(
            f'<div class="salary-plot-row"><div class="salary-plot-identity">'
            f'<a href="{url}" target="_self">{employer}</a>'
            f'<span title="{title}">{title}</span></div>'
            f'<div class="salary-track" role="img" aria-label="{text_alt}">'
            f'<div class="salary-band" style="left:{low:.2f}%;width:{high-low:.2f}%"></div>'
            f'<div class="salary-candidate" style="left:{candlo:.2f}%;width:{candhi-candlo:.2f}%"></div>'
            f'<div class="salary-center" style="left:{mid:.2f}%"></div>'
            f'<div class="salary-diamond" style="left:{expected:.2f}%"></div>'
            + (f'<div class="salary-anchor" title="Negotiation anchor" style="left:{pos(anchor):.2f}%"></div>' if anchor is not None else "")
            + f'</div><div class="salary-plot-value"><b>{_sek(r["expected_sek"])}</b>'
            f'<span>{escape(_pct(r))}</span></div></div>'
        )
    ticks = 5
    lines.append('<div class="salary-axis"><span></span><div>')
    for i in range(ticks):
        value = lower + extent * i / (ticks - 1)
        lines.append(f'<span>{_sek(value)}</span>')
    lines.append('</div><span></span></div></section>')
    return "\n".join(lines)


def _style() -> None:
    st.html("""
    <style>
    .salary-hero{background:linear-gradient(125deg,#142630 0%,#2b424a 72%,#3d555b 100%);color:#fff;
      border-radius:19px;padding:25px 30px 22px;margin:11px 0 17px;box-shadow:0 18px 35px rgba(16,29,39,.13)}
    .salary-hero .eyebrow{font-weight:750;font-size:.67rem;letter-spacing:.18em;text-transform:uppercase;color:#d7b298}
    .salary-hero h2{font-size:clamp(1.5rem,2.6vw,2.35rem);line-height:1.1;letter-spacing:-.045em;
      font-weight:650;color:#fff!important;margin:7px 0 8px}
    .salary-hero p{color:#dfe8ea;font-size:.91rem;max-width:800px;margin:0;line-height:1.5}
    .salary-section-title{font-size:1.08rem;font-weight:680;letter-spacing:-.02em;margin:20px 0 4px}
    .salary-muted{font-size:.78rem;color:#64737b;margin-bottom:14px}
    .salary-plot{background:var(--secondary-background-color,#fff);border:1px solid rgba(125,147,153,.23);
      border-radius:16px;padding:12px 20px 11px;margin:14px 0 12px}
    .salary-plot-row{display:grid;grid-template-columns:minmax(150px,235px) minmax(200px,1fr) 152px;
      gap:20px;align-items:center;padding:13px 0;border-bottom:1px solid rgba(125,147,153,.16)}
    .salary-plot-identity{display:grid;gap:3px;min-width:0}
    .salary-plot-identity a{font-size:.83rem;font-weight:720;color:inherit;text-decoration:none}
    .salary-plot-identity a:hover{text-decoration:underline}
    .salary-plot-identity span{font-size:.72rem;color:var(--text-color,#62717b);opacity:.7;
      overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .salary-track{height:28px;position:relative;background:repeating-linear-gradient(90deg,transparent,
      transparent calc(25% - 1px),rgba(116,128,138,.11) 25%);border-radius:6px}
    .salary-band{position:absolute;top:9px;height:11px;background:#c7d1d6;border-radius:6px}
    .salary-candidate{position:absolute;top:14px;height:2px;background:#445966}
    .salary-center{position:absolute;top:11px;width:9px;height:9px;border-radius:100%;background:#fff;
      border:2px solid #586e79;transform:translateX(-50%)}
    .salary-diamond{position:absolute;top:10px;width:11px;height:11px;background:#1c8494;
      border:1px solid white;transform:translateX(-50%) rotate(45deg)}
    .salary-anchor{position:absolute;top:7px;width:2px;height:17px;background:#a46c48;
      transform:translateX(-50%);border-radius:2px}
    .salary-plot-value{display:grid;text-align:right;gap:1px}
    .salary-plot-value b{font-size:1.04rem;font-weight:720;font-variant-numeric:tabular-nums}
    .salary-plot-value span{font-size:.71rem;opacity:.75}
    .salary-axis{display:grid;grid-template-columns:minmax(150px,235px) minmax(200px,1fr) 152px;gap:20px;
      margin-top:9px;font-size:.71rem;opacity:.65}
    .salary-axis div{display:flex;justify-content:space-between}
    .salary-legend{display:flex;flex-wrap:wrap;gap:10px 19px;font-size:.72rem;color:var(--text-color,#53626a);
      margin:5px 0 14px;opacity:.86}
    .salary-swatch{display:inline-block;width:17px;height:8px;margin-right:6px;border-radius:3px;background:#c7d1d6}
    .salary-line{display:inline-block;width:18px;height:2px;margin:0 6px 3px 0;background:#445966}
    .salary-mark{display:inline-block;width:9px;height:9px;margin-right:8px;transform:rotate(45deg);background:#1c8494}
    .salary-hollow{display:inline-block;width:9px;height:9px;margin-right:7px;border-radius:100%;
      background:white;border:2px solid #586e79}
    .salary-contract{border:1px solid rgba(125,147,153,.22);background:var(--secondary-background-color,#fff);
      border-radius:13px;padding:14px 17px;margin:8px 0}
    .salary-contract strong{font-size:.92rem}
    .salary-contract p{margin:5px 0;font-size:.82rem;line-height:1.55;color:var(--text-color,#53626a)}
    .salary-contract .money{font-size:1.15rem;font-weight:750;font-variant-numeric:tabular-nums}
    .salary-contract .warning{font-size:.75rem;color:#ab6a45}
    @media(max-width:700px){
      .salary-hero{padding:21px}
      .salary-plot{padding:10px 13px}
      .salary-plot-row{grid-template-columns:1fr auto;gap:4px 7px;padding:15px 0}
      .salary-plot-identity{grid-column:1 / 3}
      .salary-plot-identity span{white-space:normal}
      .salary-track{grid-column:1;height:30px}
      .salary-plot-value{grid-column:2;min-width:95px}
      .salary-axis{display:none}
    }
    </style>
    """)


def _evidence(row: dict, token: str) -> None:
    st.markdown("**Evidence and assumptions**")
    st.caption(
        "An inferred role-adjusted range is not an employer-approved offer band or an "
        "exact-role salary distribution. Source observations and modeled adjustments are separate."
    )
    st.write(
        f"Benchmark {_day(row.get('benchmark_on')) or 'unavailable'} · "
        f"Source checked {row.get('source_check_on') or 'unknown'} · "
        f"Reference year {row.get('source_reference_year') or 'unknown'} · "
        f"Next review {row.get('next_review_on') or 'not set'} · "
        f"Confidence {row.get('benchmark_confidence') or 'unknown'}."
    )
    if row.get("inference_method"):
        st.markdown("**Role-adjustment rationale**")
        st.write(str(row["inference_method"]))
    for key, title in (("observed_market_statistics", "Observed occupational statistics"),
                       ("research_limitations", "Research caveats"),
                       ("comparison_caveats", "Comparison caveats")):
        value = row.get(key)
        if value:
            with st.expander(title, expanded=False):
                st.json(value) if isinstance(value, (dict, list)) else st.write(value)
    try:
        sources = _get_sources(token, row.get("benchmark_id"))
    except (RuntimeError, ValueError, PermissionError, TimeoutError):
        st.warning("Market references could not be verified from the private source table.")
        return
    if not sources:
        st.warning("No linked source observations returned for this benchmark.")
    for source in sources:
        publisher = str(source.get("publisher") or "Source")
        title = str(source.get("title") or "Occupational reference")
        st.markdown(f"**{escape(publisher)} — {escape(title)}**", unsafe_allow_html=True)
        observed = []
        if source.get("observed_range_low_sek") is not None and source.get("observed_range_high_sek") is not None:
            observed.append(
                f"Observed published range {_sek(source['observed_range_low_sek'], compact=False)} "
                f"to {_sek(source['observed_range_high_sek'], compact=False)}"
            )
        if source.get("observed_mean_sek") is not None:
            observed.append(f"Observed mean {_sek(source['observed_mean_sek'], compact=False)}")
        st.caption(" · ".join(observed + [
            f"Reference {source.get('reference_year') or 'unknown'}",
            f"Checked {source.get('checked_on') or 'unknown'}",
            f"Proxy: {source.get('occupational_proxy') or 'unspecified'}"
        ]))
        if source.get("source_notes"):
            st.write(str(source["source_notes"]))
        url = str(source.get("source_url") or "")
        if url.startswith("https://"):
            st.link_button("Open original evidence", url, key=f"salary_src_{row.get('opportunity_id')}_{source.get('source_url')}")


def _contract_lane(rows: list[dict], token: str, today: date) -> None:
    if not rows:
        return
    st.markdown('<div class="salary-section-title">Contract and conditional economics</div>', unsafe_allow_html=True)
    st.caption(
        "Separate economic bases. Contract invoicing, modeled umbrella payroll and hypothetical "
        "employee benchmarks are not interchangeable or market-gap-ranked."
    )
    for row in rows:
        employer = escape(str(row.get("employer") or "Employer"))
        role = escape(str(row.get("role_title") or "Role"))
        currency = escape(str(row.get("daily_rate_currency") or ""))
        rate = _number(row.get("daily_rate_amount"))
        days = _number(row.get("monthly_billable_days_expected"))
        invoice = row.get("expected_invoice_monthly_sek")
        is_contract = row.get("employment_model") == "contract_umbrella"
        text = (
            f'<b class="money">{_sek(invoice, compact=False)}</b> provisional monthly invoice revenue'
            f'<p>{rate:g} {currency} per day × {days:g} assumed billable days '
            f'× {_number(row.get("fx_to_sek")):g} SEK/{currency}. '
            'Before umbrella fees, employer contributions, pension, tax and time off.</p>'
            f'<p>Modeled umbrella gross equivalent: <b>{_sek(row.get("expected_sek"), compact=False)}</b>. '
            'Not directly comparable to permanent employee base pay.</p>'
            if is_contract else
            f'<b class="money">{_sek(row.get("expected_sek"), compact=False)}</b> conditional employee '
            f'salary expectation<p>Hypothetical Swedish employee benchmark: '
            f'{_sek(row.get("market_low_sek"))}–{_sek(row.get("market_high_sek"))} '
            'gross monthly SEK. Employment type and economic basis not confirmed.</p>'
        )
        st.markdown(
            f'<div class="salary-contract"><strong>{employer} · {role}</strong>'
            f'<div>{text}</div><p class="warning">Not directly comparable · '
            f'Confirmation required</p></div>', unsafe_allow_html=True,
        )
        a, b = st.columns([1.5, 1], vertical_alignment="center")
        with a:
            st.caption(_question(row, today))
        with b:
            if st.button("Inspect evidence and assumptions", key=f"salary_contract_{row.get('opportunity_id')}", use_container_width=True):
                st.session_state["salary_inspect_process"] = row.get("process_key")
        if st.session_state.get("salary_inspect_process") == row.get("process_key"):
            with st.container(border=True):
                _evidence(row, token)


def render_salary_intelligence(session: dict | None) -> None:
    """Render owner-only, evidence-first salary benchmarking without public fallbacks."""
    token = str((session or {}).get("access_token") or "")
    if not token:
        st.error("Owner authentication required. Private salary information is not available publicly.")
        return
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo(STOCKHOLM_TIMEZONE)).date()
    _style()
    st.markdown(
        '<div class="salary-hero"><div class="eyebrow">Hiring decision desk / compensation</div>'
        '<h2>Salary Intelligence</h2><p>Compare earning scenarios with independent Swedish '
        'market evidence, identify negotiation room and confirm employment economics '
        'before drawing conclusions.</p></div>', unsafe_allow_html=True,
    )
    scope_col, _, refresh_col = st.columns([2, .35, .8], vertical_alignment="bottom")
    with scope_col:
        scope = st.segmented_control(
            "Process population", ["Active", "Historical", "Unconfirmed"],
            key="salary_scope", default="Active", width="stretch"
        ) or "Active"
    with refresh_col:
        st.button("Reload live data", key="salary_reload", width="stretch",
                  help="Read Supabase again. This does not claim to run new market research.")
    try:
        rows = _get_rows(token, scope)
    except (RuntimeError, ValueError, TimeoutError, PermissionError) as exc:
        st.error("The private salary alignment view could not be read. No historical estimates were substituted.")
        st.caption(str(exc))
        return

    if scope == "Active":
        active, benchmarked, comparable, review = _summary(rows, today)
        a, b, c, d = st.columns(4, gap="small")
        chips = [
            (a, f"Active · {active}", "all"),
            (b, f"Benchmarked · {benchmarked}/{active}", "benchmarked"),
            (c, f"Comparable · {comparable}", "comparable"),
            (d, f"Review evidence · {review}", "review"),
        ]
        for col, title, value in chips:
            with col:
                if st.button(title, key=f"salary_kpi_{value}", use_container_width=True,
                             type="primary" if st.session_state.get("salary_kpi_filter", "all") == value else "secondary"):
                    st.session_state["salary_kpi_filter"] = value
                    st.rerun()
        st.caption("Benchmarked means linked Swedish occupational references, not verified employer salary bands.")
    else:
        st.caption(f"{len(rows)} {scope.lower()} requisitions · shown separately from in-progress salary opportunities.")

    filters = st.columns([1.4, 1, 1, 1], gap="small")
    with filters[0]:
        order = st.selectbox("Sort roles", list(SORTS), key="salary_order")
    with filters[1]:
        families = sorted({str(r.get("role_family")) for r in rows if r.get("role_family")})
        family = st.selectbox("Role family", ["All"] + families, key="salary_family")
    with filters[2]:
        confidences = sorted({str(r.get("benchmark_confidence")) for r in rows if r.get("benchmark_confidence")})
        confidence = st.selectbox("Confidence", ["All"] + confidences, key="salary_confidence")
    with filters[3]:
        employment = st.selectbox("Employment", ["All", "Permanent", "Contract", "Unconfirmed"],
                                  key="salary_employment")
    employers = sorted({str(r.get("employer")) for r in rows if r.get("employer")})
    with st.expander("More filters", expanded=False):
        employer_filter = st.multiselect("Employers", employers, key="salary_employers")
        min_floor = st.checkbox("Expected below my salary floor", key="salary_floor_only")
        stale_only = st.checkbox("Benchmark review due", key="salary_due_only")
        evidence_only = st.checkbox("With salary evidence", key="salary_evidence_only")

    filtered = []
    for row in rows:
        if family != "All" and row.get("role_family") != family:
            continue
        if confidence != "All" and row.get("benchmark_confidence") != confidence:
            continue
        if employer_filter and row.get("employer") not in employer_filter:
            continue
        if employment == "Permanent" and not _direct(row):
            continue
        if employment == "Contract" and row.get("employment_model") != "contract_umbrella":
            continue
        if employment == "Unconfirmed" and row.get("employment_model") not in ("unknown", None):
            continue
        if min_floor and not (row.get("expected_sek") is not None
                              and row.get("career_floor_gross_monthly_sek") is not None
                              and _number(row["expected_sek"]) < _number(row["career_floor_gross_monthly_sek"])):
            continue
        if stale_only and not (_day(row.get("next_review_on")) is not None
                               and _day(row["next_review_on"]) <= today):
            continue
        if evidence_only and _number(row.get("salary_evidence_count")) < 1:
            continue
        chip = st.session_state.get("salary_kpi_filter", "all") if scope == "Active" else "all"
        if chip == "benchmarked" and not _benchmarked(row):
            continue
        if chip == "comparable" and not _direct(row):
            continue
        if chip == "review" and not _needs_review(row, today):
            continue
        filtered.append(row)
    filtered.sort(key=SORTS[order])
    st.caption(f"{len(filtered)} of {len(rows)} processes shown · SEK gross per month unless separately labeled · "
               f"Checked {today:%d %B %Y} Europe/Stockholm (live read, not a fresh market research claim).")

    comparable_rows = [r for r in filtered if _direct(r)]
    if comparable_rows:
        st.markdown('<div class="salary-section-title">Salary versus Swedish market</div>', unsafe_allow_html=True)
        st.caption("Role-adjusted inferred Swedish market band, not a published employer pay range.")
        st.markdown(
            '<div class="salary-legend"><span><i class="salary-swatch"></i>Inferred market low–high</span>'
            '<span><i class="salary-hollow"></i>Modeled center</span>'
            '<span><i class="salary-line"></i>Your minimum–ideal</span>'
            '<span><i class="salary-mark"></i>Your expected pay</span>'
            '<span>Thin amber tick: negotiation anchor</span></div>', unsafe_allow_html=True,
        )
        chart = _plot(comparable_rows)
        if chart:
            st.markdown(chart, unsafe_allow_html=True)
        else:
            st.info("No comparable role has all numerical market and candidate bounds.")
        st.caption("Small differences from a modeled center do not demonstrate underpayment or overpricing. "
                   "The ranges are not statistical percentiles for these exact jobs.")

        with st.expander("Compare exact figures", expanded=False):
            table = []
            for row in comparable_rows:
                table.append({
                    "Employer": str(row.get("employer") or ""),
                    "Role": str(row.get("role_title") or ""),
                    "Process": _process_url(str(row.get("process_key") or "")),
                    "Minimum": _number(row["minimum_sek"]) if row.get("minimum_sek") is not None else None,
                    "Expected": _number(row["expected_sek"]) if row.get("expected_sek") is not None else None,
                    "Ideal": _number(row["ideal_sek"]) if row.get("ideal_sek") is not None else None,
                    "Market low": _number(row["market_low_sek"]) if row.get("market_low_sek") is not None else None,
                    "Market center": _number(row["market_central_sek"]) if row.get("market_central_sek") is not None else None,
                    "Market high": _number(row["market_high_sek"]) if row.get("market_high_sek") is not None else None,
                    "Market gap %": _number(row["expected_vs_market_central_pct"]) if row.get("expected_vs_market_central_pct") is not None else None,
                    "Floor margin": (_number(row["expected_sek"]) - _number(row["career_floor_gross_monthly_sek"]))
                                    if row.get("expected_sek") is not None and row.get("career_floor_gross_monthly_sek") is not None else None,
                    "Confidence": str(row.get("benchmark_confidence") or "unknown"),
                    "Review due": row.get("next_review_on"),
                })
            st.dataframe(
                table, hide_index=True, width="stretch",
                column_config={
                    "Process": st.column_config.LinkColumn("Process detail", display_text="Open stages"),
                    **{name: st.column_config.NumberColumn(name, format="%.0f SEK")
                       for name in ("Minimum", "Expected", "Ideal", "Market low",
                                    "Market center", "Market high", "Floor margin")},
                    "Market gap %": st.column_config.NumberColumn("Gap to center (%)", format="%+.1f"),
                },
            )

    contract_rows = [r for r in filtered if not _direct(r) and r.get("assessment_id") is not None]
    _contract_lane(contract_rows, token, today)

    if comparable_rows:
        st.markdown('<div class="salary-section-title">Negotiation and evidence queue</div>', unsafe_allow_html=True)
        st.caption("The next question for each process, prioritized by economic uncertainty and benchmark support.")
        for row in sorted(comparable_rows, key=lambda r: (_priority(r, today), -_number(r.get("expected_sek")))):
            rank, signal = _priority(row, today)
            title = f"{row.get('employer') or 'Employer'} · {row.get('role_title') or 'Role'}"
            with st.expander(
                f"{title}  |  {_sek(row.get('expected_sek'))} expected · {signal}",
                expanded=st.session_state.get("salary_inspect_process") == row.get("process_key")
            ):
                m1, m2, m3 = st.columns(3)
                m1.metric("Expected", _sek(row.get("expected_sek"), compact=False))
                m2.metric("Negotiation anchor", _sek(row.get("negotiation_anchor_gross_monthly_sek"), compact=False))
                m3.metric("Potential stretch", _sek(
                    _number(row["ideal_sek"]) - _number(row["expected_sek"])
                    if row.get("ideal_sek") is not None and row.get("expected_sek") is not None else None,
                    compact=False
                ))
                st.caption(f"{_position(row)} · {_pct(row)} · "
                           f"Market confidence {row.get('benchmark_confidence') or 'unknown'} · "
                           f"Next research review {row.get('next_review_on') or 'unavailable'}")
                if row.get("negotiation_guidance"):
                    st.write(str(row["negotiation_guidance"]))
                st.markdown("**Question to ask the employer**")
                st.code(_question(row, today), language=None)
                st.link_button("Open this hiring process · Stages & MTO",
                               _process_url(str(row.get("process_key") or "")))
                _evidence(row, token)

    with st.expander("Research coverage and refresh status", expanded=False):
        st.caption("The external Swedish Salary Research Watch processes queued work on its schedule. "
                   "Reloading this page does not initiate new research or change a benchmark timestamp.")
        try:
            due = _get_due(token)
        except (RuntimeError, ValueError, PermissionError, TimeoutError):
            st.warning("The owner research queue is unavailable; no refresh status can be verified.")
        else:
            if not due:
                st.success("No queued items returned by the research-due view.")
            else:
                st.dataframe(due, hide_index=True, width="stretch")
    if not filtered:
        st.info("No salary records match these filters. Missing market evidence is shown as missing, never zero.")
