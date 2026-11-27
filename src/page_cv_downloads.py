from __future__ import annotations

from pathlib import Path
from site_assets import CV_URI
from site_components import nav, footer, CV_DOWNLOAD_NAME

STATIC = Path(__file__).resolve().parents[1] / "static"

def cv_downloads() -> str:
    def link(variant, filename, label, event, primary=False):
        if not (STATIC / filename).is_file():
            return '<p class="muted" role="status">This format is being refreshed. Please use the available PDF.</p>'
        href = CV_URI if variant == "executive" else "/cv-download/" + variant
        style = "btn primary" if primary else "btn dark"
        return f'<a class="{style}" href="{href}" download="{filename}" data-hq-event="{event}">{label} ↓</a>'

    executive = link("executive", CV_DOWNLOAD_NAME, "Download executive PDF", "cv_download_executive_pdf")
    word = link("ats-docx", "Jair_Ribeiro_CV_ATS.docx", "Download Word CV", "cv_download_ats_docx", True)
    ats_pdf = link("ats-pdf", "Jair_Ribeiro_CV_ATS.pdf", "Download recruitment PDF", "cv_download_ats_pdf")
    return f'''{nav("cv")}<main>
<section class="pagehero"><div class="container"><p class="eyebrow">Career profile · Curriculum vitae</p><h1>Download my CV.</h1><p>The same professional experience, presented in formats suited to different recruitment processes. Choose the version that best fits how the CV will be reviewed or processed.</p></div></section>
<section class="section paper" aria-labelledby="cv-formats-title" id="cv-downloads"><div class="container">
<div class="head"><div><p class="eyebrow">Three formats · One career history</p><h2 id="cv-formats-title">Choose the right format.</h2></div><p>For a direct introduction or executive review, choose the executive PDF. For an application portal, use the recruitment-ready Word file if accepted, or the simplified PDF when required.</p></div>
<style>
.site #cv-downloads .cv-format-grid>.card{{display:flex;flex-direction:column;min-width:0}}
.site #cv-downloads .cv-format-grid h3{{margin:15px 0 12px}}
.site #cv-downloads .cv-format-action{{margin-top:auto;padding-top:18px}}
.site #cv-downloads .cv-format-action .btn{{white-space:normal;max-width:100%}}
@media(max-width:700px),(max-device-width:700px){{.site #cv-downloads .cv-format-grid{{grid-template-columns:1fr}}}}
</style>
<div class="grid3 cv-format-grid">
<article class="card"><span class="org">Human review · PDF</span><h3>Executive CV</h3><p>A concise, visually structured overview of my career and leadership experience, designed for recruiters, hiring managers, executive search and direct introductions.</p><p><strong>Best for:</strong> human review and professional networking.</p><div class="cv-format-action">{executive}</div></article>
<article class="card"><span class="org">Automated applications · DOCX</span><h3>Recruitment-ready CV — Word</h3><p>A single-column document with clearly separated employment, qualifications, skills and language fields to help applicant tracking systems (ATS) interpret the information.</p><p><strong>Best for:</strong> Workday and other application portals that accept Word documents.</p><div class="cv-format-action">{word}</div></article>
<article class="card"><span class="org">Automated applications · PDF</span><h3>Recruitment-ready CV — PDF</h3><p>A simplified, machine-readable PDF with the same career evidence and consistent field structure, for platforms that require or prefer PDF files.</p><p><strong>Best for:</strong> online applications where PDF is required.</p><div class="cv-format-action">{ats_pdf}</div></article>
</div><p class="muted" style="margin-top:22px">The recruitment formats are designed to reduce parsing errors, not guarantee automatic field recognition. Always check imported dates, job titles, qualifications and language proficiency before submitting an application.</p>
<div class="actions"><a class="btn text" href="?page=impact" target="_self">Explore AI leadership →</a><a class="btn text" href="?page=contact" target="_self">Contact →</a></div></div></section></main>{footer()}'''
