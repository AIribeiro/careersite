"""Regression checks for gap-free evidence and shared footer layouts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_all_three_evidence_sections_have_scoped_responsive_grid() -> None:
    evidence = _read("src/portfolio_operating_evidence.py")
    governance = _read("src/page_ai_data_governance.py")
    assert evidence.count('class="grid3 evidence-cards-grid"') == 2
    assert governance.count('class="grid3 evidence-cards-grid"') == 1
    for section in ("leadership-in-practice", "operating-evidence", "governance-evidence"):
        assert f'id="{section}"' in evidence + governance
    # Preserve case copy and content rather than filling missing grid cells
    # with invented projects or duplicated cards.
    assert "Customer Interview Analyzer" in evidence
    assert "80+ AI opportunities" in evidence
    assert "100+ AI learning sessions" in evidence


def test_tablet_grids_do_not_leave_a_blank_right_hand_cell() -> None:
    css = _read("src/site_styles.py")
    assert "@media(min-width:800px) and (max-width:980px)" in css
    assert ".site .evidence-cards-grid{grid-template-columns:repeat(3,minmax(0,1fr))}" in css
    assert "@media(min-width:701px) and (max-width:799px)" in css
    assert ".site .evidence-cards-grid>.card:last-child{grid-column:1/-1}" in css
    assert "@media(max-width:700px)" in css
    assert ".site .evidence-cards-grid{grid-template-columns:minmax(0,1fr);gap:12px}" in css


def test_shared_next_navigation_uses_current_tablet_and_masked_frame_breakpoints() -> None:
    # The compact three-column footer was updated after this test originally
    # assumed the retired 740-900px breakpoint. Preserve the actual live
    # desktop / tablet / masked-frame contract rather than reintroducing the
    # earlier cramped layout merely to satisfy a stale expectation.
    css = _read("src/site_styles.py")
    nav = _read("src/about_next_navigation.py")
    assert "@media(min-width:721px)" in css
    assert ".site .portfolio-next .about-next-grid{" in css
    assert "grid-template-columns:repeat(3,minmax(0,1fr));" in css
    assert "@media(min-width:541px) and (max-width:720px)" in css
    assert "@media(min-device-width:541px) and (max-device-width:720px)" in css
    assert ".site .portfolio-next .about-next-grid>a.about-next-card:last-child{" in css
    assert "grid-column:1/-1;" in css
    assert "@media(max-width:540px)" in css
    assert ".site .portfolio-next a.about-next-card{" in css
    assert "min-height:0;" in css
    assert "Continue exploring the portfolio" in nav
    assert 'class="about-next portfolio-next"' in nav


def test_governance_research_spacing_has_specific_scope() -> None:
    css = _read("src/site_styles.py")
    governance = _read("src/page_ai_data_governance.py")
    assert 'id="governance-research"' in governance
    assert ".site #governance-research{" in css
    assert "padding-block:clamp(46px,5vw,68px);" in css
