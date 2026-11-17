"""Regression contracts for the homepage's executive market announcement.

Automated route discovery must not promote placeholder descriptions or
historical demos ahead of the actual signed-off executive research edition.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"scripts"))

import home_whats_new as news
import sync_portfolio_releases as releases

TITLE="Sweden’s AI & Data Market: Evidence for Executive Decisions"
HREF="?page=advisory-market-signals"


class ExecutiveHomeAnnouncementTests(unittest.TestCase):
    def test_new_research_outranks_historical_demo(self):
        with patch.object(news,"_credential_items",return_value=()):
            item=news.latest_local_release(
                datetime(2026,11,17,12,0,tzinfo=timezone.utc)
            )
        self.assertEqual(item.type,"Executive research")
        self.assertEqual(item.title,TITLE)
        self.assertEqual(item.href,HREF)
        self.assertEqual(item.cta,"Read the executive review")
        self.assertIn("43 published observations",item.description)
        self.assertIn("business confidence",item.description)
        self.assertIn("five executive perspectives",item.description.lower())

    def test_historical_sample_and_placeholder_never_become_home_feature(self):
        entries=news._static_items()
        self.assertNotIn("?page=advisory-market-demo",[item.href for item in entries])
        self.assertFalse(any(
            "Discover the newly published portfolio page" in item.description
            for item in entries
        ))
        feed=json.loads((ROOT/"data/portfolio_release_feed.json").read_text(encoding="utf-8"))
        demo=next(x for x in feed["items"] if x["key"]=="page:advisory-market-demo")
        self.assertIs(demo["promote_home"],False)

    def test_home_markup_clearly_explains_offer_and_links_to_main_service(self):
        with patch.object(news,"_credential_items",return_value=()):
            markup=news.home_whats_new()
        self.assertIn(TITLE,markup)
        self.assertIn("recruitment demand",markup)
        self.assertIn("three outlook scenarios",markup)
        self.assertIn('href="?page=advisory-market-signals"',markup)
        self.assertIn("Read the executive review",markup)
        self.assertNotIn('href="?page=advisory-market-demo"',markup)
        self.assertIn("clamp(13px,1.25vw,15px)/1.68",news.NEWS_CSS)

    def test_metadata_parser_keeps_literal_entries_when_home_value_is_dynamic(self):
        descriptions=releases.constant(
            (ROOT/"src/site_meta.py").read_text(encoding="utf-8"),"DESCRIPTIONS"
        )
        self.assertIn("advisory-market-signals",descriptions)
        self.assertIn("Swedish AI",descriptions["advisory-market-signals"])
        titles=releases.constant((ROOT/"main.py").read_text(encoding="utf-8"),"TITLES")
        self.assertIn("advisory-market-signals",titles)
        self.assertNotIn("home",titles)

    def test_route_autodiscovery_never_reintroduces_generic_demo(self):
        old="PUBLIC_VALID = {'home'}\nTITLES = {'home': HOME_TITLE}\n"
        new=("PUBLIC_VALID = {'home', 'advisory-market-demo', "
             "'advisory-market-signals', 'advisory-renewal'}\n"
             "TITLES = {'home': HOME_TITLE, "
             "'advisory-market-signals': 'AI & Data Market Intelligence | Jair Ribeiro', "
             "'advisory-renewal': 'AI Portfolio Renewal Advisor | Jair Ribeiro'}\n")
        meta=("DESCRIPTIONS = {'home': HOME_DESCRIPTION, "
              "'advisory-market-signals': 'Independent executive research "
              "on Swedish AI adoption, recruitment and business confidence "
              "with sourced decision perspectives.', "
              "'advisory-renewal': 'Review ongoing AI investments against "
              "operating results, risk and feasibility to decide where "
              "to invest and what should stop.'}\n")
        def fake_git_file(rev,path):
            if path=="main.py":
                return old if rev=="before" else new
            return meta if rev=="after" else ""
        with patch.object(releases,"git_file",side_effect=fake_git_file):
            entries=releases.new_release_items("before","after","2026-11-17T10:30:00+01:00")
        keys={x["key"] for x in entries}
        self.assertIn("page:advisory-market-signals",keys)
        self.assertIn("page:advisory-renewal",keys)
        self.assertNotIn("page:advisory-market-demo",keys)
        for entry in entries:
            self.assertGreaterEqual(len(entry["description"]),60)
            self.assertNotIn("Discover the newly published portfolio page.",entry["description"])
        market=next(e for e in entries if e["key"]=="page:advisory-market-signals")
        self.assertEqual(market["title"],"AI & Data Market Intelligence")
        self.assertEqual(market["cta"],"Explore the research")


if __name__=="__main__":
    unittest.main()
