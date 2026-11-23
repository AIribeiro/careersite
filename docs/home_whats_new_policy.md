# Homepage "What's New?" — publication rules

Every push to `main` checks for qualifying news. A code deployment is **not**
automatically a newsworthy publication. The banner exists to send a visitor
to something new and useful, not to announce internal maintenance.

## Eligibility and guardrails

1. Automatically eligible: newly launched public pages with a meaningful
   description and an actual route; newly added public credentials; newly
   published CMS articles, Executive AI Briefings and Weekly AI editions; and
   newly published Market Review editions.
2. Updates to existing pages or features require a reviewed entry in
   `data/portfolio_announcements.json`. The entry must explain *what is
   available*, *why a visitor would click* and the *exact public page*.
3. Routine code, CSS, image replacement, dependency, data refresh, background
   repair, publishing tests, CMS metadata edits and private account changes
   **never** produce banners by themselves.
4. No generic titles (e.g., "Latest portfolio improvements"), self-links
   (`?page=home`), draft content, admin pages, historical demos, unsupported
   claims or empty/placeholder descriptions.
5. A verified older announcement is preferable to a newer meaningless one.
   "What's New?" may keep the last genuinely useful release if there are no
   qualifying changes.

## To intentionally announce an update to an existing public page

Add a unique item to `data/portfolio_announcements.json`:

```json
{
  "id": "specific-release-id",
  "status": "published",
  "type": "Page update",
  "page": "presence",
  "title": "New speaking and publication records",
  "description": "Explore newly documented conference speaking contributions and published work on responsible AI and enterprise data leadership.",
  "cta": "See speaking & publications"
}
```

Allowed types: `New service`, `New resource`, `Page update` and
`Executive research`. The route must exist in `PUBLIC_VALID` and cannot
be Home, Admin, Analytics, Privacy, account access or a demo route. Titles,
descriptions and CTAs must be specific. The automation records the real
approval commit date when the entry first becomes `published`; editing an
already-published entry does not re-promote it.

## Verification

The `Home What's new regression` workflow guards publication selection,
route validity, direct CTAs, non-public exclusions, and publication-only CMS
and Market Review behavior. The `Publish portfolio release feed` workflow
checks every main-branch push and writes the feed only for eligible releases.

These checks protect editorial quality; they do not prove the live hosted
page rendered correctly. After major changes, verify the actual homepage
on desktop and mobile.
