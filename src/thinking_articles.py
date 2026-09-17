from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

BASE_URL = "https://jairribeiro-ai.streamlit.app"


@dataclass(frozen=True)
class ArticleMeta:
    key: str
    slug: str
    aliases: tuple[str, ...]
    title: str
    kind: str
    topic: str
    standfirst: str
    published_iso: str
    published_label: str
    read_minutes: int
    seo_title: str
    seo_description: str
    social_title: str
    social_description: str
    tags: tuple[str, ...]

    @property
    def kind_topic(self) -> str:
        return f"{self.kind} · {self.topic}"

    @property
    def read_label(self) -> str:
        return f"{self.published_label} · {self.read_minutes} min read"


ARTICLES: tuple[ArticleMeta, ...] = (
    ArticleMeta(
        key="pilot_to_scale",
        slug="why-enterprise-ai-often-stalls-between-pilot-and-scale",
        aliases=("pilot-to-scale",),
        title="Why Enterprise AI Often Stalls Between Pilot and Scale",
        kind="Point of view",
        topic="Enterprise AI",
        standfirst="A pilot can prove that an AI idea works. It does not prove that the organization is ready to own it, operate it, govern it and create repeatable value from it.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=3,
        seo_title="Why Enterprise AI Stalls Between Pilot and Scale | Jair Ribeiro",
        seo_description="Why enterprise AI pilots fail to scale: ownership, evidence, data accountability, governance and adoption matter as much as technical success.",
        social_title="Why Enterprise AI Often Stalls Between Pilot and Scale",
        social_description="Technical success proves possibility. Enterprise scale requires ownership, evidence, governance, adoption and operating capability.",
        tags=("Enterprise AI", "AI Scale", "AI Adoption", "AI Operating Model", "AI Governance"),
    ),
    ArticleMeta(
        key="governance_accountability",
        slug="the-ai-governance-gate-i-would-never-remove",
        aliases=("governance-accountability",),
        title="The AI Governance Gate I Would Never Remove",
        kind="Decision note",
        topic="AI Governance",
        standfirst="AI governance should become lighter when risk is lower. Human accountability should not.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=2,
        seo_title="The AI Governance Gate I Would Never Remove | Jair Ribeiro",
        seo_description="Why enterprise AI governance can be proportionate without weakening explicit human accountability for real business decisions.",
        social_title="The AI Governance Gate I Would Never Remove",
        social_description="Controls can be proportionate and lightweight. Human accountability for consequential AI decisions cannot be implicit.",
        tags=("AI Governance", "Responsible AI", "Human Accountability", "Enterprise AI"),
    ),
    ArticleMeta(
        key="investable_portfolio",
        slug="from-ai-use-case-list-to-investable-portfolio",
        aliases=("investable-portfolio",),
        title="From AI Use-Case List to Investable Portfolio",
        kind="Field note",
        topic="Portfolio & Value",
        standfirst="A long list of AI ideas is evidence of demand. It is not evidence of strategy.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=3,
        seo_title="From AI Use Cases to an Investable Portfolio | Jair Ribeiro",
        seo_description="How enterprise AI leaders turn use-case inventories into investable portfolios through staged evidence, explicit choices and the ability to stop work.",
        social_title="From AI Use-Case List to Investable Portfolio",
        social_description="An AI portfolio is not a catalogue of possibilities. It is a sequence of investment decisions under constraint.",
        tags=("AI Portfolio", "AI Value", "AI Strategy", "Investment Decisions", "Enterprise AI"),
    ),
    ArticleMeta(
        key="adoption_metric",
        slug="one-ai-adoption-metric-i-dont-trust",
        aliases=("adoption-metric",),
        title="One AI Adoption Metric I Don’t Trust",
        kind="Decision note",
        topic="AI Adoption",
        standfirst="Active users can tell me that people opened the tool. They cannot tell me that work changed.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=3,
        seo_title="One AI Adoption Metric I Don't Trust | Jair Ribeiro",
        seo_description="Why licenses, logins and active users are useful signals of reach but insufficient evidence of AI adoption without measurable workflow and behavior change.",
        social_title="One AI Adoption Metric I Don’t Trust",
        social_description="Usage shows reach. Adoption becomes meaningful when a workflow, decision or behavior actually changes.",
        tags=("AI Adoption", "AI Metrics", "Change Management", "Enterprise AI"),
    ),
    ArticleMeta(
        key="coe_not_ai_department",
        slug="the-ai-coe-should-not-become-the-companys-ai-department",
        aliases=("coe-not-ai-department",),
        title="The AI CoE Should Not Become the Company’s AI Department",
        kind="Point of view",
        topic="AI Operating Model",
        standfirst="A Center of Excellence should make the enterprise better at owning AI. If every use case still depends on the center, the organization has concentrated activity rather than built capability.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=6,
        seo_title="Why the AI CoE Should Not Become the AI Department | Jair Ribeiro",
        seo_description="A practical view of AI Center of Excellence design: centralize reusable capability and governance, while distributing business ownership and outcomes.",
        social_title="The AI CoE Should Not Become the Company’s AI Department",
        social_description="A strong AI CoE builds distributed capability. It should not become the permanent owner of every AI use case and business outcome.",
        tags=("AI CoE", "AI Operating Model", "Enterprise AI", "Federated AI", "AI Leadership"),
    ),
    ArticleMeta(
        key="strategy_to_value_framework",
        slug="strategy-portfolio-governance-adoption-value",
        aliases=("strategy-to-value",),
        title="Strategy → Portfolio → Governance → Adoption → Value",
        kind="Framework",
        topic="Enterprise AI",
        standfirst="A five-link management framework for connecting AI ambition to operating choices, changed work and measurable business outcomes.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=4,
        seo_title="Strategy → Portfolio → Governance → Adoption → Value | Jair Ribeiro",
        seo_description="A five-link enterprise AI framework connecting strategy, portfolio choices, governance, adoption and measurable business value.",
        social_title="Strategy → Portfolio → Governance → Adoption → Value",
        social_description="A simple management chain for connecting enterprise AI ambition to investment choices, responsible scale, changed work and outcomes.",
        tags=("AI Strategy", "AI Portfolio", "AI Governance", "AI Adoption", "AI Value"),
    ),
    ArticleMeta(
        key="stop_ai_use_case",
        slug="when-an-ai-use-case-should-be-stopped",
        aliases=("stop-ai-use-case",),
        title="When an AI Use Case Should Be Stopped",
        kind="Field note",
        topic="AI Portfolio & Value",
        standfirst="AI portfolios need explicit exit criteria. A technically credible use case can still be the wrong place for the next unit of investment.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=5,
        seo_title="When an AI Use Case Should Be Stopped | Jair Ribeiro",
        seo_description="Six signals that an AI use case should be stopped or reconsidered, from weak value mechanisms and adoption costs to changed portfolio priorities.",
        social_title="When an AI Use Case Should Be Stopped",
        social_description="Stopping is not portfolio failure. The real failure is continuing to fund AI work after evidence shows weak value, high adoption cost or changed priorities.",
        tags=("AI Portfolio", "AI Value", "AI Use Cases", "Investment Decisions", "Enterprise AI"),
    ),
    ArticleMeta(
        key="roi_diagnosed_too_late",
        slug="ai-roi-is-often-diagnosed-too-late",
        aliases=("roi-diagnosed-too-late",),
        title="AI ROI is often diagnosed too late.",
        kind="Decision note",
        topic="AI Value",
        standfirst="If value only becomes a serious question after deployment, the portfolio has already missed the most useful moment to shape it.",
        published_iso="2026-09-17",
        published_label="17 Sep 2026",
        read_minutes=1,
        seo_title="AI ROI Is Often Diagnosed Too Late | Jair Ribeiro",
        seo_description="Why AI ROI should be designed from discovery through a clear value mechanism connecting workflow change, adoption, operational effect and outcome.",
        social_title="AI ROI is often diagnosed too late",
        social_description="ROI starts with the value mechanism, not the post-launch dashboard. Define the causal chain before major investment.",
        tags=("AI ROI", "AI Value", "AI Portfolio", "Business Value", "Enterprise AI"),
    ),
)

BY_KEY = {article.key: article for article in ARTICLES}
BY_SLUG = {article.slug: article for article in ARTICLES}
for _article in ARTICLES:
    for _alias in _article.aliases:
        BY_SLUG[_alias] = _article


def resolve_article(value: str | None) -> ArticleMeta | None:
    if not value:
        return None
    return BY_SLUG.get(str(value).strip().lower())


def article_by_key(key: str) -> ArticleMeta:
    return BY_KEY[key]


def article_relative_url(article: ArticleMeta) -> str:
    """Internal Streamlit navigation URL."""
    return f"?page=thinking&article={article.slug}"


def article_app_url(article: ArticleMeta) -> str:
    """Direct Streamlit article URL used as the human redirect target."""
    return f"{BASE_URL}/?page=thinking&article={article.slug}"


def article_url(article: ArticleMeta) -> str:
    """Canonical and social-friendly public article URL."""
    return f"{BASE_URL}/thinking/{article.slug}"


def article_social_image_url(article: ArticleMeta) -> str:
    return f"{BASE_URL}/social/{article.slug}.png"


def article_share_url(article: ArticleMeta) -> str:
    return article_url(article)


def published_articles() -> Iterable[ArticleMeta]:
    return ARTICLES
