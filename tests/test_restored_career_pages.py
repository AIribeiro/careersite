"""Restored public Certifications and Speaking/Publications destinations."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_certifications_and_presence_are_not_redirected_to_about() -> None:
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "LEGACY_PRESENCE_LINK" not in main
    assert "LEGACY_CREDENTIALS_LINK" not in main
    assert '"certifications", "presence"' in main
    assert '"certifications": "AI, Data & Leadership Certifications | Jair Ribeiro"' in main
    assert '"presence": "Speaking & Publications | Jair Ribeiro"' in main
    assert 'elif PAGE == "certifications":' in main
    assert "from page_certifications import certifications" in main
    assert 'elif PAGE == "presence":' in main
    assert "from page_presence import presence" in main
    assert "render_page = certifications" in main
    assert "render_page = presence" in main


def test_restored_pages_render_the_existing_original_content() -> None:
    from page_certifications import certifications
    from page_presence import presence

    credentials = certifications()
    publication = presence()
    assert "Selected AI, data and leadership credentials." in credentials
    assert "EITCA/AI Artificial Intelligence Academy" in credentials
    assert "Microsoft Leadership and Innovation" in credentials
    assert "Verify credential" in credentials
    assert "Selected speaking, publications and external contributions." in publication
    assert "Generative AI Summit" in publication
    assert "Financial Times" in publication
    assert "Digital First Magazine" in publication
    assert credentials.count("<main>") == 1
    assert publication.count("<main>") == 1
    assert credentials.count("</main>") == 1
    assert publication.count("</main>") == 1


def test_about_and_cv_link_to_distinct_public_destinations() -> None:
    about = (ROOT / "src/page_about.py").read_text(encoding="utf-8")
    for route in ("certifications", "presence"):
        assert f'href="?page={route}"' in about
    from career_facts import CERTIFICATIONS_URL, PRESENCE_URL
    assert CERTIFICATIONS_URL == "https://jairribeiro.com/?page=certifications&utm_source=cv"
    assert PRESENCE_URL == "https://jairribeiro.com/?page=presence&utm_source=cv"


def test_restored_pages_use_about_nav_and_same_standard_footer() -> None:
    from about_next_navigation import portfolio_next_navigation
    from site_portfolio_continuation import inject_portfolio_continuation
    from site_components import nav

    for page in ("certifications", "presence"):
        menu = nav(page)
        assert 'class="link on"' in menu
        assert 'href="?page=about"' in menu
        assert "class=\"about-next portfolio-next\"" in portfolio_next_navigation(page)
        document = f"<main><p>{page}</p></main><footer>Test</footer>"
        finished = inject_portfolio_continuation(document, page)
        assert finished.count('class="about-next portfolio-next"') == 1
        assert finished.index('class="about-next portfolio-next"') < finished.index("</main>")
