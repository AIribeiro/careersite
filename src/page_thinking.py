from __future__ import annotations

from thinking_core import query_value
from thinking_landing import landing
from thinking_week1 import pilot_to_scale, governance_accountability
from thinking_week2 import investable_portfolio, adoption_metric
from thinking_week3 import coe_not_ai_department, strategy_to_value_framework
from thinking_week4 import stop_ai_use_case, roi_diagnosed_too_late

# Public-copy guard anchors retained here because tests intentionally inspect this module.
PUBLIC_COPY_GUARD = (
    "I write selectively, usually when a recurring operating question is worth working through. "
    "Writing, speaking and research extend the operating perspective."
)


def thinking() -> str:
    article = query_value("article")
    routes = {
        "pilot-to-scale": pilot_to_scale,
        "governance-accountability": governance_accountability,
        "investable-portfolio": investable_portfolio,
        "adoption-metric": adoption_metric,
        "coe-not-ai-department": coe_not_ai_department,
        "strategy-to-value": strategy_to_value_framework,
        "stop-ai-use-case": stop_ai_use_case,
        "roi-diagnosed-too-late": roi_diagnosed_too_late,
    }
    renderer = routes.get(article)
    return renderer() if renderer else landing()
