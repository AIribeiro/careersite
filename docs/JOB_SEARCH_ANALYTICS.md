# Job Search Analytics

Route: `?page=analytics&view=jobs`. Accessible from the existing analytics menu.
Owner signs in using the existing portfolio CMS account. No owner credentials,
job records, access tokens, or service-role keys are stored in source control.

## Access

`sql/job_search_owner_read.sql` adds SELECT for authenticated clients with an
owner-only RLS policy based on the signed top-level email claim and non-null
user ID. Anonymous visitors have no SELECT grant; other authenticated users
see no rows. There are no new write grants or SECURITY DEFINER functions.
Private records are fetched only after owner sign-in, with that user's token.
They are not placed in a shared Streamlit cache. The response is paginated in
500-row batches; HTTP failures are not presented as empty activity.

## Counts and scope

- Official snapshots use only `record_type=snapshot_metric` at the selected
  snapshot date. They do not change with the event filters.
- Events use primary evidence/history/activity records, deduplicated by
  logical event key (source key / ID fallback). Snapshots and secondary
  workbook representations never contribute to event counts.
- Event charts use the activity window. Undated evidence can be included in
  counts but never in dated trends or duration calculations.
- Process matching uses normalized exact employer + role; no fuzzy merging.
  Missing/placeholder roles are excluded from matched processes.
  Repeated applications to the same employer/title may collapse; this is a
  conservative proxy until the source includes a stable process ID.
- Application cohorts begin with a dated application inside the window and
  observe subsequent stages through the end date, once per linked process.
  Same-day order is allowed because dates have no consistent timestamps.
- Interview flags describe interview-related activity. Completed interviews
  require an explicit held/completed activity or `interview_completed` type.
  Invitation and rescheduling records do not imply completion.
- Next stages use explicit stage/type values (`next_stage`, `second_interview`,
  `final_interview`, `reference_check`, `offer`, `offer_received`,
  `offer_accepted`) or reference-check interaction type. Offers require an
  explicit offer stage/type. Missing progression is not proof of failure.
- Follow-ups are a parallel activity, not a mandatory stage between interview
  and offer. Response rate uses the latest sent follow-up per linked process;
  earlier responses do not resolve later follow-ups. Closed processes are
  removed from the waiting queue, but remain in the response denominator.
- State/aging/follow-up views use all available history through the end date,
  including before the activity start. Status is the latest documented status
  eligible at the cutoff, not a live assertion about the employer.
- Negative flags attached to application rows are counted as flags but never
  interpreted as rejection dates. Rejection latency needs separate dated
  decision evidence and a matched application.
- Role family/seniority are labelled title-based groupings. Source channel
  is never guessed from the mailbox providing evidence. Recruiter involvement
  is not described as recruiter-led acquisition. Qualified-conversation
  conversion is not claimed without qualification evidence.

## Data coverage at release

The official snapshot and detailed event import have different coverage.
The dashboard explicitly separates them and includes provenance and CSV
export. Missing channels, dates, and unlinked processes are visible in the
coverage view; unavailable rates/timings are not silently replaced by zero.

## Verification

Synthetic tests cover primary-event deduplication, ordered process conversion,
invitation/completion separation, retrospective status dates, missing dates,
follow-up response ordering, state changes, signed-out access, and UI rendering.
The complete imported evidence was rendered locally without adding it to git.
Database access was checked with owner, non-owner and anonymous roles.
