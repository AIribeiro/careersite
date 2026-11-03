# Weekly AI — leadership positioning, discovery and distribution

Status: approved site direction, 3 November 2026. This file sets editorial and measurement rules; it does **not** authorize external publication or changes to scheduled automation.

## Non-negotiable information architecture

- **Thinking remains the master public page and the only top-navigation entry for this editorial area.**
- Weekly AI lives at `?page=thinking#weekly-ai`; its archive remains `?page=thinking&weekly_ai=archive`.
- Each edition keeps its existing permalink, CMS publication workflow, sourced reporting and audio.
- Do not create a new main navigation item, a parallel Weekly AI landing page, or a separate newsletter.
- Provide a clear route from Home to the in-page Weekly AI feature, then from an edition to Thinking articles and Executive AI Briefings.

## The audience promise

**Weekly AI — The AI week, through a leadership lens.**

Short description:
> A concise weekly perspective on the AI developments that matter to enterprise leaders: what changed, why it matters to the business, and what deserves a closer look. Personally curated, source-linked, and available to read or listen.

This is not a wire-service headline digest. The differentiator is leadership judgment: identify the decision, operating consequence, or assumption that executives should challenge. The headline should lead with a genuine leadership question only when the source and edition content support it. Do not imply every development requires immediate action.

## Editorial anatomy for future editions

1. **What changed?** The precise development, with date and trustworthy original sources.
2. **Why does it matter to enterprise leadership?** The possible business, operating-model, adoption, data, risk, or governance implication; distinguish confirmed facts from interpretation.
3. **What deserves attention next?** One credible question or decision boundary; avoid generic advice.
4. **Read or listen.** Keep concise, source-first, with audio only when a verified asset exists.
5. **Continue reading.** A relevant Thinking perspective or independent Executive Briefing, without repetitive contact CTAs.

Maintain the existing Weekly AI editorial standard and Friday edition cadence; no employer names or confidential examples in public briefings.

## Promotion experiment: four comparable release cycles

- **Friday publication:** Keep the approved Friday workflow. After publication and verification of the individual permalink, publish at most one distinct social introduction per authorized channel. Lead with the week's most consequential business question; do not use "new issue is out" as the sole hook.
- **Monday leadership follow-up:** Test a second, short interpretation of one specific edition only if it adds a genuinely different perspective. It should not repackage the same post or create duplicate promotional obligations. Subject to the established social approvals.
- **LinkedIn newsletter:** Cross-reference selected Weekly AI editions contextually, using the existing newsletter audience and editorial strategy. No extra newsletter cadence or quota.
- **X, Threads, Facebook, WhatsApp:** Condense the point for each channel, preserving original attributions and approved posting rules. Do not generate mass-identical posts.
- **Internal discovery:** Home promo, Thinking format jump links, continuing editorial links after each Weekly AI edition and compact writing footer.
- **Paid media:** Hold until channel and reader quality have a credible measured baseline.

Example **Friday** hook (illustrative only; replace with a verified edition-specific claim):
> AI agents keep gaining capability. The enterprise question is whether process ownership, controls and escalation are keeping pace. This week's Weekly AI looks at the implications for leaders.

Example **Monday** hook (only if grounded in the edition):
> The useful AI question for Monday's management meeting may not be "which model?" but "which workflow is ready to change, and who owns the outcome?"

## Attribution contract

- Use the existing `site_campaign_links.article_distribution_link()` for **individual published Weekly AI editions**.
- Keep `utm_campaign=weekly_ai`, a truthful `utm_source`, and the actual edition slug in `utm_content`. Prefer first-party tracked URLs; use the approved preview link for LinkedIn social-card rendering.
- Distinguish the Friday release and Monday follow-up in the editorial publication log and promotional copy, without inventing visits or replies.
- Do not share an unverified edition URL. The enduring collection entry point is `?page=thinking#weekly-ai`.

## Analytics and decision rules

Instrumented entry points:
- Home: `home-weekly-ai-promo` section exposure and `home_weekly_ai_open` click.
- Thinking: `thinking_format_weekly_ai`, `weekly-ai-feature` exposure, `weekly_ai_open`, `weekly_ai_listen_open`, `weekly_ai_archive_open`.
- Reader continuation: `weekly-ai-next` exposure; `weekly_ai_next_thinking` and `weekly_ai_next_briefings` clicks.
- Secondary discovery: `home_writing_weekly_ai` and `writing_footer_weekly_ai`.

Evaluate:
1. **Discoverability:** weekly-feature exposures and the rate of eligible Home-to-Weekly-AI opens.
2. **Acquisition:** source- and campaign-attributed sessions reaching individual Weekly AI editions.
3. **Quality:** meaningful reading/engagement based on existing verified telemetry, audio engagement, and non-bot return sessions where measurable.
4. **Depth:** cross-content continuation to Thinking and Executive Briefings.
5. **Return habit:** measured repeat weekly readership, clearly distinguishing sessions from distinct people.

Compare four post-change Fridays to four comparable preceding editions using an equal observation window per edition. Do not use unadjusted lifetime visits for older versus newer editions. Where exposure tracking, audio tracking or visitor deduplication is unavailable, report the metric as unavailable rather than filling in a proxy. Treat any 2x-visit or 50%-CTR target as a *test objective*, never a promise or forecast.

## Guardrails

- Keep the top navigation unchanged and preserve Thinking's parent role.
- Do not replace substantive insight with clickbait or oversell the business consequences of uncertain news.
- Do not create a second automated social publication without explicit authorized scheduling.
- Preserve existing approvals, source provenance, publishing times, analytics privacy boundaries and social channel conventions.
