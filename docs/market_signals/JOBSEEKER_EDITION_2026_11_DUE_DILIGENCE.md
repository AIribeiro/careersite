# Jobseeker Edition 1.0 — editorial and evidence due diligence

**Reviewed:** 18 November 2026  
**Parent evidence release:** Swedish AI & Data Market Review, Executive Edition 2.0.2, issued 17 November 2026  
**Scope:** The candidate-facing service page, five analytical perspectives, complete 30-day planning material, PDF cover, supporting research and the PDF's traceable source register.

## Editorial finding

The report is a **candidate decision guide built from a bounded 2026 market-research snapshot**. It is not a comprehensive AI/Data labour-market census, live job search, salary study or evidence of a particular candidate's probability of getting hired. The value proposition is to help readers examine where to search, how to interpret adjacent responsibilities, how to present proven capabilities and when to revisit a search strategy.

## Claim and evidence checks

| Source / claim | Verification and denominator | Residual limit |
| --- | --- | --- |
| SCB enterprise AI use: 49%; large enterprises: 85% | Published IT usage in enterprises 2026; firms with 10+ staff versus 250+ staff. Original: https://www.scb.se/en/finding-statistics/statistics-by-subject-area/research-and-the-digital-society/the-digital-society/ict-usage-in-enterprises/pong/statistical-news/ict-usage-in-enterprises-2026/ | AI use is neither business value nor hiring demand. Survey industry scope / SNI changed in 2026; don't treat a cross-year difference as directly comparable. |
| 33% internal analytics staff; non-adopter barriers 62%/43%/34% | SCB 2026 survey and signed-off observation population fields. Barriers apply only to companies which considered AI but did not adopt it, and can overlap. | No data establishes AI-vacancy demand, employer maturity or an internal workforce shortage from these figures. |
| SCB national vacancies: 159,500; advertised 127,500; other methods 32,100 | Published Q2 2026 whole-economy survey: https://www.scb.se/en/finding-statistics/statistics-by-subject-area/labour-market/labour-force-demand/job-openings-and-recruitment-needs/pong/statistical-news/job-openings-and-recruitment-needs-2nd-quarter-2026/ | Values are estimates, components are rounded, and non-advertised recruitment methods cannot be called hidden AI positions, successful hires or a tested networking strategy. |
| JobTech 20 selected September and 29 selected October senior advertisements; 13 Stockholm, 5 Västra Götaland in October | Matched against the signed-off publication rows and source classification. Selection: documented 30-seed, headline-based retrospective title classifier. See `JOBTECH_V1_REPRODUCTION.md`. | **Low national coverage:** advertisements, not guaranteed unique vacancies or hires; retrospective API revisions and absence of immutable record-level snapshots limit independent replication. Do not report a reliable +45% job-market rise or extrapolate trend from 20 to 29. |
| KI 110.7 confidence; employment balances 2 (past) and 7 (forward) | KI October 2026 business tendency tables: https://www.konj.se/publikationer/konjunkturbarometern/2026-10-29-stort-fall-i-hushallens-stamningslage/ | 110.7 is an index against a normal value of 100; 2 and 7 are staffing net balances, not vacancies or numbers of hires. Expectations are not completed appointments. |
| SCB Q2 VGR 3.2 versus national 2.9 vacancies per 100 employed positions | Official national whole-economy survey and signed-off regional observations. | The difference is not a statistically established advantage without uncertainty intervals, and it cannot measure regional specialist AI hiring. |
| Brainville Sweden Oct +10.7% listed assignments; +18.5% available consultants YoY | Brainville November 4 report as catalogued in the evidence table and corroborated by the company repost of the Sweden October analysis: https://www.linkedin.com/company/brainville/ | Marketplace participation may vary; all consulting disciplines, not national representation, specialist AI availability, consultant rates or probability of contract. |
| Six evidence series / five publishers / 43 observations | Existing signed-off release manifest; the jobseeker PDF uses the same stored published rows and exact evidence register as Executive Edition 2.0.2. | Distinct series provide context, not six independent replications of one labour-market phenomenon. Some observations in the shared full source register are background rather than candidate-specific evidence. |

## Specific corrections

1. Reframed the publication's name as **Swedish AI & Data Market Review — Jobseeker Edition**, avoiding a title that implied a complete census of AI vacancies.
2. Clarified the benefit in the PDF and reader landing: test relevant discovery channels, adjacent titles, professional evidence and location or contract choices, with a 30-day planning framework.
3. Explicitly identified the issue date as **18 November 2026**, separate from the **17 November 2026 evidence snapshot**.
4. Rewrote all five evidence interpretations to distinguish measured observations from editorial hypotheses. The most material correction is avoiding an inference that the 32,100 other-method vacancies represent hidden AI opportunities or prove networking works better than applications.
5. Clarified JobTech selection, retrospective revisions and advertisement-versus-vacancy scope. The 20-to-29 difference is **not** asserted to be sustained market hiring growth.
6. Identified SCB's separate AI adopter and non-adopter cohorts, allowing for overlapping barriers.
7. Clarified the KI confidence index and staffing net balances; avoided treating 3.2-versus-2.9 regional estimates as a proven advantage.
8. Clarified Brainville as one platform with consultant availability growing faster than listed assignments, without converting either series into AI-specific competition.
9. Added a **fail-closed numeric contract** for 20 specific figures quoted in the candidate narrative. If an underlying published value changes, the report now stops rather than silently producing a contradiction between prose and its evidence register.
10. Clarified jobseeker scope at the public service choice, PDF description and reader page. Improved preference handling for a candidate-directed deep link in a returning member session.
11. Added regression tests for numeric drift, candidate publication date, source limits, URL-to-edition handling and the rendered PDF.

## Risks not repaired by rewriting

- A comprehensive national AI/Data job demand series, offer conversion metrics, senior-vs-junior opportunity segmentation, salary series and role-specific location/language distributions **are not in this edition**. Do not promise these features.
- JobTech historical observations cannot be replicated exactly at point-in-time without the original immutable advertisement records. A later data collection would require a new documented and approved release, not silent insertion into 2.0.2.
- Brainville is one platform. The 2026 enterprise IT survey includes a classification change. SCB survey estimates retain uncertainty. The shared full source register is not proof that all 43 entries have been independently re-collected from original releases on audit day.
- The 30-day plan is a professional decision aid, not an evaluated job-search intervention. No method here establishes causal effects on replies, interviews, offers or time-to-hire.
- The registered-reader route should still receive a production-browser check with an authenticated account; CI source and PDF tests do not replace end-to-end member UX testing.

## Evidence hierarchy and release discipline

**Facts:** signed-off publication rows, dated measures, verified primary releases, and linked source records.  
**Interpretation:** conditional, qualified editorial reasoning about a job search.  
**Actions:** candidate experiments and due-diligence questions, not observed causal results.

Retain the original Executive Edition and historical sample unchanged. Correct the candidate reader and its dynamically generated PDF from the same approved evidence. Any *new* national job-demand indicators require sourcing, methodological review, a versioned edition and separate tests.
