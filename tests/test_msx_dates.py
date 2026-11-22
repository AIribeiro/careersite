from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_msx_public_dates_are_september_2026_across_portfolio_and_cv() -> None:
    facts = (ROOT / "src/career_facts.py").read_text(encoding="utf-8")
    home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
    impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
    canonical_cv = (ROOT / "src/site_cv.py").read_text(encoding="utf-8")
    fallback_cv = (ROOT / "src/site_assets.py").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/build-cv.yml").read_text(encoding="utf-8")

    assert 'MSX_PUBLIC_DATES = "Dec 2025 - Sep 2026"' in facts
    assert 'MSX_PUBLIC_TIMELINE = "2025–2026"' in facts
    assert "MSX_PUBLIC_DATES" in home
    assert "MSX_PUBLIC_DATES" in impact
    assert "MSX_PUBLIC_DATES" in canonical_cv
    assert "MSX_PUBLIC_DATES" in fallback_cv
    assert '"Dec 2025 - Sep 2026"' in workflow

    for text in (facts, home, impact, canonical_cv, fallback_cv, workflow):
        assert "Dec 2025 - Jun 2026" not in text
        assert "Dec 2025 – Jun 2026" not in text


def test_volvo_operational_work_precedes_director_foundations() -> None:
    home = (ROOT / "src/page_home.py").read_text(encoding="utf-8")
    impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
    cv = (ROOT / "src/site_cv.py").read_text(encoding="utf-8")
    cases = (ROOT / "src/portfolio_operating_evidence.py").read_text(encoding="utf-8")

    assert "Enterprise AI &amp; Data Leader" in home
    assert "Volvo Group / Volvo Trucks" in impact
    assert "MSX International" in impact
    assert "MSX_PUBLIC_DATES" in impact
    assert "explicit Director-level role at MSX International" in cv
    assert "working multilingual GenAI Customer Interview Analyzer" in cv
    assert "did not proceed to a production rollout" in cases
    assert "portfolio decision criteria" in impact or "portfolio review" in cases
