"""Contact page: three routes fill the row without a blank right-hand cell."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_contact_routes_preserve_exactly_three_actions() -> None:
    page = (ROOT / "src/page_contact.py").read_text(encoding="utf-8")
    assert 'id="contact-pathways"' in page
    section = page.split('id="contact-pathways"', 1)[1].split("contact-closing", 1)[0]
    assert 'class="grid3 contact-pathways-grid"' in section
    assert section.count('<article class="card">') == 3
    for item in ("Leadership &amp; speaking", "Selective pro-bono advisory",
                 "Free Executive AI Reader Library"):
        assert item in section
    assert 'data-hq-event="contact_personal_route"' in section
    assert 'data-hq-event="contact_advisory_route"' in section
    assert 'data-hq-event="contact_reader_route"' in section
    assert '{portfolio_next_navigation("contact")}' in page
    assert 'contact-footer-links' in page


def test_contact_routes_use_all_columns_by_viewport() -> None:
    css = (ROOT / "src/site_styles.py").read_text(encoding="utf-8")
    assert ".site #contact-pathways .contact-pathways-grid{" in css
    assert "grid-template-columns:repeat(3,minmax(0,1fr));" in css
    assert "@media(min-width:701px) and (max-width:849px)" in css
    assert ".site #contact-pathways .contact-pathways-grid>.card:last-child{" in css
    assert "grid-column:1/-1;" in css
    assert "@media(max-width:700px)" in css
    assert "grid-template-columns:minmax(0,1fr);" in css


def test_contact_styling_is_scoped_to_contact_not_other_grids() -> None:
    css = (ROOT / "src/site_styles.py").read_text(encoding="utf-8")
    section = css.split("/* Contact direct routes:", 1)[1].split("</style>", 1)[0]
    assert all(".site #contact-pathways " in selector
               for selector in [
                   ".site #contact-pathways .head",
                   ".site #contact-pathways .contact-pathways-grid",
                   ".site #contact-pathways .contact-pathways-grid>.card:last-child",
               ])
    assert ".site #operating-evidence" not in section
    assert ".site #governance-evidence" not in section
