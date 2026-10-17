"""ASGI article permalinks preserve legitimate UTM tags for human visits."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
import unittest

from starlette.datastructures import QueryParams


class ArticleShareRedirectTests(unittest.TestCase):
    def test_human_reader_redirect_retains_attribution_and_blocks_route_override(self):
        import app as launcher
        from site_cms import CmsArticle

        slug = "ai-is-entering-the-management-layer-leadership-has-to-catch-up"
        article = CmsArticle(title="AI Is Entering the Management Layer", slug=slug,
                             status="published")
        request = SimpleNamespace(
            path_params={"slug": slug},
            headers={"user-agent": "Mozilla/5.0"},
            query_params=QueryParams(
                "source=linkedin&utm_source=linkedin&utm_medium=social"
                "&utm_campaign=thinking&utm_content=" + slug +
                "&page=admin&article=unrelated&workspace=cms&source=facebook"
            ),
        )
        with patch.object(
            launcher, "fetch_public_article",
            side_effect=AssertionError("Human redirects must not call CMS"),
        ):
            response = asyncio.run(launcher._thinking_article(request))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["cache-control"], "no-store")
        result = urlparse(response.headers["location"])
        self.assertEqual(result.netloc, "jairribeiro-ai.streamlit.app")
        params = parse_qs(result.query)
        self.assertEqual(params["page"], ["thinking"])
        self.assertEqual(params["article"], [slug])
        self.assertEqual(params["source"], ["linkedin"])
        self.assertEqual(params["utm_source"], ["linkedin"])
        self.assertEqual(params["utm_medium"], ["social"])
        self.assertEqual(params["utm_campaign"], ["thinking"])
        self.assertEqual(params["utm_content"], [slug])
        self.assertNotIn("workspace", params)

    def test_reported_cms_article_redirect_is_independent_of_cms_availability(self):
        import app as launcher

        slug = "ai-is-turning-data-definitions-into-a-leadership-problem"
        request = SimpleNamespace(
            path_params={"slug": slug},
            headers={"user-agent": "Mozilla/5.0 Safari/605.1"},
            query_params=QueryParams(
                "source=linkedin&utm_source=linkedin&utm_medium=social"
                "&utm_campaign=thinking&utm_content=" + slug
            ),
        )
        with patch.object(
            launcher, "fetch_public_article",
            side_effect=RuntimeError("CMS unavailable"),
        ):
            response = asyncio.run(launcher._thinking_article(request))
        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.headers["location"])
        self.assertEqual(parsed.path, "/")
        params = parse_qs(parsed.query)
        self.assertEqual(params["article"], [slug])
        self.assertEqual(params["utm_campaign"], ["thinking"])

    def test_linkedin_crawler_receives_og_html_not_redirect(self):
        import app as launcher
        from site_cms import CmsArticle

        article = CmsArticle(title="A CMS Article", slug="a-cms-article",
                             status="published")
        request = SimpleNamespace(
            path_params={"slug": article.slug},
            headers={"user-agent": "LinkedInBot/1.0"},
            query_params=QueryParams("source=linkedin"),
        )
        html = '<html><head><meta property="og:title" content="A CMS Article"></head></html>'
        with patch.object(launcher, "fetch_public_article", return_value=article), \
             patch.object(launcher, "cms_share_document", return_value=html):
            response = asyncio.run(launcher._thinking_article(request))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'property="og:title"', response.body)
        self.assertNotIn("location", response.headers)


if __name__ == "__main__":
    unittest.main()
