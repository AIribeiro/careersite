# Content Studio — authoring Premium Thinking Articles

Effective for **new editorial Articles created on or after 12 November 2026**.
This is the CMS editorial workflow; the entitlement policy remains in
[`docs/article-early-access.md`](article-early-access.md).

## Publish one coherent article in two reader layers

The CMS continues to store one `content_html` field and the existing
`subtitle` and `excerpt` fields in `public.careersite_articles`.
No schema change or migration is required for this reader journey.

1. **Title and subtitle.** A clear executive question and its business stakes.
2. **Public executive summary.** In the explicitly named Content Studio field,
   write a standalone, factual summary (about 35–65 words). It appears as
   "The argument in brief" before sign-in. Metadata regeneration preserves
   an already written summary.
3. **Complete article body.** Start with at least two substantive paragraphs
   that give the real leadership problem and a defensible answer. After the
   introduction, add a meaningful H2/H3 heading; subsequent sections develop
   the full evidence, decisions, trade-offs and conclusion. This is a **single
   continuous manuscript** — do not insert login banners into the copy.
4. **Check both previews.** The Content Studio now has a **Public introduction
   · No sign-in** tab and a **Complete article · Premium Reader** tab. The
   former uses exactly the same renderer as the anonymous site; the latter
   renders the full draft regardless of the owner's current reader session.
   Neither preview saves or publishes changes.
5. **Publish.** First-time editorial Article publication requires a useful
   subtitle, at least 20 summary words, two pre-heading paragraphs with
   at least 65 words between them, and an analytical section boundary.
   Source validity and the soundness of the argument are still human editorial
   responsibilities. Draft saving remains unrestricted.

## What anonymous readers see

`src/article_reader_preview.py` displays the CMS title/deck, the authored
summary, a bounded sample of the genuine paragraphs **before the first H2/H3**,
then up to four true section headings and the site's complimentary
registered-reader invitation.

The new opening extractor **never crosses a section heading**. Older records
that begin with a heading retain their historical excerpt-based fallback.
There is no separate `preview_html` or per-article manual paywall flag.

## Release rules are unchanged

- The latest published editorial Article stays Premium regardless of age.
- Every Article stays Premium for at least seven days from original publication.
- An older Article is fully public only after the seven-day period **and** the
  publication of a newer Article.
- `Article`, `Point of view`, `Decision note`, `Field note`, `Framework`
  participate in the same succession sequence.
- Executive AI Briefings remain permanently registered-reader content; the
  latest Weekly AI is Premium, older Weekly AI editions are public.
- Historical published Articles and pre-existing drafts are not retroactively
  blocked by the new authoring checks.

The registered reader uses the existing Supabase Auth session and one library
account. Email newsletter consent is separate and optional.

## Security boundary and release check

This remains a **presentation-level** registered-reader experience, not a paid
paywall or secured asset delivery system. The public CMS REST API currently
exposes `content_html` through direct reads. Protecting the full edition from
direct API consumers requires a separate migration of private content storage,
authenticated reads and RLS, without breaking public catalogue metadata.

Automated coverage:

- `tests/test_premium_article_cms.py`: first-publication checks, extraction
  boundary, anonymous/full preview independence and bypass prevention
- `tests/test_article_early_access.py`: latest-issue + seven-day release rules
- `tests/test_briefing_public_preview.py`: unchanged briefing reader experience
- `tests/test_thinking_premium_reader.py`: shared reader surfaces

Before production release, run all relevant tests, inspect the Content Studio
on desktop/mobile, and test publication/registration with a draft article.
