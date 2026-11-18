"""Ensure the CV distributed to recruiters links only to the branded portfolio."""
from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from career_facts import CERTIFICATIONS_URL, PORTFOLIO_CV_URL, PRESENCE_URL
from site_cv import build_public_cv


def test_generated_cv_uses_jairribeiro_domain_for_all_portfolio_links() -> None:
    reader = PdfReader(BytesIO(build_public_cv()), strict=True)
    assert len(reader.pages) == 2
    links = {
        str(action["/URI"])
        for page in reader.pages
        for ref in page.get("/Annots", [])
        if (action := ref.get_object().get("/A")) and action.get("/URI")
    }
    expected = {
        "https://jairribeiro.com/?source=cv",
        "https://jairribeiro.com/?page=certifications&utm_source=cv",
        "https://jairribeiro.com/?page=presence&utm_source=cv",
    }
    assert {PORTFOLIO_CV_URL, CERTIFICATIONS_URL, PRESENCE_URL} == expected
    assert expected <= links
    assert all("streamlit.app" not in url.lower() for url in links)
