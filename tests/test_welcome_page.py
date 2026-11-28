"""Source contract for the dedicated professional welcome route."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WelcomePageTests(unittest.TestCase):
    def test_route_and_shared_design(self):
        page = (ROOT / "src/page_welcome.py").read_text()
        main = (ROOT / "main.py").read_text()
        self.assertIn('elif PAGE == "welcome":', main)
        self.assertIn('render_page = welcome', main)
        self.assertIn('nav("welcome")', page)
        self.assertIn('footer()', page)
        for route in ("impact", "ai-data-governance", "thinking", "briefings", "advisory", "about", "cv", "readers", "contact"):
            self.assertIn(route, page)
        self.assertIn('data-analytics-section="welcome-portfolio-guide"', page)
        self.assertIn('data-hq-event="welcome_', page)
        compile(page, "page_welcome.py", "exec")

    def test_analytics_route_and_privacy(self):
        aggregate = (ROOT / "src/site_aggregate_traffic.py").read_text()
        meta = (ROOT / "src/site_meta.py").read_text()
        self.assertIn('"welcome"', aggregate)
        self.assertIn("page === 'welcome' ? 'noindex,follow'", meta)
