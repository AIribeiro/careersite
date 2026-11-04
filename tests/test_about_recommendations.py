from __future__ import annotations

import json
from html import unescape
from pathlib import Path
import unittest

from about_recommendations import load_recommendations, recommendations_section


ROOT = Path(__file__).resolve().parents[1]


class AboutRecommendationTests(unittest.TestCase):
    def test_home_does_not_repeat_recommendations(self) -> None:
        home = (ROOT / "src" / "page_home.py").read_text(encoding="utf-8")
        self.assertNotIn("Comments from people I worked with.", home)
        self.assertNotIn("reference_claes_home", home)
        self.assertNotIn("reference_anna_home", home)

    def test_about_includes_full_recommendation_section(self) -> None:
        about = (ROOT / "src" / "page_about.py").read_text(encoding="utf-8")
        self.assertIn("from about_recommendations import recommendations_section", about)
        self.assertIn("{recommendations_section()}", about)

    def test_all_original_recommendations_are_retained(self) -> None:
        records = load_recommendations()
        self.assertEqual(len(records), 23)
        self.assertEqual(len({record["name"] for record in records}), 23)
        for item in records:
            self.assertTrue(item["name"])
            self.assertTrue(item["role"])
            self.assertTrue(item["date"])
            self.assertTrue(item["relationship"])
            self.assertTrue(item["quote"])
            self.assertIn(item["group"], {"Enterprise AI & leadership", "Enterprise technology & collaboration", "Community & leadership"})
        self.assertEqual(sum(1 for item in records if item.get("featured")), 4)

    def test_full_texts_and_link_destinations_are_available(self) -> None:
        records = load_recommendations()
        markup = unescape(recommendations_section())
        for item in records:
            self.assertIn(item["name"], markup)
            self.assertIn(item["quote"], markup)
            self.assertIn(item["relationship"], markup)
            self.assertIn(item["role"], markup)
        self.assertEqual(markup.count("about-rec-item-name"), 20)  # 1 CSS selector + 19 entries
        self.assertEqual(markup.count("<details class=\"about-rec-item\">"), 19)
        self.assertIn("LinkedIn profile", markup)
        self.assertIn("Find on LinkedIn", markup)
        self.assertIn("2026", markup)

    def test_high_signal_recommendations_are_featured_in_direct_manager_order(self) -> None:
        markup = recommendations_section()
        featured = ("Claes Sandros", "Anna Börjesson Sandberg", "Kumara Datta", "Jim Edwards")
        pos = [markup.index(f"<h3>{name}</h3>") for name in featured]
        self.assertEqual(pos, sorted(pos))
        self.assertIn("Read the complete recommendation", markup)

    def test_no_new_network_dependency_or_user_tracking(self) -> None:
        source = (ROOT / "src" / "about_recommendations.py").read_text(encoding="utf-8")
        self.assertNotIn("requests.get", source)
        self.assertNotIn("st.components", source)
        self.assertNotIn("<img", recommendations_section())
        self.assertNotIn("<script", recommendations_section())


if __name__ == "__main__":
    unittest.main()
