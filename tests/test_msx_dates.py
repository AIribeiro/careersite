from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_msx_public_dates_do_not_expose_specific_june_end() -> None:
    impact = (ROOT / "src/page_impact.py").read_text(encoding="utf-8")
    canonical_cv = (ROOT / "src/site_cv.py").read_text(encoding="utf-8")
    fallback_cv = (ROOT / "src/site_assets.py").read_text(encoding="utf-8")

    for text in (impact, canonical_cv, fallback_cv):
        assert "Dec 2025 – Jun 2026" not in text
        assert "Dec 2025 - Jun 2026" not in text
        assert "Dec 2025 – June 2026" not in text
        assert "Dec 2025 - June 2026" not in text

    assert "Dec 2025 – 2026 · Gothenburg" in impact
    assert '"Dec 2025 - 2026"' in canonical_cv
    assert "Dec 2025 - 2026 | Gothenburg, Sweden" in fallback_cv
