# JobTech senior AI & Data advertisement basket — v1 method and verification limits

**Edition:** Swedish AI & Data Market Review, November 2026 (Executive Edition 2.0.2; prior publication vintages retained)  
**Classification source:** Supabase Edge function `jobtech-target-probe`, version 1, SHA-256 `2a07910b4d2f662f2322979bbc3ae4b5924cea4ddd3dfe2f5dce9aba5d153365`  
**Frozen publication observations:** June–October complete calendar months; November 1–15 separately labelled incomplete. The 16 November 2026 extraction is the publication vintage.  
**Scope:** Author-defined *advertisement sample* for selected strategic/senior AI and Data/Analytics titles in Sweden, not all vacancies, unique open positions, people hired, candidate supply, salary, or market size. The published 29 for October 2026 is a frozen research observation, not an official Arbetsförmedlingen AI management statistic.

## Retrieval contract

1. Query **both** `https://historical.api.jobtechdev.se/search` and `https://jobsearch.api.jobtechdev.se/search`.
2. For each of the 30 exact text seeds below, submit a `GET /search` request with `q=<seed>`, `published-after=<YYYY-MM-DD>`, `published-before=<exclusive-end-date>`, `sort=pubdate-asc`, `limit=100`, `offset=0,100,...`, `resdet=full` and header `x-feature-freetext-bool-method: and`. The historical endpoint also receives `request-timeout=90`.
3. Retrieve all pages up to the API's result ceiling. Where a query yields over 1,900 hits, recursively split the calendar window at its midpoint, up to four levels. If any source query fails, **do not report the result as a complete extraction**.
4. Apply the **headline-only** classifier below to each returned advertisement. The search seed does not itself guarantee inclusion.
5. Combine both endpoints and all seeds; deduplicate first by `original_id`, falling back to lowercased `headline|employer.name|publication_date`.
6. Group kept advertisements by their publication month and by `workplace_address.region`; count one classified advertisement per deduplicated ID. A regional subset is not a complete count of all local AI roles.
7. Store the full query window, extraction time, failures, source revisions and classifier hash with the resulting totals. Previously published, signed-off point codes are frozen; a fresh query is a **new vintage**, not a silent correction.

**30 exact search seeds (case preserved):**

01. `AI Lead`
02. `AI Head`
03. `AI Director`
04. `AI Manager`
05. `AI Strategy`
06. `AI Transformation`
07. `AI Governance`
08. `AI Adoption`
09. `AI Enablement`
10. `AI Capability`
11. `AI Portfolio`
12. `Responsible AI`
13. `AI Automation`
14. `AI Innovation`
15. `AI Productivity`
16. `AI Upskilling`
17. `GenAI Lead`
18. `Data AI Lead`
19. `Data AI Head`
20. `Data AI Director`
21. `Data AI Manager`
22. `Head Data`
23. `Director Data`
24. `Head Analytics`
25. `Director Analytics`
26. `Manager Data Analytics`
27. `Data Governance`
28. `AI strateg`
29. `AI ansvarig`
30. `Verksamhetsutvecklare AI`

## Explicit title-selection bias

The 30 search seeds and the headline classifier were designed to identify a **narrow group of senior job titles**. They are not a stratified or representative sample. A leader responsible for enterprise AI may be advertised as Head of Operations, Chief Digital Officer, Product Director, Commercial Transformation Lead, Business Improvement Head, HR leader, general manager or another title outside the rules. The exclusion rules also remove many engineering, product, project and architecture roles, even when those positions influence or own AI outcomes. These omitted opportunities are **not zero demand**; their number is unknown. Title changes alone can change observed month-to-month counts.

**Recruitment-channel coverage:** advertisements in the queried JobTech sources do not represent unadvertised searches, executive search, internal appointments or all third-party job boards. The recorded publication month is the advertisement's date, while the research extraction and verification dates can be months later.

**Numerical interpretation:** with small totals, an increase from 20 in September to 29 in October is a difference inside this selection only. Do not turn it into a percentage change for Sweden's national AI leadership market, an estimate of completed recruitment or evidence of specialist shortage.

## Frozen classifier code

The following code is extracted verbatim from the deployed v1 classification and fingerprint functions. It is included for auditability; there is no internal service authentication token here.

```typescript
const excludeRe = /\b(engineer|engineering|developer|utvecklare|scientist|researcher|research|forsk\w*|architect|arkitekt|programmer|software|mlops|machine learning|data engineer|data scientist|product owner|product manager|product lead|project manager|program manager|scrum|analyst|tekniker|technician|sales|business development|presales|pre-sales|marketing|growth|content|retail|workstream|controller|service manager|tech lead|technical lead|team lead)\b/i;

function classify(headline:string){
  const h=(headline||"").replace(/\s+/g," ").trim();
  if(!h || excludeRe.test(h)) return null;
  const ai=/\b(ai|artificial intelligence|genai|generative ai)\b/i.test(h) || /\bai[-\s]?strateg\b/i.test(h);
  const strategicAI=/\b(strategy|strateg|transformation|governance|adoption|enablement|capability|portfolio|value|productivity|responsible|automation|innovation|upskilling|center of excellence|centre of excellence|coe|verksamhetsutvecklare|ansvarig)\b/i.test(h);
  const seniorAI=/\b(head|director|lead|leader|chef)\b/i.test(h);
  const exactAIManager=/\b(ai|genai|generative ai)\s+manager\b/i.test(h) || /\bmanager\s+(?:of\s+)?(?:ai|genai|generative ai)\b/i.test(h);
  const dataAI=/(data\s*(?:&|and|och)?\s*ai|ai\s*(?:&|and|och)?\s*data)/i.test(h);
  const dataAnalytics=/\b(data|analytics)\b/i.test(h);
  const seniorData=/\b(head|director|chef)\b/i.test(h) && dataAnalytics;
  const managerDataAnalytics=/\bmanager\b/i.test(h) && /(data\s*(?:&|and)\s*analytics|analytics\s*(?:&|and)\s*data)/i.test(h);
  const dataGov=/\bdata\s+governance\b/i.test(h) && /\b(lead|head|director|manager|chef|ansvarig)\b/i.test(h);
  const swedishAI=/\b(ai[-\s]?strateg|verksamhetsutvecklare.*\bai\b|ai.*ansvarig|ansvarig.*\bai\b)/i.test(h);
  if(ai && (strategicAI || seniorAI || exactAIManager)) return "A";
  if(dataAI && /\b(lead|head|director|manager|chef|ansvarig)\b/i.test(h)) return "A";
  if(seniorData || managerDataAnalytics || dataGov) return "B";
  if(swedishAI) return "C";
  return null;
}

function fp(h:Hit){
  const oid=String(h.original_id||"").trim();
  if(oid) return "o:"+oid;
  return "f:"+[h.headline||"",h.employer?.name||"",h.publication_date||""].join("|").toLowerCase();
}
```

The `classify` function returns tier A (AI leadership), B (senior Data/Analytics or Data Governance), C (selected Swedish AI responsibility titles), or null (excluded). The headline exclusions include engineering, developer, scientist, architect, technical lead, product, programme, project, analyst, sales and other roles. A person holding AI accountability under a different job title may be missed.

## Reference observations and revision policy

- **September 2026:** 20 Sweden-wide selected advertisements after retrospective revision; 12 Stockholm; 4 Västra Götaland.
- **October 2026:** 29 Sweden-wide; 13 Stockholm; 5 Västra Götaland.
- **November 1–15:** partial period, not comparable directly with complete months.
- A 30 October *month-to-date* run had reported 30 nationally before the final, revised October extraction produced 29. This illustrates why historical API values must be frozen by vintage and not treated as immutable observations of the underlying job market.

**Interpretation:** The percentages and counts in this basket are *author-derived*, not official Arbetsförmedlingen statistics about total AI leadership vacancies. The classification is selective, revisions can change counts, and monthly samples are small. Never annualise an incomplete month, infer hires from advertisements, or attribute hiring changes to AI adoption.

## Repeatability and point-in-time verification limits

This document supplies query semantics and executable classifier logic, but **does not constitute a published immutable record-level advertisement export**. Historical API entries can be revised or removed, regional classifications can change, pagination and free-text query behavior can evolve, and original IDs are not included in the public edition. Therefore a later replay may produce different counts even with the same code. A fully independent point-in-time replication would require the preserved response dataset and exact request/response audit artifacts; the present claim is *method transparency and approximate re-execution*, not guaranteed exact reproduction.

Source API: https://historical.api.jobtechdev.se/search  
Reader evidence CSV: available to registered Market Signals Advisory members; it reports aggregate observation records, not the individual job advertisements.
