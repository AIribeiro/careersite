# Executive AI Briefings — retrospective employer anonymity audit

**Audit date:** 2 November 2026  
**Scope:** All Content Studio records with `kind='Executive Briefing'` and `status='published'`, plus reader-specific Python/HTML, library artwork and the bundled governance SVG.  
**Published records found:** 5  
**Result:** Five published CMS records passed the named-former-employer scan after remediation. Reader source files and the governance illustration also passed the same name review. The deployed Streamlit pages could not be opened through the available web checks, so visual/live rendering is **not independently verified**.

## Edition-by-edition disposition

| Edition | Example and experience basis | Remediation or finding | Status |
| --- | --- | --- | --- |
| Data Governance: What Deserves Funding? | Service operations, warranty-related data quality, master-data responsibilities and investment choices | Previously revised to replace named employers with a field-informed, anonymous composite disclaimer. Verified all CMS fields clean in this audit. | CMS published; source reviewed |
| EU AI Act: What Executives Must Decide Now | External AI assistant used by an internal enterprise service team; deployer/provider responsibility | Replaced generic recruitment-screening company example with a field-informed internal-service scenario, explicitly not an identifiable organisation. | CMS published; source reviewed |
| AI Governance Explained to Executives | AI-assisted technical service-case routing and permission boundaries | Reworked the independent reader's recommend/prepare/execute example. Replaced financial credit actions with service-case routing controls. Added a field-informed anonymized-composite disclosure; no invented results. | CMS published; reader committed |
| Seven Questions for Better AI Decisions | Enterprise service-case triage, process diagnosis and AI investment review | Added explicit field-informed anonymized-composite status to the reader example; replaced “field-tested” claim with “field-informed”. | CMS published; reader committed |
| AI, ML, GenAI, RAG and Agents: What Executives Actually Need to Know | Service and warranty workflow, retrieval-supported knowledge, bounded AI authority | Rewrote the body scenario and aside disclosure as field-informed anonymous composites. Former-employer technical reference had already been replaced by a public neutral standard source. | CMS published; source reviewed |

## Controls

1. `docs/executive_briefings_editorial_standard.md` requires field-grounded and anonymous examples, no named current or former employers anywhere, no identifiable context or unsupported financial/operational achievements, and both CMS and hard-coded reader review.
2. `src/briefing_content_policy.py` validates recognized employer names (including historical variants, URL/HTML encoding, body, links and public metadata) when saving and publishing via `src/site_cms.py`. Regression tests live in `tests/test_briefing_content_policy.py`.
3. Supabase migration `enforce_executive_briefing_employer_anonymity` installed `public.careersite_block_briefing_employer_names()` and `careersite_articles_briefing_employer_guard_trg` on the CMS table. It screens the entire record when `kind='Executive Briefing'`, including direct writes that bypass the CMS editor.
4. Database negative tests attempted an article-body update naming a former employer and a metadata update naming a former employer. Both were rejected with SQLSTATE `23514` and did not change the records. A benign no-op update completed.
5. Final database query returned **5 published items, 0 recognized employer-name matches**. The GitHub reader, catalog and SVG sources also had zero matches.

## Limits and remaining verification

- String checks cannot prove that an unnamed example does not indirectly reveal an employer, nor can they establish the real-world history of a scenario. Editorial review remains mandatory. The permitted field basis is established by the author's enterprise work across service, warranty, data stewardship, AI adoption and governance; examples are **illustrative composites**, not case reports.
- Neutral research authorities and third-party technical source names can be cited outside examples when relevant. They are not substitutes for factual accuracy and may not be former-employer sources.
- GitHub source updates are committed but successful CI execution, live deployment, individual-page rendering, mobile appearance and real user navigation have **not** been verified in this audit. Do not represent the code changes as visually confirmed on the public app.
