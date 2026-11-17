"""AI & Data Market Signals — curated, evidence-led Advisory member product.

Only reads the dedicated, RLS-protected publication tables through the verified
member JWT. It never reads the private career, job-search or forecast datasets.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape as html_escape
from io import BytesIO, StringIO
from urllib.parse import urlsplit
import csv
import math

import altair as alt
import pandas as pd
import streamlit as st
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from site_cms import _request_json, _rest_url
from market_labelled_bars import labelled_bars_html
from site_components import nav, footer
from about_next_navigation import portfolio_next_navigation
from page_public_services import SERVICES_CSS

PALETTE = {
    "navy": "#11273C", "ink": "#22394D", "copper": "#B17B58",
    "muted": "#607182", "paper": "#F8F7F3", "white": "#FFFFFF",
    "line": "#DCD8D0",
}
LENSES = {
    "leadership": "AI & Data leadership demand",
    "adoption": "AI adoption",
    "capability": "Data & AI capabilities",
    "consulting": "Consulting conditions",
}
SOURCE_CADENCE_DAYS = {
    "af_jobtech_target_demand": 15,
    "af_jobsearch_current": 15,
    "brainville_consulting_market": 50,
    "scb_enterprise_ai_adoption": 410,
    "techsverige_market_analysis": 190,
    "manpower_employment_outlook": 110,
    "scb_private_management_salary": 410,
    "almega_services_indicator": 110,
    "ki_konjunkturbarometern": 48,
    "swedbank_pmi": 48,
}
MARKET_STYLE = """
<style>
.st-key-market_signals_workspace [data-testid="stMetric"] {
 background:#FFFDF9;border:1px solid #DDD8CF;border-top:2px solid #AD7855;
 padding:14px 16px;border-radius:4px;
}
.st-key-market_signals_workspace [data-testid="stMetricLabel"] {
 color:#53677B;white-space:normal!important;overflow:visible!important;
 max-width:100%;min-width:0;
}
.st-key-market_signals_workspace [data-testid="stMetricLabel"] * {
 white-space:normal!important;text-overflow:clip!important;
 overflow-wrap:anywhere!important;overflow:visible!important;
}
.st-key-market_signals_workspace [data-testid="stMetricValue"] {
 color:#142B42;white-space:normal!important;overflow-wrap:anywhere;
}
.st-key-market_signals_workspace [data-testid="stMetric"] {min-width:0;}
.st-key-market_signals_workspace [data-testid="stPills"] {
 overflow-x:auto;max-width:100%;padding:8px;background:#FFFDF9;border:1px solid #E3DDD5;
}
.st-key-market_signals_workspace [data-testid="stPills"] button {
 min-height:42px;white-space:nowrap;font-weight:700;
}
.market-editorial-status {margin:10px 0 17px;padding:13px 17px;
 border-left:2px solid #B17B58;border-bottom:1px solid #E1DCD3;
 background:#F9F7F3;color:#334D5F}
.market-editorial-status strong {font-size:11px;font-weight:800;letter-spacing:.035em}
.market-editorial-status p {font-size:12px;line-height:1.65;color:#5F6F7D;margin:5px 0 0}
.market-hero {background:linear-gradient(120deg,#10253A,#203D53);color:#fff;
 padding:clamp(28px,4vw,51px);margin:7px 0 21px}
.market-hero .eyebrow {text-transform:uppercase;letter-spacing:.17em;font-size:10px;
 color:#E5B58F;font-weight:800}
.market-hero h2 {color:#fff;font:500 clamp(35px,4.9vw,59px)/1.1 Georgia,serif;
 letter-spacing:-.035em;margin:14px 0 12px}
.market-hero p {color:#D3DEE6;font-size:15px;line-height:1.7;max-width:820px}
.market-head {padding:12px 0 5px}
.market-head h3 {color:#1A3248;font:500 clamp(23px,3vw,34px)/1.15 Georgia,serif;
 margin:8px 0}
.market-head p {color:#596B7B;line-height:1.65}
.market-kicker {text-transform:uppercase;font-size:10px;font-weight:800;
 color:#976B4E;letter-spacing:.14em}
.market-thesis {padding:20px 23px;border-left:4px solid #AC7854;
 background:#FFFDF9;margin:12px 0;color:#213B52;line-height:1.75}
.market-thesis h3 {margin:0 0 8px;font:500 25px Georgia,serif;color:#142B42}
.market-evidence {margin:12px 0 17px;padding:16px 20px;border:1px solid #DDD8CE;
 background:#F6F3ED;color:#35495B;font-size:13px;line-height:1.7}
.market-evidence strong{color:#203D55}
.market-source {padding:15px 18px;border-bottom:1px solid #DED8CD;background:#FFFEFC;
 overflow-wrap:anywhere}
.market-source strong {font-size:13px;color:#20394F}
.market-source small {display:block;color:#687784;margin-top:4px;line-height:1.6}
.market-source a {color:#1B577C;text-decoration:underline}
.market-outcome{padding:20px 22px;background:#142B42;color:#F9F6F1;
 line-height:1.7;margin:12px 0 20px}
.market-outcome strong{color:#F0C4A1}
.market-outcome p{color:#E0E6EB}
@media(max-width:700px),(max-device-width:700px){
 .market-hero{padding:24px 18px}
 .market-thesis,.market-outcome{padding:16px 17px}
 .st-key-market_signals_workspace .stHorizontalBlock {flex-wrap:wrap!important}
 .st-key-market_signals_workspace .stColumn {min-width:min(100%,260px)!important}
}
</style>
"""


MARKET_SIGNALS_LANDING_CSS = """
<style>
/* Scoped, accessible editorial landing page. No scripts, external assets or fixed widths. */
.site.ms-landing {width:100%;max-width:100%;overflow-x:clip;overflow-wrap:break-word}
.site.ms-landing *, .site.ms-landing *::before,.site.ms-landing *::after {box-sizing:border-box}
.site.ms-landing .container {width:calc(100% - clamp(30px,5vw,88px));max-width:none;min-width:0}
.site.ms-landing .ms-hero {background:#101f32;color:#f8f7f2;padding:clamp(52px,7vw,99px) 0 66px;position:relative}
.site.ms-landing .ms-hero:before {content:"";position:absolute;inset:0 0 auto; height:4px;background:linear-gradient(90deg,#B67D59 0%,#B67D59 21%,transparent 21%,transparent 100%)}
.site.ms-landing .ms-hero-grid {display:grid;grid-template-columns:minmax(0,1fr);gap:clamp(28px,4vw,52px);align-items:start;width:100%}
.site.ms-landing .ms-hero-grid > *,.site.ms-landing .ms-grid > *,.site.ms-landing .ms-proofs > * {min-width:0}
.site.ms-landing .ms-overline {font-size:11px;line-height:1.5;letter-spacing:.18em;text-transform:uppercase;font-weight:800;color:#AD6844;margin:0 0 17px}
.site.ms-landing .ms-hero .ms-overline {color:#E8B995}
.site.ms-landing .ms-hero h1 {display:block;width:100%;max-width:none;font:500 clamp(39px,4.9vw,69px)/1.07 Georgia,serif;letter-spacing:-.037em;margin:0 0 24px;color:#fff;white-space:normal!important;overflow-wrap:break-word;text-wrap:pretty}
.site.ms-landing .ms-hero-lead {color:#D6DFE9;font-size:clamp(17px,1.5vw,20px);line-height:1.65;width:100%;max-width:none;margin:0}
.site.ms-landing .ms-hero-context {font-size:14px;color:#BFCBD7;line-height:1.72;width:100%;max-width:none;margin:18px 0 0}
.site.ms-landing .ms-actions {display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:30px 0 0}
.site.ms-landing .ms-button {display:inline-flex;min-height:50px;align-items:center;justify-content:center;text-align:center;padding:14px 20px;background:#DCA987;border:1px solid #DCA987;color:#10273A!important;font-size:13px;font-weight:850;letter-spacing:.01em;text-decoration:none!important;line-height:1.35;max-width:100%}
.site.ms-landing .ms-button:hover,.site.ms-landing .ms-button:focus-visible {background:#F4C8A9}
.site.ms-landing .ms-button--outline {background:transparent;border-color:#8EA4B6;color:#F2F6F9!important}
.site.ms-landing .ms-button--outline:hover {background:#24394F}
.site.ms-landing a:focus-visible {outline:3px solid #E5A675;outline-offset:3px}
.site.ms-landing .ms-hero-meta {color:#BCC9D6;font-size:12px;line-height:1.6;margin:19px 0 0}
.site.ms-landing .ms-edition {background:#1B3349;border:1px solid #53677B;border-top:3px solid #D3A07C;padding:clamp(21px,3vw,33px);width:100%;max-width:none}
.site.ms-landing .ms-edition small {font-weight:800;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#E8BB98}
.site.ms-landing .ms-edition h2 {font:500 clamp(24px,2.5vw,32px)/1.17 Georgia,serif;color:#fff;margin:15px 0 12px;letter-spacing:-.015em;overflow-wrap:anywhere}
.site.ms-landing .ms-edition p {font-size:13px;line-height:1.73;color:#CCD6DF;margin:0}
.site.ms-landing .ms-edition-counts {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:25px 0;border-top:1px solid #5B6F80;border-bottom:1px solid #5B6F80;padding:18px 0}
.site.ms-landing .ms-edition-counts strong {display:block;color:#FFF9F3;font:500 clamp(24px,2.3vw,33px)/1.1 Georgia,serif}
.site.ms-landing .ms-edition-counts span {display:block;color:#C0CDD9;font-size:10px;line-height:1.5;margin-top:6px}
.site.ms-landing .ms-edition .ms-edition-note {font-size:11px;color:#BFCBD7}
.site.ms-landing .ms-section {padding:clamp(55px,7vw,94px) 0}
.site.ms-landing .ms-section--white {background:#FFFDF9}
.site.ms-landing .ms-section--paper {background:#F4F0E9}
.site.ms-landing .ms-section--ink {background:#11283C;color:#F5F4F1}
.site.ms-landing .ms-section-head {display:block;width:100%;margin:0 0 34px}
.site.ms-landing .ms-section h2 {display:block;width:100%;max-width:none;font:500 clamp(31px,4.1vw,54px)/1.12 Georgia,serif;color:#1A3045;letter-spacing:-.025em;white-space:normal!important;overflow-wrap:break-word;text-wrap:pretty;margin:0}
.site.ms-landing .ms-section--ink h2 {color:#F9F8F4}
.site.ms-landing .ms-section-intro {font-size:15px;color:#56687A;line-height:1.77;width:100%;max-width:none;margin:18px 0 0}
.site.ms-landing .ms-section--ink .ms-section-intro {color:#CAD5DF}
.site.ms-landing .ms-proofs {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}
.site.ms-landing .ms-proof {background:#FFFEFC;border:1px solid #DDD6CD;padding:clamp(19px,2.5vw,30px);display:flex;flex-direction:column;min-height:330px}
.site.ms-landing .ms-proof .ms-label,.site.ms-landing .ms-usecase .ms-label {font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#996843;font-weight:850}
.site.ms-landing .ms-proof h3 {color:#1D344A;font:500 clamp(22px,2vw,28px)/1.18 Georgia,serif;margin:18px 0 17px}
.site.ms-landing .ms-proof .ms-number {color:#153249;font:500 clamp(37px,3.8vw,54px)/1 Georgia,serif;margin:0 0 11px}
.site.ms-landing .ms-proof .ms-number span {font-size:19px;font-family:Arial,sans-serif;font-weight:500}
.site.ms-landing .ms-proof .ms-number-pair {display:flex;gap:18px;flex-wrap:wrap}
.site.ms-landing .ms-proof .ms-number-pair small {display:block;font-family:Arial,sans-serif;font-size:10px;color:#697985;margin-top:7px}
.site.ms-landing .ms-proof p {font-size:14px;line-height:1.73;color:#526579;margin:0 0 14px}
.site.ms-landing .ms-proof .ms-proof-question {border-top:1px solid #E4DED6;margin-top:auto;padding-top:19px;color:#223A50;font-size:14px;line-height:1.6}
.site.ms-landing .ms-proof .ms-proof-question strong {display:block;color:#A36C4B;font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px}
.site.ms-landing .ms-proof-source {font-size:11px!important;line-height:1.55!important;color:#6B7780!important;margin-top:11px!important}
.site.ms-landing .ms-proof-source a {color:#295778!important;text-underline-offset:3px}
.site.ms-landing .ms-proof--demo {background:#183349;border-color:#183349}
.site.ms-landing .ms-proof--demo h3,.site.ms-landing .ms-proof--demo p,.site.ms-landing .ms-proof--demo .ms-proof-question {color:#F7F8F5}
.site.ms-landing .ms-proof--demo .ms-label,.site.ms-landing .ms-proof--demo .ms-proof-question strong {color:#EDBC99}
.site.ms-landing .ms-proof--demo .ms-proof-question {border-top-color:#5E7180}
.site.ms-landing .ms-demo-link {display:block;background:#DCA987;color:#132D42!important;font-size:13px;font-weight:800;text-decoration:none!important;text-align:center;padding:15px 12px;margin:15px 0;line-height:1.5}
.site.ms-landing .ms-demo-link:hover,.site.ms-landing .ms-demo-link:focus-visible {background:#F0C3A2}
.site.ms-landing .ms-proof--demo .ms-proof-source {color:#D6DDE4!important}
.site.ms-landing .ms-note {font-size:12px;line-height:1.65;color:#667789;margin:17px 0 0}
.site.ms-landing .ms-decision-list {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.site.ms-landing .ms-usecase {border-top:2px solid #AD7B59;padding:23px 26px 25px;background:#FFFEFC;min-height:190px}
.site.ms-landing .ms-usecase h3 {color:#1E3449;font:500 clamp(21px,2.1vw,29px)/1.2 Georgia,serif;margin:14px 0 10px}
.site.ms-landing .ms-usecase p {font-size:13px;line-height:1.7;color:#57697C;margin:0}
.site.ms-landing .ms-workspace {display:grid;grid-template-columns:minmax(0,1.26fr) minmax(0,.75fr);gap:clamp(20px,4vw,70px);align-items:start}
.site.ms-landing .ms-dashboard-list {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;border-top:1px solid #53687A}
.site.ms-landing .ms-dashboard-list article {border-bottom:1px solid #53687A;padding:16px 16px 18px 0;min-width:0}
.site.ms-landing .ms-dashboard-list span {color:#E4B48E;font-size:10px;font-weight:800;letter-spacing:.14em}
.site.ms-landing .ms-dashboard-list h3 {font-size:15px;font-weight:800;color:#F7F8F8;line-height:1.45;margin:8px 0}
.site.ms-landing .ms-dashboard-list p {font-size:12px;color:#BDCAD7;line-height:1.65;margin:0}
.site.ms-landing .ms-path {background:#203A51;border:1px solid #526A7E;padding:clamp(21px,2.7vw,34px)}
.site.ms-landing .ms-path h3 {color:#F8F5F0;font:500 28px/1.2 Georgia,serif;margin:12px 0 20px}
.site.ms-landing .ms-path ol {list-style:none;margin:0;padding:0;counter-reset:market-step}
.site.ms-landing .ms-path li {counter-increment:market-step;border-top:1px solid #4C6375;padding:16px 0 16px 38px;position:relative;color:#D8E1E8;font-size:13px;line-height:1.62}
.site.ms-landing .ms-path li:before {content:"0" counter(market-step);position:absolute;top:17px;left:0;color:#F3C5A4;font-weight:800;font-size:11px;letter-spacing:.06em}
.site.ms-landing .ms-path li strong {display:block;color:#fff;font-size:13px;margin-bottom:3px}
.site.ms-landing .ms-path .ms-path-caption {margin:16px 0 0;color:#C4D1DC;font-size:11px;line-height:1.65}
.site.ms-landing .ms-formats {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.site.ms-landing .ms-format {background:#fffefa;border:1px solid #DBD6CD;padding:27px;min-width:0;display:flex;flex-direction:column}
.site.ms-landing .ms-format small {font-weight:800;color:#9F6A49;font-size:10px;letter-spacing:.14em;text-transform:uppercase}
.site.ms-landing .ms-format h3 {font:500 27px/1.2 Georgia,serif;color:#20384C;margin:16px 0}
.site.ms-landing .ms-format p {font-size:14px;line-height:1.74;color:#536579;margin:0 0 13px}
.site.ms-landing .ms-format .ms-format-bottom {margin-top:auto;border-top:1px solid #E6E0D7;padding-top:14px;font-size:12px;color:#233D55;font-weight:800;line-height:1.55}
.site.ms-landing .ms-standard {display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.75fr);gap:clamp(20px,6vw,100px)}
.site.ms-landing .ms-source-list {margin:0;padding:0;list-style:none}
.site.ms-landing .ms-source-list li {border-bottom:1px solid #D9D2C9;padding:17px 0;color:#465A6B;font-size:14px;line-height:1.72}
.site.ms-landing .ms-source-list strong {display:block;color:#1D3449;font-size:14px}
.site.ms-landing .ms-source-list a {color:#265D82!important;text-decoration:underline!important;text-underline-offset:3px}
.site.ms-landing .ms-quality {background:#E9E3D9;border-left:3px solid #A57250;padding:clamp(20px,2.7vw,33px)}
.site.ms-landing .ms-quality h3 {font:500 27px/1.22 Georgia,serif;color:#1C364D;margin:0 0 18px}
.site.ms-landing .ms-quality p {font-size:13px;line-height:1.8;color:#46586A;margin:0 0 15px}
.site.ms-landing .ms-quality p strong {display:block;margin-bottom:3px;color:#1D3449;font-weight:800}
.site.ms-landing .ms-quality .ms-small {font-size:11px;color:#667484}
.site.ms-landing .ms-lastcta {background:#122A3D;color:#FAF8F3;padding:clamp(55px,7vw,86px) 0}
.site.ms-landing .ms-cta-grid {display:grid;grid-template-columns:minmax(0,1fr);gap:30px;align-items:start}
.site.ms-landing .ms-lastcta h2 {display:block;width:100%;max-width:none;font:500 clamp(32px,4.4vw,56px)/1.13 Georgia,serif;color:#fff;letter-spacing:-.025em;overflow-wrap:break-word;margin:0}
.site.ms-landing .ms-lastcta p {color:#D2DEE9;font-size:15px;line-height:1.75;margin:17px 0}
.site.ms-landing .ms-cta-aside {width:100%;padding:24px;border-left:2px solid #C9916E;background:#203A50}
.site.ms-landing .ms-cta-aside strong {color:#FCE4D1}
.site.ms-landing .ms-cta-aside p {margin:10px 0 0;font-size:13px}
@media(max-width:1100px) {
 .site.ms-landing .ms-hero-grid {grid-template-columns:minmax(0,1fr)}
 .site.ms-landing .ms-edition {max-width:none}
 .site.ms-landing .ms-proofs {grid-template-columns:repeat(2,minmax(0,1fr))}
 .site.ms-landing .ms-section-head {grid-template-columns:minmax(0,1fr);gap:13px}
 .site.ms-landing .ms-workspace,.site.ms-landing .ms-standard,.site.ms-landing .ms-cta-grid {grid-template-columns:minmax(0,1fr);gap:25px}
}
@media(max-width:760px),(max-device-width:760px) {
 .site.ms-landing .ms-hero {padding:50px 0}
 .site.ms-landing .ms-hero h1 {font-size:clamp(36px,8.5vw,52px);line-height:1.11}
 .site.ms-landing .ms-proofs,.site.ms-landing .ms-decision-list,.site.ms-landing .ms-formats {grid-template-columns:minmax(0,1fr)}
 .site.ms-landing .ms-proof {min-height:0}
 .site.ms-landing .ms-dashboard-list {grid-template-columns:minmax(0,1fr)}
 .site.ms-landing .ms-edition-counts {gap:5px}
 .site.ms-landing .ms-section {padding:54px 0}
 .site.ms-landing .ms-actions {align-items:stretch}
 .site.ms-landing .ms-actions .ms-button {width:100%}
 .site.ms-landing .ms-usecase {min-height:0}
}
@media(prefers-reduced-motion:reduce) {
 .site.ms-landing .ms-button {transition:none}
}
</style>
"""

MARKET_SIGNALS_LANDING_HTML = """
<main class="site advisory-page ms-landing">
<section class="ms-hero" aria-labelledby="ms-title"><div class="container">
  <div class="ms-hero-grid">
    <div>
      <p class="ms-overline">AI &amp; Data Market Signals / Sweden</p>
      <h1 id="ms-title">AI &amp; Data Market Intelligence for Executive Decision-Making</h1>
      <p class="ms-hero-lead">A focused review of reported enterprise AI use, selected senior AI &amp; Data job advertisements, and consulting-market activity in Sweden.</p>
      <p class="ms-hero-context">The research separates observed measures from assumptions about business value, capability needs and recruitment. Original sources, alternative explanations and decision questions are provided; conclusions about an individual organisation require its own evidence.</p>
      <div class="ms-actions">
        <a class="ms-button" href="?page=advisory-access&amp;view=market-signals" target="_self" data-hq-event="market_signals_register">Access the published research</a>
        <a class="ms-button ms-button--outline" href="#ms-findings">Review selected findings</a>
      </div>
      <p class="ms-hero-meta">The historical research sample is public. The full report, Observatory and downloadable materials are available through free Advisory registration.</p>
    </div>
    <aside class="ms-edition" aria-label="Published research edition">
      <small>November 2026 / Published edition</small>
      <h2>AI &amp; Data Market Review<br>Edition 01</h2>
      <p>Published 16 November 2026. This edition examines reported AI use, selected senior AI/Data job advertisements and wider consulting activity in Sweden, with the original figures and their limitations.</p>
      <div class="ms-edition-counts">
        <div><strong>30</strong><span>published data points</span></div>
        <div><strong>4</strong><span>written analyses</span></div>
        <div><strong>3</strong><span>data sources</span></div>
      </div>
      <p class="ms-edition-note">All figures retain their reporting periods and limitations. This edition is not a live market forecast.</p>
    </aside>
  </div>
</div></section>

<section class="ms-section ms-section--white" id="ms-findings" aria-labelledby="ms-findings-title"><div class="container">
  <div class="ms-section-head">
    <div><p class="ms-overline">November 2026 / Published observations</p>
      <h2 id="ms-findings-title">What the published evidence shows—and where its limits lie.</h2></div>
    <p class="ms-section-intro">Three distinct measures from Edition 01 illustrate the research. The fourth panel provides a public historical sample. None of these figures, on its own, establishes business value or market-wide AI hiring conditions.</p>
  </div>
  <div class="ms-proofs">
    <article class="ms-proof">
      <span class="ms-label">01 / Enterprise AI adoption</span>
      <h3>AI use is reported; business outcomes require separate evidence.</h3>
      <div class="ms-number">49<span>%</span></div>
      <p>of Swedish enterprises with at least 10 employees reported using AI in the 2026 SCB survey. Among enterprises with 250 or more employees, the share was <strong>85%</strong>. These numbers measure reported use, not business results.</p>
      <div class="ms-proof-question"><strong>Executive consideration</strong>What has improved in cost, service, quality or risk since people started using AI?</div>
      <p class="ms-proof-source"><a href="https://www.scb.se/hitta-statistik/statistik-efter-amne/forskning-och-det-digitala-samhallet/det-digitala-samhallet/it-anvandning-i-foretag/pong/statistiknyhet/it-anvandning-i-foretag-2026/" target="_blank" rel="noopener noreferrer">Source: Statistics Sweden (SCB), 2026 survey</a></p>
    </article>
    <article class="ms-proof">
      <span class="ms-label">02 / Senior leadership advertisements</span>
      <h3>Senior AI &amp; Data recruitment: a limited observed sample.</h3>
      <div class="ms-number">29</div>
      <p>Our defined JobTech search found 29 advertisements in Sweden for selected senior AI and Data/Analytics job titles in October 2026. This is a small, selective sample—not a count of all vacancies or people hired.</p>
      <div class="ms-proof-question"><strong>Executive consideration</strong>Before recruiting, have you agreed what this leader needs to own and deliver?</div>
      <p class="ms-proof-source"><a href="https://historical.api.jobtechdev.se/search" target="_blank" rel="noopener noreferrer">Source: Arbetsförmedlingen JobTech, selected titles</a> · October 2026</p>
    </article>
    <article class="ms-proof">
      <span class="ms-label">03 / Consulting market activity</span>
      <h3>Consulting assignments and available capacity both increased.</h3>
      <div class="ms-number ms-number-pair">
        <div>+10.7<span>%</span><small>Listed assignments · YoY</small></div>
        <div>+18.5<span>%</span><small>Available consultants · YoY</small></div>
      </div>
      <p>Brainville reported both increases in its Swedish marketplace for October 2026 compared with a year earlier. They describe different groups across many professions, not AI/Data specialists alone.</p>
      <div class="ms-proof-question"><strong>Executive consideration</strong>What should your team learn to do itself, and where would outside expertise really help?</div>
      <p class="ms-proof-source"><a href="https://www.brainville.com/sv/Blog/Post/1923" target="_blank" rel="noopener noreferrer">Source: Brainville, October 2026 market report</a></p>
    </article>
    <article class="ms-proof ms-proof--demo">
      <span class="ms-label">04 / Historical research sample</span>
      <h3>Historical leadership-advertisement evidence, June–August 2026.</h3>
      <p>Read a free, five-page example based on our earliest complete set of reviewed leadership job-advertisement records, from June to August 2026. It includes the figures, a chart, the questions they raise and the limits of what we can conclude.</p>
      <p>This sample was prepared in November 2026 using older JobTech records. It is not a full market review from those summer months; later SCB and Brainville figures are not included.</p>
      <a class="ms-demo-link" href="?page=advisory-market-demo" target="_self"
         data-hq-event="market_signals_public_demo">View the historical research sample</a>
      <div class="ms-proof-question"><strong>What the analysis includes</strong>How we explain a number, consider other explanations and turn it into a useful question for leaders.</div>
      <p class="ms-proof-source">JobTech · June–August 2026 · Sample prepared November 2026</p>
    </article>
  </div>
  <p class="ms-note">These three sources measure different things. Their figures should not be combined into one AI market score or treated as evidence that one trend caused another.</p>
</div></section>

<section class="ms-section ms-section--paper" aria-labelledby="ms-decisions-title"><div class="container">
  <div class="ms-section-head">
    <div><p class="ms-overline">Executive applications</p>
      <h2 id="ms-decisions-title">Executive decisions that benefit from market context.</h2></div>
    <p class="ms-section-intro">For AI, Data and Analytics leaders, CIO/CDO teams and executive sponsors. Market evidence helps challenge a plan; your own business evidence is still needed to choose what to do.</p>
  </div>
  <div class="ms-decision-list">
    <article class="ms-usecase"><span class="ms-label">Capability sourcing</span>
      <h3>Internal capability, recruitment or external expertise</h3>
      <p>Use selected leadership advertisements and wider consulting figures to test a sourcing assumption—then compare options against what your organisation needs.</p></article>
    <article class="ms-usecase"><span class="ms-label">Business value</span>
      <h3>Business outcomes beyond reported adoption</h3>
      <p>Look beyond reported adoption. Discuss how your organisation measures outcomes, handles its data and assigns responsibility for results.</p></article>
    <article class="ms-usecase"><span class="ms-label">Recruitment decisions</span>
      <h3>Recruitment assumptions and observed advertisements</h3>
      <p>See which job titles were included, how monthly counts vary and why advertisements alone cannot establish a talent shortage.</p></article>
    <article class="ms-usecase"><span class="ms-label">Management discussion</span>
      <h3>Presenting evidence and uncertainty to management</h3>
      <p>Bring a sourced interpretation, its alternative explanations and a practical question to the discussion.</p></article>
  </div>
</div></section>

<section class="ms-section ms-section--ink" id="ms-inside" aria-labelledby="ms-workspace-title"><div class="container">
  <div class="ms-section-head">
    <div><p class="ms-overline" style="color:#E6B48B">Research workspace</p>
      <h2 id="ms-workspace-title">The Market Observatory: measures, comparisons and source records.</h2></div>
    <p class="ms-section-intro">The member Observatory has eight sections. Edition 01 contains published figures on AI use, selected leadership adverts and consulting activity. Skills, pay and wider sector figures are still being reviewed, so those sections do not yet contain a complete set of data.</p>
  </div>
  <div class="ms-workspace">
    <div class="ms-dashboard-list" aria-label="Market Signals dashboard sections">
      <article><span>01 / OVERVIEW</span><h3>Executive evidence overview</h3><p>Start with selected findings and see the dates and groups they cover.</p></article>
      <article><span>02 / LEADERSHIP ADVERTS</span><h3>AI &amp; Data leadership advertisements</h3><p>Follow a defined set of senior job advertisements by complete month and region.</p></article>
      <article><span>03 / AI IN BUSINESS</span><h3>Enterprise AI adoption &amp; capabilities</h3><p>Explore SCB figures on AI use, analytics and barriers, with their different survey groups kept separate.</p></article>
      <article><span>04 / UNDER REVIEW</span><h3>Skills and management pay — under review</h3><p>Additional skills and salary measures are being checked; they are not published in Edition 01.</p></article>
      <article><span>05 / CONSULTING</span><h3>Consulting and sector context</h3><p>See Brainville's October consulting figures. Further sector indicators are awaiting review.</p></article>
      <article><span>06 / EXPLANATIONS</span><h3>Interpretation and evidence limits</h3><p>See what published figures suggest, what else might explain them and where comparisons stop.</p></article>
      <article><span>07 / HISTORY</span><h3>Comparable historical observations</h3><p>Compare completed periods within the same measure; partial months are shown separately.</p></article>
      <article><span>08 / ORIGINAL RECORDS</span><h3>Sources and measurement methods</h3><p>Check original links, dates, survey groups and limitations, and export the source list.</p></article>
    </div>
    <aside class="ms-path">
      <p class="ms-overline" style="color:#EDB994">Analytical approach</p>
      <h3>A structured assessment of the evidence.</h3>
      <ol>
        <li><strong>Define the decision.</strong>What are you trying to decide about investment, capability or people?</li>
        <li><strong>Establish the evidence base.</strong>Check the figure, its date and the group it actually describes.</li>
        <li><strong>Test alternative explanations.</strong>Understand what the figure cannot tell you.</li>
        <li><strong>Record the implications.</strong>Download the report or decision brief and record what you still need to know.</li>
      </ol>
      <p class="ms-path-caption">Monthly archive: November 2026 is the complete published edition. June–October 2026 show retrospective leadership-advertisement records only, not full monthly reports.</p>
      <div class="ms-actions"><a class="ms-button" href="?page=advisory-access&amp;view=market-signals" target="_self" data-hq-event="market_signals_dashboard_cta">Open Market Signals</a></div>
    </aside>
  </div>
</div></section>

<section class="ms-section ms-section--white" aria-labelledby="ms-materials-title"><div class="container">
  <div class="ms-section-head">
    <div><p class="ms-overline">Published research / Member access</p>
      <h2 id="ms-materials-title">Research publications and supporting records.</h2></div>
    <p class="ms-section-intro">Choose the format that suits your next discussion: examine the data, read the complete research or take a focused decision brief.</p>
  </div>
  <div class="ms-formats">
    <article class="ms-format"><small>01 / EXPLORE ONLINE</small>
      <h3>Market Observatory</h3>
      <p>Use the dashboard sections, monthly archive and source records to explore published observations. Some topics have limited coverage while their sources are being reviewed.</p>
      <div class="ms-format-bottom">Interactive views · Historical records · Source details</div></article>
    <article class="ms-format"><small>02 / DOWNLOAD A4 PDF</small>
      <h3>Complete AI &amp; Data Market Review</h3>
      <p>The November 2026 research edition examines adoption, Data and Analytics capabilities, leadership advertisements and consulting conditions. It includes alternative explanations, an executive decision agenda and all 30 published observations.</p>
      <div class="ms-format-bottom">Edition 01 · Full research PDF · Source appendix</div></article>
    <article class="ms-format"><small>03 / USE IN A MEETING</small>
      <h3>Decision briefs and source register</h3>
      <p>Choose one of four written analyses and download its PDF, including the supporting figures and a printable decision record. You can also export the published source list as a CSV file.</p>
      <div class="ms-format-bottom">Four decision themes · Decision brief PDF · Source CSV</div></article>
  </div>
</div></section>

<section class="ms-section ms-section--paper" aria-labelledby="ms-standards-title"><div class="container">
  <div class="ms-section-head">
    <div><p class="ms-overline">Sources and methods</p>
      <h2 id="ms-standards-title">Source provenance, definitions and limitations.</h2></div>
    <p class="ms-section-intro">Every figure in the published edition has a source, date, defined group and explanation of its limits. We distinguish what the publisher measured from what we think it may mean for a leader.</p>
  </div>
  <div class="ms-standard">
    <div>
      <ul class="ms-source-list">
        <li><strong>Statistics Sweden (SCB)</strong>National survey figures on AI use, data analysis and barriers to adoption. The 2026 survey changed its industry coverage, which matters for year-on-year comparisons.</li>
        <li><strong>Arbetsförmedlingen JobTech</strong>A selected set of senior AI/Data job advertisements drawn from public records. It is not a count of all vacancies or completed hires.</li>
        <li><strong>Brainville</strong>October 2026 changes in a broad Swedish consulting marketplace. These figures do not measure AI-specialist availability.</li>
      </ul>
      <p class="ms-note">Other proposed data on skills, management pay and sector conditions are not included until their sources and definitions are checked.</p>
    </div>
    <aside class="ms-quality">
      <h3>Limits of the published evidence.</h3>
      <p><strong>Business value from AI</strong>Reported use alone cannot tell us.</p>
      <p><strong>AI leadership talent shortages</strong>A small selection of job adverts cannot establish that.</p>
      <p><strong>Availability of specialist AI consultants</strong>Broad consulting marketplace activity cannot answer that.</p>
      <p class="ms-small">Those questions need additional evidence. This service does not use private job-search records or personal hiring forecasts to make market claims.</p>
    </aside>
  </div>
</div></section>

<section class="ms-lastcta" aria-labelledby="ms-cta-title"><div class="container">
  <div class="ms-cta-grid">
    <div>
      <p class="ms-overline" style="color:#E9B88E">Research access</p>
      <h2 id="ms-cta-title">November 2026: Research and supporting evidence.</h2>
      <p>Read the complete November review, explore the published dashboard data and download decision briefs you can use with your team. The research will help you examine a choice; it will not make a company-specific recommendation for you.</p>
      <div class="ms-actions">
        <a class="ms-button" href="?page=advisory-access&amp;view=market-signals" target="_self" data-hq-event="market_signals_final_register">Access Edition 01 · Free account</a>
        <a class="ms-button ms-button--outline" href="?page=advisory-access&amp;view=market-signals&amp;signin=1" target="_self" data-hq-event="market_signals_final_signin">Already registered? Sign in</a>
      </div>
    </div>
    <aside class="ms-cta-aside"><strong>Intended readers</strong>
      <p>Enterprise AI leaders, Data &amp; Analytics executives, CIO/CDO teams and executive sponsors responsible for capability, investment and operating-model decisions.</p>
      <p>Registration is free. No personal approval is needed; once your Advisory account is verified, you can use the research yourself.</p>
    </aside>
  </div>
</div></section>

</main>
"""

def advisory_market_signals() -> str:
    """Executive-market-intelligence service landing page; no privileged API reads."""
    return (
        SERVICES_CSS
        + MARKET_SIGNALS_LANDING_CSS
        + nav("advisory")
        + MARKET_SIGNALS_LANDING_HTML.replace(
            "</main>",
            portfolio_next_navigation("advisory-market-signals") + "</main>",
        )
        + footer()
    )

def _checked_url(value: str) -> str:
    value = str(value or "")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Market evidence source is not a trusted HTTPS URL.")
    return value


def _load_curated(token: str) -> tuple[list[dict], list[dict]]:
    if not token:
        raise PermissionError("A verified Advisory session is required.")
    def catalogue(table: str, order: str, max_rows: int = 2000) -> list[dict]:
        batch_size=200
        results=[]
        for offset in range(0,max_rows,batch_size):
            batch=_request_json(
                "GET",
                _rest_url(f"{table}?select=*&is_published=eq.true&order={order}"
                          f"&limit={batch_size}&offset={offset}"),
                token=token,timeout=12,
            )
            if not isinstance(batch,list):
                raise RuntimeError("Published market catalogue is not readable.")
            results.extend(batch)
            if len(batch)<batch_size:
                return results
        raise RuntimeError("Published catalogue exceeds the verified page limit.")

    p=catalogue("portfolio_market_signal_points","period_end.asc")
    b=catalogue("portfolio_market_signal_briefs","published_on.desc")
    if not isinstance(p, list) or not isinstance(b, list) or not p or not b:
        raise RuntimeError("Verified market evidence is unavailable.")
    seen = set()
    for item in p:
        key = str(item.get("code") or "")
        if not key or key in seen:
            raise ValueError("Market evidence catalogue contains a missing or duplicate identifier.")
        seen.add(key)
        _checked_url(str(item.get("source_url") or ""))
        if item.get("value") is None or item.get("evidence_grade") not in {"primary","derived","contextual"}:
            raise ValueError("Market evidence failed completeness checks.")
        if not item.get("period_start") or not item.get("period_end") or not item.get("verified_on"):
            raise ValueError("Market evidence lacks a date or verification stamp.")
    by_code = {p["code"]: p for p in p}
    for brief in b:
        codes = brief.get("evidence_codes")
        if not isinstance(codes, list) or len(codes) < 2 or any(c not in by_code for c in codes):
            raise ValueError("An executive interpretation references unavailable evidence.")
        families = {by_code[c]["source_family"] for c in codes}
        if brief.get("support_level") == "independent_sources" and len(families) < 2:
            raise ValueError("Independent verification claimed without two source families.")
        if not brief.get("counterevidence") or not brief.get("limitations"):
            raise ValueError("An executive interpretation is missing its limitations.")
    return p, b


INITIAL_PREVIEW_CODES = frozenset({
    "brainville_202610_assignments_yoy","brainville_202610_consultants_yoy",
    "jobtech_v1_jun_se","jobtech_v1_jun_vgr","jobtech_v1_jun_sto",
    "jobtech_v1_jul_se","jobtech_v1_jul_vgr","jobtech_v1_jul_sto",
    "jobtech_v1_aug_se","jobtech_v1_aug_vgr","jobtech_v1_aug_sto",
    "jobtech_v1_sep_se","jobtech_v1_sep_vgr","jobtech_v1_sep_sto",
    "jobtech_v1_oct_se","jobtech_v1_oct_vgr","jobtech_v1_oct_sto",
    "jobtech_v1_nov15_se","jobtech_v1_nov15_vgr","jobtech_v1_nov15_sto",
    "scb_2026_ai_10plus","scb_2026_ai_250plus",
    "scb_2026_ai_10to49","scb_2026_ai_50to249",
    "scb_2026_ai_data_quality_barrier","scb_2026_ai_expertise_barrier",
    "scb_2026_ai_privacy_barrier","scb_2026_analytics_internal",
    "scb_2026_bi_use","scb_2026_data_analytics_use",
    "scb_2026_ict_specialists",
})

def _release_snapshot(token: str, points: list[dict], briefs: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Bind published editions to the same approved evidence as the executive PDFs.

    The initial 2026 catalogue remains a clearly marked pre-release preview
    until the owner completes the first formal editorial source approval.
    """
    response=_request_json(
        "POST",_rest_url("rpc/portfolio_market_signals_current_release_v1"),
        token=token,payload={},timeout=10,
    )
    if not isinstance(response,dict) or type(response.get("published")) is not bool:
        raise RuntimeError("Verified editorial release state unavailable.")
    if not response["published"]:
        # The pre-release preview is a frozen, historically disclosed catalogue.
        # Publishing a later point cannot silently add it to member dashboards;
        # new datasets require a signed-off versioned edition manifest.
        preview=[p for p in points if p["code"] in INITIAL_PREVIEW_CODES]
        preview_codes={p["code"] for p in preview}
        preview_briefs=[b for b in briefs
                        if set(b["evidence_codes"]).issubset(preview_codes)]
        if len(preview)!=len(INITIAL_PREVIEW_CODES) or not preview_briefs:
            raise ValueError("Frozen pre-release catalogue cannot be verified.")
        return preview,preview_briefs,response
    codes=response.get("evidence_codes")
    slugs=response.get("brief_slugs")
    if not isinstance(codes,list) or not isinstance(slugs,list) or len(codes)<2 or not slugs:
        raise ValueError("Published edition has an incomplete evidence manifest.")
    point_map={p["code"]:p for p in points}
    brief_map={b["slug"]:b for b in briefs}
    if len(set(codes))!=len(codes) or len(set(slugs))!=len(slugs):
        raise ValueError("Published edition includes duplicate references.")
    if any(x not in point_map for x in codes) or any(x not in brief_map for x in slugs):
        raise ValueError("The published edition refers to missing data or analysis.")
    selected_points=[point_map[c] for c in codes]
    selected_briefs=[brief_map[c] for c in slugs]
    selected_codes=set(codes)
    for brief in selected_briefs:
        if not set(brief["evidence_codes"]).issubset(selected_codes):
            raise ValueError("Executive analysis cites evidence outside its published edition.")
    if len({p["source_family"] for p in selected_points})<2:
        raise ValueError("A published edition requires independent source families.")
    return selected_points,selected_briefs,response


def _freshness(point: dict, today: date | None = None) -> str:
    today = today or date.today()
    verified = date.fromisoformat(str(point["verified_on"])[:10])
    allowed = SOURCE_CADENCE_DAYS.get(point.get("source_family"), 90)
    return "Review overdue" if (today - verified).days > allowed else "Verified"


def _value(point: dict) -> str:
    number = float(point["value"])
    shown = f"{int(number):,}" if number.is_integer() else f"{number:,.1f}"
    unit = str(point["metric_unit"])
    return shown + ("%" if unit == "percent" else " " + unit)


def _head(kicker: str, title: str, copy: str = "") -> None:
    st.html(
        '<section class="market-head"><span class="market-kicker">'
        + html_escape(kicker) + '</span><h3>' + html_escape(title) + '</h3>'
        + ('<p>' + html_escape(copy) + '</p>' if copy else "") + '</section>'
    )


def _plot(points: list[dict], lens: str, geography: str) -> None:
    selected = [p for p in points if p["lens"] == lens and p["geography"] == geography]
    if lens == "leadership":
        complete = sorted(
            (p for p in selected if p["period_complete"]),
            key=lambda p: p["period_end"]
        )
        if not complete:
            st.warning("There are no complete monthly observations for this geography.")
            return
        table = pd.DataFrame({
            "Period": [p["period_label"] for p in complete],
            "Month": pd.to_datetime([p["period_start"] for p in complete]),
            "Advertisements": [int(p["value"]) for p in complete],
        })
        chart = alt.Chart(table).mark_line(
            color=PALETTE["navy"], point={"filled": True, "fill": PALETTE["copper"], "size": 82},
            strokeWidth=3,
        ).encode(
            x=alt.X("Month:T", title="Publication month", axis=alt.Axis(format="%b %Y")),
            y=alt.Y("Advertisements:Q", title="Qualifying advertisements", scale=alt.Scale(zero=True)),
            tooltip=["Period:N", alt.Tooltip("Advertisements:Q", format=",d")],
        ).properties(height=290)
        st.altair_chart(chart, use_container_width=True)
        partial = sorted(
            (p for p in selected if not p["period_complete"]),
            key=lambda p: p["period_end"]
        )
        if partial:
            last = partial[-1]
            st.caption(
                f"Latest incomplete period: {last['period_label']} — {_value(last)}. "
                "Excluded from the full-month trend because the windows differ."
            )
        st.caption(
            "Frozen JobTech headline-only title basket v1, not total vacancies or completed hires. "
            "Small samples, indexed coverage and retrospective API revisions restrict conclusions."
        )
    else:
        latest = {}
        for p in sorted(selected, key=lambda x: x["period_end"]):
            latest[p["series_code"]] = p
        rows = list(latest.values())
        if not rows:
            st.warning("No source-supported observations are available for this selection.")
            return
        # Axis ticks truncate long survey indicator names on tablets. Render
        # every label as wrapping text above its own bar; keep units and vintage.
        bar_rows = [{
            "label": p["metric_label"],
            "value": float(p["value"]),
            "display_value": _value(p),
            "period": p["period_label"],
            "source": p.get("source_title") or p.get("source_family") or "",
        } for p in sorted(rows, key=lambda item: float(item["value"]), reverse=True)]
        st.html(labelled_bars_html(
            bar_rows, color=PALETTE["navy"], unit_label="original source units"
        ))
        if lens == "consulting":
            st.caption("Brainville figures cover all consulting disciplines, not AI/Data-specific consulting.")
        if lens in ("adoption","capability"):
            st.caption(
                "SCB enterprise survey 2026. Bar denominators differ for adoption rates and "
                "barriers among non-adopters; do not compare them as shares of the same population."
            )


def _safe_csv(points: list[dict]) -> bytes:
    output = StringIO()
    w = csv.writer(output)
    w.writerow(["metric","value","unit","geography","period","period_complete","population",
                "source_family","source_title","source_url","published_on","verified_on",
                "evidence_grade","methodology","caveat"])
    for p in points:
        cells = [p.get(k,"") for k in (
            "metric_label","value","metric_unit","geography","period_label",
            "period_complete","population_note","source_family","source_title","source_url",
            "published_on","verified_on","evidence_grade","methodology","caveat"
        )]
        w.writerow(["'"+str(v) if str(v).startswith(("=","+","-","@")) and not isinstance(v,(int,float)) else v for v in cells])
    return output.getvalue().encode("utf-8-sig")


def _pdf_safe(text: object) -> str:
    """Keep PDF library's base font predictable while retaining text semantics."""
    return html_escape(str(text if text is not None else "").replace("\u2013", "-")
                       .replace("\u2014", "-").replace("\u2019", "'").replace("\u2022", "-")
                       .encode("latin-1","replace").decode("latin-1"))


def executive_pdf(points: list[dict], brief: dict, geography: str) -> bytes:
    """Source-linked A4 market analysis + executive decision record; no private user inputs."""
    by_code = {p["code"]:p for p in points}
    support = [by_code[c] for c in brief["evidence_codes"]]
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
        topMargin=24*mm, bottomMargin=19*mm,
        title="AI & Data Market Signals - Executive Decision Brief",
        author="Jair Ribeiro | Enterprise AI & Data Leader",
    )
    title = ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=24,leading=29,textColor=colors.HexColor(PALETTE["navy"]),spaceAfter=16)
    h = ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=12,leading=17,textColor=colors.HexColor(PALETTE["navy"]),spaceBefore=12,spaceAfter=7)
    body = ParagraphStyle("body",fontName="Helvetica",fontSize=9.5,leading=15,textColor=colors.HexColor(PALETTE["ink"]),spaceAfter=9)
    small = ParagraphStyle("small",fontName="Helvetica",fontSize=7.8,leading=11,textColor=colors.HexColor(PALETTE["muted"]),spaceAfter=5)
    copper = colors.HexColor(PALETTE["copper"])
    story = [
        Paragraph("AI &amp; DATA MARKET SIGNALS",small),
        HRFlowable(width="100%",thickness=2,color=copper),
        Spacer(1,13),
        Paragraph("Executive market decision brief",title),
        Paragraph(_pdf_safe(brief["title"]),h),
        Paragraph(_pdf_safe(brief["thesis"]),body),
        Paragraph("Edition: "+_pdf_safe(brief["published_on"]) +
                  " | Primary geography: Sweden | Selected geography: "+_pdf_safe(geography),small),
        Paragraph("What the evidence says",h),
        Paragraph(_pdf_safe(brief["interpretation"]),body),
        Paragraph("The executive decision",h),
        Paragraph(_pdf_safe(brief["decision_question"]),body),
        Paragraph("Proposed first action",h),
        Paragraph(_pdf_safe(brief["recommended_action"]),body),
        Paragraph("What could challenge this reading?",h),
        Paragraph(_pdf_safe(brief["counterevidence"]),body),
        Paragraph("Confidence boundary",h),
        Paragraph(_pdf_safe(brief["limitations"]),body),
        Paragraph(
            "Independent source families: "+
            str(len({p["source_family"] for p in support}))+
            ". This describes independent evidence streams, not proof of causation. "
            "All statistics retain original populations and observation windows.",small),
        PageBreak(),
        Paragraph("Evidence record",title),
        Paragraph(
            "The following metrics are the specific supporting observations for this decision. "
            "They are not broad claims about every vacancy, business or AI investment.",body)
    ]
    for i,p in enumerate(support,1):
        link = _checked_url(p["source_url"])
        block = [
            Paragraph(f"{i:02d} / "+_pdf_safe(p["metric_label"]),h),
            Paragraph(_pdf_safe(_value(p))+" | "+_pdf_safe(p["geography"])+" | "+
                      _pdf_safe(p["period_label"]),body),
            Paragraph("Population: "+_pdf_safe(p["population_note"]),small),
            Paragraph("Publisher: "+_pdf_safe(p["source_title"]) +
                      " | Released "+_pdf_safe(p["published_on"]) +
                      " | Verified "+_pdf_safe(p["verified_on"]),small),
            Paragraph("Caution: "+_pdf_safe(p["caveat"]),small),
            Paragraph('<link href="'+html_escape(link,quote=True)+'" color="#1B557A">'+
                      _pdf_safe(link)+'</link>',small),
            Spacer(1,4),
        ]
        story.append(KeepTogether(block))
    story.extend([
        PageBreak(), Paragraph("Leadership decision record",title),
        Paragraph("This record is a structured working tool, not an automated investment verdict.",body),
    ])
    fields = [
        ("Decision to be taken",brief["decision_question"]),
        ("What internal outcome should change?","_____________________________________________________________"),
        ("Decision owner and accountable business function","_____________________________________________________________"),
        ("Current baseline and strongest alternative","_____________________________________________________________"),
        ("Evidence missing before commitment","_____________________________________________________________"),
        ("What would change the recommendation?","_____________________________________________________________"),
        ("First 30-day action and owner","_____________________________________________________________"),
        ("Next review date / stop-or-scale threshold","_____________________________________________________________"),
    ]
    for label,value in fields:
        story.append(Paragraph(_pdf_safe(label),h))
        story.append(Paragraph(_pdf_safe(value),body))
        story.append(Spacer(1,5))
    story.extend([
        Spacer(1,12),
        Paragraph("Prepared from verified and curated market observations. "
                  "No private career intelligence, individual interviews or personal hiring forecasts are included.",small),
    ])
    def frame(canvas, document):
        canvas.saveState()
        w,h= A4
        canvas.setFillColor(colors.HexColor(PALETTE["navy"]))
        canvas.rect(0,h-13*mm,w,13*mm,stroke=0,fill=1)
        canvas.setFont("Helvetica-Bold",8)
        canvas.setFillColor(colors.white)
        canvas.drawString(18*mm,h-8*mm,"JAIR RIBEIRO  /  MARKET INTELLIGENCE")
        canvas.setStrokeColor(colors.HexColor(PALETTE["line"]))
        canvas.line(18*mm,14*mm,w-18*mm,14*mm)
        canvas.setFont("Helvetica",8)
        canvas.setFillColor(colors.HexColor(PALETTE["muted"]))
        canvas.drawString(18*mm,9*mm,"jairribeiro.com  /  Evidence-led Executive Advisory")
        canvas.drawRightString(w-18*mm,9*mm,f"{document.page}")
        canvas.restoreState()
    doc.build(story,onFirstPage=frame,onLaterPages=frame)
    result = buf.getvalue()
    if not result.startswith(b"%PDF") or len(result) < 2000:
        raise ValueError("Market brief PDF failed output validation.")
    return result


def _record_market_event(token: str, event: str, lens: str = "", detail: str = "") -> None:
    """Best-effort anonymous usage event. Never submit user notes or private responses."""
    if not token or event not in {"open","lens","decision","pdf_decision","pdf_review","csv_evidence"}:
        return
    try:
        _request_json(
            "POST", _rest_url("rpc/portfolio_market_signals_record_event_v1"),
            token=token, timeout=6,
            payload={"p_event":event,"p_lens":lens[:50],"p_detail":detail[:120]},
        )
    except (RuntimeError,ValueError,TimeoutError,KeyError,OSError):
        # Observability must never block verified evidence access.
        pass


def render_private_market_signals(session: dict, user: dict) -> None:
    """Only called after Advisory profile, password, membership and role checks."""
    token = str(session.get("access_token") or "")
    with st.container(key="market_signals_workspace"):
        st.html(MARKET_STYLE)
        st.html(
            '<section class="market-hero"><span class="eyebrow">'
            'JAIR RIBEIRO ADVISORY / MARKET INTELLIGENCE</span>'
            '<h2>AI &amp; Data Market Signals</h2>'
            '<p>Evidence before interpretation. Understand the market, challenge the assumptions, '
            'and make a better capability decision.</p></section>'
        )
        try:
            points, briefs = _load_curated(token)
            points, briefs, release = _release_snapshot(token,points,briefs)
            from market_archive import (
                load_market_archives,archive_option_label,archive_coverage
            )
            monthly_archives=load_market_archives(token)
        except (RuntimeError, PermissionError, ValueError, KeyError, TimeoutError, OSError) as exc:
            st.error("The verified market evidence or monthly archive is unavailable. "
                     "No cached or invented figures will be substituted.")
            return
        if not monthly_archives:
            st.error("No immutable monthly edition is available for viewing.")
            return
        selected_month=st.selectbox(
            "Market observatory · Monthly editions",
            monthly_archives,
            format_func=archive_option_label,
            key="market_signals_monthly_vintage",
            help="Choose the complete published edition or a separately labelled "
                 "retrospective JobTech-only monthly reconstruction."
        )
        historical=selected_month["archive_kind"]=="retrospective_title_basket"
        points=list(selected_month["observations"])
        briefs=list(selected_month["interpretations"])
        if not historical:
            release={
                "published":True,"issue_date":str(selected_month["first_published_at"])[:10],
                "slug":selected_month.get("edition_slug"),
                "title":selected_month["title"],
            }
        st.caption(archive_coverage(selected_month))
        issue_month=date.fromisoformat(str(selected_month["month_start"])[:10]).strftime("%B %Y")
        issue_label=str(selected_month["first_published_at"])[:10]
        statement=(
            "Historical reconstruction verified in November 2026. "
            "Not a contemporary full-market edition. "
            if historical else
            "Frozen published executive market edition, released " + html_escape(issue_label) + ". "
        )
        st.html(
            '<section class="market-editorial-status" aria-label="Editorial status">'
            '<strong>Market Intelligence · '+html_escape(issue_month)+'</strong>'
            '<p>' + statement +
            'Evidence-linked indicators with transparent reporting periods, '
            'source references and methodological limitations.</p></section>'
        )
        viewer_key = "market_signals_open_" + str(user.get("id") or "member")
        if not st.session_state.get(viewer_key):
            _record_market_event(token,"open")
            st.session_state[viewer_key] = True
        family_count = len({p["source_family"] for p in points})
        periods = [str(p["verified_on"])[:10] for p in points]
        st.caption(
            f"Curated observations: {len(points)}  ·  Source families: {family_count}  ·  "
            f"Latest evidence verification: {max(periods)}  ·  Geography: Sweden"
        )
        overdue = [p for p in points if _freshness(p) == "Review overdue"]
        if overdue:
            st.warning(
                f"{len(overdue)} observations have passed their source-specific recheck interval. "
                "Their last verified values are retained with dates; the tool will not present them as current."
            )
        from page_advisory_market_observatory import render_market_observatory
        if not historical:
            # The published V2 analysis is edition-bound and is available only
            # through the same verified member JWT as the approved observations.
            from market_intelligence_v2 import (
                load_published_editorial, render_executive_intelligence,
            )
            try:
                v2 = load_published_editorial(
                    token, str(release.get("slug") or ""), points,
                    _request_json, _rest_url,
                )
            except (PermissionError, RuntimeError, ValueError, KeyError, OSError):
                st.error(
                    "The executive analysis cannot be verified for this edition. "
                    "No inferred or unchecked market conclusions will be shown."
                )
                return
            if v2 is not None:
                render_executive_intelligence(
                    st, v2, points, str(release["slug"]), token, _record_market_event,
                )
                with st.expander("Explore the underlying evidence and historical charts",
                                 expanded=False):
                    render_market_observatory(points,historical=False)
                return
        render_market_observatory(points,historical=historical)
        if historical:
            from page_advisory_market_demo import historical_market_pdf
            st.markdown("#### Download this historical evidence record")
            st.caption(
                "This PDF analyses only the selected complete-month frozen JobTech "
                "observations. Broader AI adoption, Data capabilities and consulting "
                "conditions cannot be reconstructed from this older monthly cohort."
            )
            st.download_button(
                "Download historical market snapshot · PDF",
                data=historical_market_pdf(points,month_label=issue_month),
                file_name="Jair_Ribeiro_Historical_Market_"+str(selected_month["month_start"])[:7]+".pdf",
                mime="application/pdf",
                key="market_historical_pdf",
                use_container_width=True,
            )
            return
        lens = str(st.session_state.get("market_observatory_section") or "pulse")
        geo = "Sweden"
        if st.session_state.get("market_signals_previous_lens") != lens:
            _record_market_event(token,"lens",lens)
            st.session_state["market_signals_previous_lens"] = lens
        _head("EDITORIAL INTERPRETATION","What the observed signals mean for the decisions ahead",
              "The dashboard shows factual evidence; this companion analysis records executive judgement, counterarguments and the next practical decision.")
        selected_brief = st.selectbox(
            "Decision theme",range(len(briefs)),format_func=lambda ix:briefs[ix]["title"],
            key="market_signals_decision",
        )
        brief=briefs[selected_brief]
        if st.session_state.get("market_signals_previous_decision") != brief["slug"]:
            _record_market_event(token,"decision",str(lens),str(brief["slug"]))
            st.session_state["market_signals_previous_decision"] = brief["slug"]
        grade=brief["support_level"]
        grade_label=("Two or more independent source families" if grade=="independent_sources"
                     else "Single-source analysis" if grade=="single_source" else "Context only")
        st.html(
            '<article class="market-thesis"><span class="market-kicker">'+html_escape(grade_label)+
            '</span><h3>'+html_escape(brief["title"])+'</h3><p>'+html_escape(brief["thesis"])+
            '</p></article>'
        )
        st.write(brief["interpretation"])
        st.html('<section class="market-outcome"><strong>DECISION TO MAKE</strong><p>'+
                html_escape(brief["decision_question"])+'</p><strong>FIRST ACTION</strong><p>'+
                html_escape(brief["recommended_action"])+'</p></section>')
        with st.expander("Challenge the conclusion · counterevidence and limitations",expanded=True):
            st.markdown("**What could change this reading**")
            st.write(brief["counterevidence"])
            st.markdown("**What these data cannot establish**")
            st.write(brief["limitations"])
            if grade=="independent_sources":
                st.caption("Independent source families offer contextual triangulation, not independent replication of the same metric.")
        by_code={p["code"]:p for p in points}
        support=[by_code[c] for c in brief["evidence_codes"]]
        _head("EVIDENCE TRAIL","Trace every claim to its origin")
        for p in support:
            source=_checked_url(p["source_url"])
            st.html(
                '<div class="market-source"><strong>'+html_escape(p["metric_label"])+
                ' · '+html_escape(_value(p))+'</strong><small>'+
                html_escape(p["geography"]+' · '+p["period_label"]+' · '+p["population_note"])+
                '</small><small>Source: <a href="'+html_escape(source,quote=True)+
                '" target="_blank" rel="noopener noreferrer">'+html_escape(p["source_title"])+
                '</a> · Published '+html_escape(p["published_on"])+' · Verified '+
                html_escape(p["verified_on"])+' · '+html_escape(_freshness(p))+
                '</small></div>'
            )
        _head("YOUR MATERIALS","Take this analysis into the leadership meeting",
              "The PDF includes an executive interpretation, evidence appendix with links, and a printable decision record.")
        try:
            data=executive_pdf(points,brief,geo)
        except (ValueError, KeyError, OSError):
            st.error("The report cannot be generated reliably from the current evidence.")
        else:
            st.download_button(
                "Download executive market decision brief · PDF",
                data=data,
                file_name="Jair_Ribeiro_AI_Data_Market_Decision_Brief.pdf",
                mime="application/pdf",
                key="market_signals_pdf",type="primary",
                use_container_width=True,
                on_click=_record_market_event,
                args=(token,"pdf_decision",str(lens),str(brief["slug"])),
            )
        st.markdown("#### Complete Market Review")
        st.caption(
            "A complete source-led executive research edition: independent reading "
            "of enterprise AI adoption, data and analytical capability, leadership "
            "advertisement trends, regional distinctions and consulting conditions. "
            "Includes alternative explanations, decision tests, executive discussion "
            "agenda and a traceable register of all approved observations. "
            "No unsupported data or unpublished sources."
        )
        try:
            from page_advisory_market_review import market_review_pdf
            market_pdf=market_review_pdf(points,briefs,release)
        except (ValueError, KeyError, OSError) as exc:
            st.error("The complete market review cannot be validated for export.")
        else:
            st.download_button(
                "Download complete AI & Data Market Review · PDF",
                data=market_pdf,
                file_name="Jair_Ribeiro_AI_Data_Market_Review_2026_11.pdf",
                mime="application/pdf",
                key="market_review_pdf",
                use_container_width=True,
                on_click=_record_market_event,
                args=(token,"pdf_review","all","market-review"),
            )
        st.caption("Market Signals edition 1.0 · Independent research interpretation by Jair Ribeiro. "
                   "Not investment, recruitment or legal advice. Source populations, releases and methods govern the figures.")
