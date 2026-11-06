# Executive AI Briefings — premium infographic release contract v1.1

**Effective:** 6 November 2026. **Reference:** the explicitly user-approved infographic “The AI Is Live. Who Holds the Authority?” bundled as `assets/approved-premium-operating-authority.png` in private @Executive Infographic Studio 1.1.0. This image is a visual **quality floor**, not a mandatory grid or source of facts for future topics.

## Why the standard exists

Earlier briefings used article-specific Python renderers and separate SVG/WebP image routes that returned HTTP 200 while displaying a broken image on the user's iPad Safari. The user later confirmed that source-controlled WebP bytes embedded directly in the final Streamlit HTML rendered successfully. Do not assume a green HTTP test proves a working browser image.

## Source → visual → delivery (required for every new briefing)

1. Prepare the briefing using `docs/executive_briefings_editorial_standard.md`. Lock every decision, label, number, limitation, relevant source and no-employer-anonymity requirement. No copied source diagram or invented business result.
2. Save a CMS draft and calculate the actual article fingerprint using `briefing_infographic_engine.source_fingerprint`, the SHA-256 of title, subtitle and HTML body joined by vertical bars.
3. Produce a source-matched original infographic meeting the **premium design contract**: dramatic restrained navy header with cyan editorial accents; semantic uniform line icons; teal/copper/steel palette assigned meaningfully; subtle gradient bands, warm white surfaces, fine dividers and shadows, perfect spacing, readable labels, executive action bar, authentic circular author portrait and restrained footer. Other topics require their own diagram, never a compulsory 4×5 card grid. The generated image is not accepted until its text has been audited against source.
4. Review **exact source files**: desktop PNG/source, truly readable mobile composition and print-quality A4 PDF. Do not silently substitute a coded approximation after an owner approves a generated image.
5. Use `scripts/build_briefing_artwork_bundle.py` with `--slug --article-fingerprint --revision --desktop --mobile --pdf --heading --deck` to package files. Commit the resulting immutable folder under `static/briefing-artwork/<slug>/` containing `manifest.json`, `desktop.webp`, `mobile.webp`, and `infographic.pdf`.
6. Source approval requires a current Supabase `careersite_briefing_infographics` record, `approved` status, matching article fingerprint, alt/caption, and six reviewed criteria. An old approved row or only committed files cannot authorize publishing.
7. The shared renderer `src/briefing_approved_asset_renderer.py` reads the manifest for **any slug**, validates file SHA256, image dimensions, WebP signatures, PDF signature, source fingerprint and safe file paths; it emits one infographic after the executive judgment. Both desktop and mobile images are bounded, cached, embedded as `data:image/webp;base64` within the HTML. One responsive composition is shown at a time. No remote `<img>` request. The prominent **Download infographic · A4 PDF** CTA precedes the tall graphic, served by common route `/briefing-artwork/<slug>/download.pdf`.
8. Before publishing: confirm decoded WebP bytes **inside the final HTML**, one `briefing-infographic` analytics section, CTA, A4 download, author credit, mobile layout and source matching. Test with `PYTHONPATH=src python -m unittest -v tests.test_briefing_approved_asset_renderer`. The tests use a totally new slug to prove no special-case Python branch is needed.
9. Publish and separately verify the Supabase record, GitHub commit, focused CI, deployment, and real browser/device image. A green unit test is **not** physical iPad QA. A failure means hold/repair; never claim live verification without evidence.

## Source-controlled bundle schema

`manifest.json` contains `schema_version:1`, `slug`, `revision`, `article_fingerprint`, `heading`, `deck`, desktop `{file,sha256,width,height}`, mobile `{file,sha256,width,height}`, and PDF `{file,sha256,pages}`. Checksums are actual file hashes. The packager checks A4 geometry, decodability and a strict 1.5 MiB inline-image size budget. The bundle is versioned rather than overwritten; revisions require reapproval. No new per-article code branch is required.

## Reader and rollback behavior

`src/briefing_infographic_store.py` first validates the CMS-approved visual and article fingerprint, then tries the common manifest renderer. A **missing** manifest keeps existing legacy readers working, but a **present, invalid** manifest fails closed without a giant empty image or an older mismatched visual. The shared PDF route verifies published article status and matching fingerprint before serving bytes. Existing published legacy articles are not migrated automatically; migrate only after exact approved artwork and real-device QA. Rollback only to an approved asset set whose article fingerprint still matches; otherwise hold the visual while repairing.

## Mandatory visual QA

Inspect the actual output at full scale, iPad and phone. Check every label, icon stroke, header hierarchy, card spacing, body contrast, portrait identity, footer, count, image crop, PDF page and matching CTA. A 2×2 layout is one possible design, not the standard answer to every article. Always distinguish generated/approved/committed/published/deployed/device-verified states.