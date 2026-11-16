"""Verified-reader CTA for the interactive AI Portfolio Renewal Excel advisor.

This is an HTML route to the existing Streamlit member session, never a public
static XLSX. Generated workbook bytes are provided only by the verified dialog.
"""
from __future__ import annotations

from briefing_renewal_excel import SLUG


def decision_record_cta_html() -> str:
    return (
        '<section class="renewal-worksheet-cta" data-analytics-section="briefing-decision-record">'
        '<style>.site .renewal-worksheet-cta{margin:32px 0 36px;padding:25px 28px;'
        'background:#edf3f2;border:1px solid #c8d8dc;border-left:4px solid #b4805a}'
        '.site .renewal-worksheet-cta h3{font:500 28px/1.2 Georgia,serif;'
        'margin:7px 0 10px;color:#102b40}.site .renewal-worksheet-cta p{'
        'font:14px/1.75 Arial,sans-serif;color:#354b5b;max-width:730px}'
        '.site .renewal-worksheet-cta a{display:inline-flex;align-items:center;'
        'justify-content:center;min-height:46px;background:#13354b;'
        'color:#fff!important;text-decoration:none!important;padding:13px 19px;'
        'font:750 12px/1.4 Arial,sans-serif;margin-top:9px}'
        '@media(max-width:650px){.site .renewal-worksheet-cta{padding:19px}'
        '.site .renewal-worksheet-cta a{width:100%}}</style>'
        '<span class="eyebrow">AI PORTFOLIO RENEWAL · MEMBER DECISION TOOL</span>'
        '<h3>Download your Excel Decision Advisor</h3>'
        '<p>Compare your existing AI initiative with a credible alternative. '
        'Use guided inputs and dropdown choices to calculate a recommendation: '
        'Renew, Replace, Test, Stop or Hold. Five worksheets include instructions, '
        'a worked example, transparent decision rules and a record of the '
        'executive\'s final decision. Included with complimentary verified reader access.</p>'
        '<a href="?page=briefing&amp;article=' + SLUG
        + '&amp;worksheet=1" target="_self" '
        'data-hq-event="briefing_excel_decision_advisor_open">'
        'Download Excel Decision Advisor (.xlsx)</a></section>'
    )
