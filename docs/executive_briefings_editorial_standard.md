# Executive AI Briefings — editorial and visual quality standard

**Effective:** 2 November 2026  
**Status:** Authoritative quality reference for all *new or substantially revised* Executive AI Briefings.  
**Reference edition:** [EU AI Act: What Executives Must Decide Now](https://jairribeiro-ai.streamlit.app/?page=briefing&article=eu-ai-act-what-executives-must-decide). Use its standard of evidence, clarity, decision usefulness and visual craft; **do not clone its sections or artwork** for unrelated subjects.

This standard complements [editorial channel selection](editorial_channel_selection.md). It does **not** introduce a publishing quota, amend the WEEKLY AI schedule, authorise automatic publication, or assert that older briefings already pass every new check.

## The editorial promise

**Content is the product. Design is how leaders reach the judgment quickly.**

A briefing is a short, independently useful advisory product for a senior leader facing a **specific** AI decision. It must make a technical, operational, regulatory or governance question understandable without watering down the facts. It carries Jair Ribeiro's business-first perspective on ownership, operating impact, adoption, evidence, human judgment and measurable outcomes. It does not mimic a vendor explainer, news summary, compliance poster or generic consultant deck.

A senior reader should be able to answer five questions after reading:
1. **What am I deciding?** The actual business choice, tension or approval.
2. **What do we know?** The reliable facts and their limits, including dates or legal status when material.
3. **What could change the answer?** Relevant risk, exception, trade-off, failure mode or alternative.
4. **What should I ask to see?** Evidence, responsible people, control, test or proof required.
5. **What happens next?** Proceed / hold / stop, next inquiry or other bounded action.

## Field-informed examples without employer identification — mandatory

Executive AI Briefings must **never name, link to or otherwise identify any of Jair Ribeiro's current or former employers**. This rule applies to the title, excerpt, article body, scenario, disclaimer, sources and links, diagrams, captions, image alt text, metadata and social excerpts—not only to a visible case-study heading. Do not use an employer's name even in a negative disclaimer such as “this is not a case from [company].” Do not identify a previous employer as a reference provider; prefer suitable independent standards, public authorities, neutral sources or another verifiable primary source.

All operational examples must be **field-informed**: derived from the kinds of enterprise AI, data, analytics, governance, service, commercial and process situations that Jair has actually encountered in his career. Translate experience into **unbranded, anonymized examples** that illuminate the decision, without making the reader able to infer the organization. Do not mention business names, client names, supplier brands, recognizable products, unique projects, locations, named individuals, proprietary operating details or identifying metrics in the example.

Write an example as an **illustrative composite** when it synthesizes several real patterns, and state that it is not an account of one specific engagement or verified outcome. If the user has supplied a demonstrably verifiable, publishable first-person event and authorizes its use, state only what is substantiated and anonymizable; never invent first-person accomplishments, figures, decisions or outcomes to make a case vivid. If there is no field-grounded example, omit it rather than manufacture a case.

Separate **examples** from **external evidence**: an authority or research publisher may be named and linked when attribution is necessary and it is not an employer of Jair's; such source attribution must not disguise an employer-specific story or vendor promotion. Do not strip proper names from official legal instruments or original primary evidence when essential to accuracy. No brands or company names inside case narratives.

**Pre-release and retrospective check:** inspect **both** the published CMS record and the actual reader implementation: title, category, snippets, body, aside, SEO/social metadata, links, hard-coded Python/HTML cases, card artwork, bundled SVG text and accessible captions. Screen known employer names, abbreviations, historical brands, encoded links and context that could re-identify an unnamed employer or client. Check each scenario's field-experience basis and truthful composite label; no measured results or first-person claims without defensible evidence. The Content Studio save/publish validator and the Supabase row trigger reject known employer strings, including direct database edits. These mechanical checks **do not** validate anonymity by context or whether a case truly happened; editorial review is still required. Any breach is a publication blocker. Re-audit every previously published briefing when changing its content or reader code.

## Standard executive decision heading — all editions (7 November 2026)

The opening recommendation/decision section must use **“The Leadership Decision”** as its visible section label in every Executive AI Briefing, including previously published editions. It replaces the less familiar **“The executive judgment”** (and the older “The executive premise” in the seven-question reader). Maintain the concise issue-specific decision sentence, supporting rationale, **Next move**, and the outcome/trade-off/evidence questions when relevant. This is a section heading, not a demand to make every article prescriptive or remove uncertainty.

The shared CMS reader in `src/site_cms.py` applies a presentation-only normalization for legacy headings within published CMS articles. New authored reader templates also use the updated heading. **Do not alter historical published CMS content, titles, subtitles or source-locked diagrams solely to rename this heading**: doing so would invalidate their approved infographic fingerprints and could interrupt the iPad/Safari image and PDF delivery. Preserve other meaningful labels, such as “Executive decision map” and “Next move”, when they serve different purposes. Regression tests must cover main and special reader variants, legacy CMS body markup and unchanged source hashes.

## Content architecture: one issue, two speeds

Design a **one-minute executive scan** with a direct title, sharp deck, explicit judgment, and a meaningful visual decision aid. The full briefing may reasonably take **4–7 minutes or longer when the evidence warrants it**. Concision means *no wasted text*, not thin content or arbitrary word counts. A senior leader must not have to expand a hidden section to discover the central answer. Place deeper legal, technical or methodological detail after the decision path.

Recommended sequence — adapt it rather than applying mechanically:
- **Question and judgment:** what executives need to decide now; one clear recommendation or conditional position.
- **Ground truth:** what is established, what is misunderstood, and what remains uncertain. For law or policy: exact instrument, version, amendments, effective/applicability dates, and who is affected.
- **Decision model:** a topic-specific 3–6-step original framework, classification map, exception tree, trade-off comparison or workflow. It must represent the actual reasoning, not a decorative infographic.
- **Business application:** one credible example or scenario, plainly labelled illustrative if not verifiable personal experience; explain how obligations or recommendations change with context.
- **Action record:** questions and evidence an executive can use in a real meeting, including accountable owner, decision rights, next gate and review trigger.
- **References and contact:** primary evidence sources accessible from the edition, appropriate caveat, and a clear but restrained invitation to discuss a context-specific decision.

Avoid repetitive introductions, seven generic questions padded into a list, “AI will change everything” framing, inflated case-study outcomes, theatrical first-person claims, lengthy research dumps, and jargon that cannot be turned into a test or decision.

## Contextual navigation — mandatory at the end of every briefing

A briefing is an independent executive decision guide **and a deliberate entry point to the wider portfolio**. After the main article and sharing material, place the contextual **“Where to go next”** section. The final reader section must always remain the shared contact footer headed **“Have an AI choice that needs a clearer answer?”**, directly before the site footer. Never place related-reading recommendations beneath that contact footer. **Do not add intermediate contact panels** with competing titles such as “Who owns the next decision?”, “Have a governance proposal to challenge?”, or another “Discuss your decision” button. Keep questions about decision ownership inside the substantive guidance, not in a second solicitation. Each reader should have **one contact CTA block**, the standard final footer, while independent share controls and contextual reading remain above it.

- Recommend up to **two distinct published Executive AI Briefings** that extend the decision the reader has just considered. Never recommend the current edition, unpublished drafts or generic popularity lists.
- Make the link **editorial, not algorithmic decoration**: each card must state *why that particular briefing is the next useful decision*. The six current editions have curated reading paths; future editions fall back to topic overlap until their path is curated.
- Derive destination titles, reading time, publication status and canonical URLs from the published CMS record rather than duplicating content in a hard-coded card. Stop recommending an edition as soon as it is unpublished.
- Keep the navigation calm and premium: two equal-priority cards, a short transition, a library link and a one-column mobile layout. Preserve keyboard focus, useful link labels and readable contrast.
- Use the existing first-party analytics: `briefings-related-reading` section exposure, `briefing_related_open` card clicks, destination article identity and page attribution. Do not add marketing UTMs to internal reading links, and do not treat link clicks as verified destination reading.
- The recommendation section is injected **once centrally and immediately before the shared contact footer** through the CMS renderer so that all independent briefing readers inherit it. Every reader variant must include the standard contact footer; if there are no other published editions, do not show empty recommendation cards.

Before releasing a reader or changing its routing, verify the related links open published editions, the current edition is excluded, the section follows the actual article and contact content, and desktop/mobile navigation remains usable.

## Evidence, accuracy and originality are release blockers

- Verify material factual claims against **current primary sources** wherever available: official regulations, government and regulator documents, published standards, company filings and original research. Use corroborating reputable secondary reporting only where helpful. Quote sparingly, paraphrase independently.
- For time-sensitive subjects state the **as-of date** and distinguish enacted/in-force, applicable, transitional, proposed, announced and forecast. Never infer legal effect from an infographic, social post or single commentary article.
- Differentiate **legal obligations**, **external findings**, **the author's management judgment**, and **illustrative scenarios**. Where evidence is insufficient, say so, narrow the claim, or leave it out.
- Check classifications, exceptions and scope before presenting simplified diagrams. A mnemonic is not the law. Provider/vendor statements are not independent evidence of customer compliance.
- Never copy somebody else's original visual structure, phrasing, diagrams or intellectual framing. Create a new explanatory model that provides genuine analytical value; credit data and primary authorities.
- Do not claim a source was checked, a live page was rendered, a business outcome occurred, or an edit is published unless independently verified in this workflow.
- Give links to the specific authoritative documents/articles; avoid citation theatre or uncited sensitive claims. Include an expert/legal-advice boundary where the topic demands it.

## Premium visual and Safari-safe publishing — updated 6 November 2026

**The primary visual-quality reference is now the exact owner-approved "The AI Is Live. Who Holds the Authority?" infographic**, included in private @Executive Infographic Studio v1.1.0 as its premium reference asset. The standard concerns icon craft, navy editorial hierarchy, restrained teal/copper/steel gradients, legible cards, original analytical logic, branded author footer and decision-oriented conclusion; it does **not** prescribe the same 2×2 framework for every topic. The older security and EU AI Act examples remain reference editions but no longer set the upper visual-quality benchmark.

The reusable **source-locked asset release** is documented in [Executive Briefings Premium Visual Release](executive_briefings_premium_visual_release.md). Every new Executive AI Briefing created from 6 November 2026 requires a **complete approved desktop/mobile WebP + A4 PDF bundle and manifest**, not just an approved editorial SVG specification. Use the shared renderer in src/briefing_approved_asset_renderer.py, source and file SHA-256 checks, HTML-embedded bounded WebP bytes for Safari/Streamlit, exactly one infographic directly after the Leadership Decision section, and a prominent PDF CTA above the image. Individual new editions must not add copied special-case rendering code.

These requirements are not retrospective publication blockers for already-published legacy editions; migrate those only after the exact owner-approved source artwork is verified and without disturbing working pages. The server-side CMS publishing guard, Content Studio gate and focused CI enforce new-bundle readiness; **live-device verification remains separate** from source/content CI. Avoid declaring publication success based solely on HTTP 200, accepted CMS metadata, or image bytes rendered by a test server.

## Mandatory infographic — generated, reviewed, versioned, inserted

Every published Executive AI Briefing must have **one primary, original, strategic, premium infographic** that makes its executive decision logic easier to understand. It is part of the content, not optional decoration. Each must explain a real tension, sequence, decision gate, control boundary, evidence requirement, ownership split or relevant timeline. **The subject chooses the visual grammar:** comparison, flow, layers, decision map, timeline or questioning framework; no fixed six-row template, copied source diagrams, arbitrary icons, invented outcomes or generic decorative art.

The **Executive Briefing Infographic Engine** is the standard authoring route:
1. Save the article draft; generate an editable structured visual proposal from its own headings and decision text.
2. An editor rewrites/curates its title, labels, proof points and conclusion; generation itself is not fact-checking or approval.
3. Render approved desktop/mobile artwork and matching A4 PDF through the premium asset-bundle contract for new editions. Source-lock all labels and use verified self-contained WebP bytes inside the published reader; no external image request or unapproved substitution.
4. Review all six criteria: factual accuracy; original structure; employer/client anonymity; scan/readability; actual mobile-preview readability; and direct relevance to the executive decision. Require an informative alt text and caption.
5. Approve a specific revision tied cryptographically to the article title, deck and body. A changed article invalidates the approval; public readers must fail closed rather than showing an outdated infographic.
6. Insert exactly one image immediately after the Leadership Decision section, before full reasoning. Put its A4 PDF CTA above the poster. Preserve the prior approved image while a replacement is only a draft, and switch only when the current source-matched asset revision passes both CMS and bundle gates.
7. A new briefing cannot publish without an approved current infographic. Existing editions remain public while revisions are prepared; their six initial specifications were backfilled with source-level editorial review on 2 November 2026. **This does not constitute independently verified live-browser or real-device appearance.**

**No false review claims.** A stored editorial check is not a claim that Streamlit deployment, browser behavior, responsive device rendering or CI succeeded; report those separately. If the preview reveals clipping, meaningless labels, misleading comparisons, conflicting legal claims or a diagram that adds no understanding, reject and revise before approval. The original visual concept must remain sufficiently distinct from any supplied reference.

**Infographic measurement:** the first-party `briefing-infographic` section reports exposure and observed attention in the owner-only analytics view. This is attention instrumentation, not evidence that the reader comprehended the infographic. Do not infer causal conversion improvements from simple before/after counts.

## Visual language: premium, restrained and readable

The approved portfolio identity remains **deep navy, muted copper, warm cream/white**, with editorial typography, measured contrast and generous spacing. Visual quality is assessed against the EU AI Act edition, not against stock graphics or a copied infographic.

- **Topic-specific visual identity**: an original diagram or decision map that makes the logic easier to understand. Every icon, shape and step must explain something; no image filler or brand-person portrait in an issue about a regulatory/business topic.
- **Above-the-fold clarity**: readable title and deck, clearly signalled executive judgment, visual hierarchy that works at desktop and iPhone widths. Prefer a clean 16:9 editorial composition for illustrated covers and preview art when used; preserve safe crops and legible labels.
- **Meaningful information design**: use decision gates, date timelines, obligation cards, exception notes or ownership maps suited to the subject. Do not recycle the same graphic pattern merely because it was successful before.
- **Reliable rendering**: use supported, sanitiser-safe first-party HTML/CSS or verified bundled artwork; never depend on untested remote image assets. Include descriptive alt text or equivalent accessible semantics. Ensure narrow-screen stacking without clipped words, overflowing cards, unreadable type or invisible charts.
- **Low-friction reading**: concise sections, short line lengths, restrained callouts, precise labels and comfortable spacing. Avoid overpacked dashboards, childish icons, glossy effects and false “compliance achieved” status badges.
- **One independent page** per publication with a unique card, stable URL, factual metadata, source links, responsive reader and working context-aware contact CTA.

## Editorial pre-publication gate

Treat these as **mandatory human review criteria**, not as a score to game:

1. **Decision relevance:** Can a busy executive state the actual choice and useful recommendation after one minute?
2. **Substance:** Does the body contain a clear explanation, a concrete trade-off or exception, evidence to ask for, and a practical next move—not just slogans?
3. **Evidence:** Were changing claims/date-sensitive facts checked against authoritative sources and cited? Are status and limitations precise?
4. **Originality:** Is the interpretation, structure and any visual an independent contribution? Are examples honestly labelled?
5. **Visual craft:** Does the original subject-specific visual improve understanding, render correctly and preserve mobile readability/accessibility?
6. **Publication integrity:** Does the *individual* briefing render from the published CMS item, appear separately in the collection, preserve working links/attribution/metadata and expose contact without dominating the page?

**Release rule:** A failure on any criterion means **hold / revise**, not “publish and fix later.” Never silently weaken the standard to meet a cadence. The Content Studio acknowledgement reminds editors to carry out these checks; it is **manual attestation**, not automated legal or visual validation.

**Verification report:** Separate *saved draft*, *database-published*, *GitHub-committed*, *deployed*, and *visually verified live*. Only claim the levels actually observed. If live rendering cannot be reached, state that explicitly.

## Editorial and distribution boundaries

- Choose a briefing **only when the problem genuinely benefits from an executive decision guide**. There is no fixed quota or obligation to create one for each news event.
- Promote **specific verified published briefing pages** only where relevant. Prefer collection link for series introductions. Never let promotion dictate subject or editorial content.
- Respect the distinct roles and existing schedules of Thinking essays, WEEKLY AI, LinkedIn posts and the newsletter, as established in [channel selection](editorial_channel_selection.md).
- Stronger wording, attractive artwork or additional sections do not compensate for missing truth, originality or operational usefulness.

**North star:** An executive can take the briefing into a real meeting, ask a better question, demand the right evidence and make a defensible next decision.
