from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ArticleAnalyticsTests(unittest.TestCase):
    def test_article_client_is_session_scoped_and_tracks_content_interactions(self) -> None:
        source = (ROOT / "src/site_article_analytics.py").read_text(encoding="utf-8")

        for token in (
            "article_view",
            "article_click",
            "article_share",
            "article_slug",
            "article_action",
            "article_engaged_ms",
            "jair_hq_session_v1",
            "jair_hq_attribution_v1",
            "jair_hq_article_engaged_v2",
            "sessionStorage",
        ):
            self.assertIn(token, source)

        self.assertIn("FIRST_HEARTBEAT_MS = 5000", source)
        self.assertIn("HEARTBEAT_MS = 10000", source)
        self.assertIn("SESSION_TIMEOUT_MS = 30 * 60 * 1000", source)
        self.assertIn("jair_hq_started_v3", source)
        self.assertIn("jair_hq_engaged_v3", source)
        self.assertIn("jair_hq_last_active_v3", source)
        self.assertIn("__jairArticleScheduleFirstHeartbeat", source)
        self.assertNotIn("localStorage", source)
        self.assertNotIn("document.cookie", source)
        self.assertNotIn("user_agent", source)

    def test_runtime_orders_article_tracking_before_generic_analytics(self) -> None:
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        guard = (ROOT / "src/site_share_guard.py").read_text(encoding="utf-8")

        self.assertIn("inject_article_analytics", main)
        self.assertIn("inject_share_guard", main)
        self.assertIn("page_analytics_v2", main)
        self.assertLess(main.index("inject_article_analytics(PAGE"), main.index("inject_share_guard()"))
        self.assertLess(main.index("inject_share_guard()"), main.index("inject_analytics(PAGE"))
        self.assertIn("article_share_", guard)
        self.assertIn("stopImmediatePropagation", guard)

    def test_private_dashboard_has_article_intelligence(self) -> None:
        article_dashboard = (ROOT / "src/page_article_analytics.py").read_text(encoding="utf-8")
        wrapper = (ROOT / "src/page_analytics_v2.py").read_text(encoding="utf-8")

        for token in (
            "careersite_analytics_articles_v2",
            "Article visits & interactions",
            "Most-read articles",
            "Active reading time",
            "Most-shared articles",
            "Share channels",
            "Tagged acquisition source",
            "Article views",
            "Measured sessions",
            "Engaged reads",
        ):
            self.assertIn(token, article_dashboard)

        self.assertIn("Duration unconfirmed", article_dashboard)
        self.assertIn("median_active_seconds", article_dashboard)
        self.assertIn("confirmed_duration_sessions", article_dashboard)
        self.assertIn("render_site_analytics_dashboard()", wrapper)
        self.assertIn("render_article_analytics()", wrapper)
        self.assertNotIn("st.dataframe", article_dashboard)


if __name__ == "__main__":
    unittest.main()
