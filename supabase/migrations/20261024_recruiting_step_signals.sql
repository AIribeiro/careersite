-- Owner-only recruiter timing signals. These are evidence inputs, not inferred commitments.
create table if not exists public.careersite_recruiting_step_signals(
 id bigint generated always as identity primary key,
 opportunity_id bigint not null references public.careersite_recruiting_opportunities(id) on delete cascade,
 signal_key text not null unique,
 kind text not null check(kind in ('employer_response_window','referral_intent','conditional_stage','stage_progression')),
 event_label text not null,
 anchor_date date not null,
 window_start date,
 window_end date,
 source_kind text not null check(source_kind in ('outlook','gmail','interview_review','calendar','candidate_report')),
 source_reference text not null,
 evidence_note text not null default '',
 recorded_at timestamptz not null default now(),
 check (window_start is null or window_end is null or window_end>=window_start),
 check (source_reference <> '')
);
create index if not exists careersite_recruiting_step_signals_opportunity
 on public.careersite_recruiting_step_signals(opportunity_id,anchor_date desc);
alter table public.careersite_recruiting_step_signals enable row level security;
revoke all on public.careersite_recruiting_step_signals from public,anon,authenticated;
grant select,insert,update,delete on public.careersite_recruiting_step_signals to authenticated;
grant usage,select on sequence public.careersite_recruiting_step_signals_id_seq to authenticated;
create policy "Owner selects recruiting signals" on public.careersite_recruiting_step_signals
for select to authenticated using ((select auth.uid()) is not null
 and lower(coalesce((select auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 and coalesce((select auth.jwt())->>'is_anonymous','false')='false');
create policy "Owner inserts recruiting signals" on public.careersite_recruiting_step_signals
for insert to authenticated with check ((select auth.uid()) is not null
 and lower(coalesce((select auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 and coalesce((select auth.jwt())->>'is_anonymous','false')='false');
create policy "Owner updates recruiting signals" on public.careersite_recruiting_step_signals
for update to authenticated using ((select auth.uid()) is not null
 and lower(coalesce((select auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 and coalesce((select auth.jwt())->>'is_anonymous','false')='false')
with check ((select auth.uid()) is not null
 and lower(coalesce((select auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 and coalesce((select auth.jwt())->>'is_anonymous','false')='false');
create policy "Owner deletes recruiting signals" on public.careersite_recruiting_step_signals
for delete to authenticated using ((select auth.uid()) is not null
 and lower(coalesce((select auth.jwt())->>'email',''))='jair.ribeiro@outlook.it'
 and coalesce((select auth.jwt())->>'is_anonymous','false')='false');

insert into public.careersite_recruiting_step_signals
(opportunity_id,signal_key,kind,event_label,anchor_date,window_start,window_end,source_kind,source_reference,evidence_note)
values
(2,'betsson-sb-recruiter-reply-20261023','employer_response_window',
'Adrian: hiring-manager review and reply', '2026-10-23','2026-10-26','2026-10-27',
'interview_review','careersite_post_interview_reviews.meeting_id=15 / transcript 23 Oct',
'Recruiter intended to present candidate to Director of Sports Product Monday 26 Oct and respond Monday or Tuesday. Indication, not guaranteed confirmation or interview booking.'),
(16,'betsson-ai-referral-20261023','referral_intent',
'Adrian to check fit with Head of AI recruiter', '2026-10-23',null,null,
'interview_review','careersite_recruiting_opportunities.id=16 notes 23 Oct / interview meeting 15',
'At separate Sportsbook role screening, Adrian said he would discuss application with colleague. No firm reply date or stage progression.'),
(7,'kpmg-conditional-partner-20261014','conditional_stage',
'Potential Tax Transformation partner interview','2026-10-14',null,null,
'outlook','Outlook Therese Schulze email 14 Oct 2026 Re: Interview KPMG AI Lead Manager Tax & Legal Technology',
'Final shortlisted candidate(s) may meet partner heading Tax Transformation; not confirmed as scheduled or selected.'),
(7,'kpmg-stage1-invite-20261013','stage_progression',
'Invitation to second interview', '2026-10-13','2026-10-13','2026-10-13',
'outlook','Outlook Therese Schulze invitation 13 Oct 2026 / second meeting 22 Oct',
'Empirical prior in same vacancy: round 1 held 7 Oct, invitation to next stage 13 Oct = 6 calendar days.'),
(8,'leovegas-stage1-invite-20261019','stage_progression',
'Invitation to second interview','2026-10-19','2026-10-19','2026-10-19',
'outlook','Outlook LeoVegas - 2nd Stage Invitation 19 Oct 2026 from Magdalena Roman',
'Empirical prior in same vacancy: round 1 held 2 Oct, invitation to next stage 19 Oct = 17 calendar days.')
on conflict(signal_key) do nothing;
comment on table public.careersite_recruiting_step_signals is
'Private, dated source statements used as inputs for recruiting planning forecasts; not predictions, offers or live mailbox sync.';
