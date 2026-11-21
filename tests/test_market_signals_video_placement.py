"""Placement contract for the same approved horizontal Market Signals film.

The public viewer and authenticated member MUST share the exact media and
section markup. Neither viewer may receive the mobile portrait/thumbnail slot.
"""
from __future__ import annotations

import inspect
import unittest
from unittest.mock import patch

from page_advisory_market_signals import (
    MARKET_SIGNALS_LANDING_HTML,
    MARKET_SIGNALS_LANDING_CSS,
    MARKET_SIGNALS_VIDEO_HTML,
    _extract_market_signals_video,
    render_market_signals_member_video,
    render_private_market_signals,
)

EXACT_WEB_MASTER = (
    "https://rnqweoxtynelfirffmlr.supabase.co/storage/v1/object/public/"
    "portfolio-public-videos/market-signals/unionen-2026-11/"
    "website-eafa2f511a32.mp4"
)

class MarketVideoPlacementContract(unittest.TestCase):
    def test_public_landscape_video_is_between_hero_and_editions(self):
        page=MARKET_SIGNALS_LANDING_HTML
        self.assertEqual(page.count('id="ms-video"'),1)
        self.assertEqual(page.count('class="ms-video-player"'),1)
        i_hero=page.index('<section class="ms-hero"')
        i_summary=page.index('class="ms-issue-line"')
        i_video=page.index('<section class="ms-section ms-section--video"')
        i_editions=page.index('<section class="ms-section ms-section--paper" id="ms-perspectives"')
        i_unionen=page.index('id="ms-workforce-update"')
        self.assertLess(i_hero,i_summary)
        self.assertLess(i_summary,i_video)
        self.assertLess(i_video,i_editions)
        self.assertLess(i_editions,i_unionen)
        self.assertEqual(page.count(EXACT_WEB_MASTER),3)  # direct CTA, source, video fallback
        self.assertEqual(MARKET_SIGNALS_VIDEO_HTML,_extract_market_signals_video(page))

    def test_player_is_native_landscape_not_thumbnail_or_center_crop(self):
        css=MARKET_SIGNALS_LANDING_CSS
        self.assertIn("aspect-ratio:16 / 9",css)
        self.assertIn("object-fit:contain",css)
        self.assertIn(".ms-video-figure{width:100%;max-width:920px",css)
        self.assertNotIn("aspect-ratio:512 / 910",css)
        self.assertNotIn(".ms-video-figure{width:100%;max-width:215px",css)
        self.assertNotIn("autoplay",MARKET_SIGNALS_VIDEO_HTML)
        self.assertIn("controls playsinline webkit-playsinline preload=\"metadata\"",MARKET_SIGNALS_VIDEO_HTML)

    def test_member_html_reuses_the_exact_public_player(self):
        rendered=[]
        with patch("page_advisory_market_signals.st.html",side_effect=rendered.append):
            render_market_signals_member_video()
        self.assertEqual(len(rendered),1)
        member=rendered[0]
        self.assertIn(MARKET_SIGNALS_VIDEO_HTML,member)
        self.assertIn("site ms-landing ms-market-video-auth",member)
        self.assertIn("aspect-ratio:16 / 9",member)
        self.assertIn("ms-video-player",member)
        self.assertIn(EXACT_WEB_MASTER,member)
        self.assertNotIn('id="ms-perspectives"',member)
        self.assertEqual(member.count('<video '),1)

    def test_authenticated_video_is_after_member_hero_before_report_controls(self):
        source=inspect.getsource(render_private_market_signals)
        intro=source.index('st.html(\n            \'<section class="market-hero"')
        video=source.index("        render_market_signals_member_video()")
        records=source.index("        try:\n            points, briefs = _load_curated(token)")
        selector=source.index('        selected_month=st.selectbox(')
        self.assertLess(intro,video)
        self.assertLess(video,records)
        self.assertLess(records,selector)
        self.assertNotIn("autoplay",MARKET_SIGNALS_VIDEO_HTML)

if __name__=="__main__": unittest.main()
