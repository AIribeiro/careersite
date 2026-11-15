# Executive AI Leadership Workshop — service operating contract

Site: https://jairribeiro.com/?page=advisory-access&view=workshop
Public discovery: https://jairribeiro.com/?page=advisory
Model: leadership-workshop-v1

## Purpose and access

Free self-service leadership decision aid for verified Advisory members. It does not independently verify evidence, certify maturity, approve AI investment or deployment, or establish legal compliance.

Individual mode: one private assessment, 21 evidence-focused questions, two executive dilemmas, a reasoned leadership readiness position, suggested owners, a recorded decision and a PDF.

Team mode: an organizer may invite up to 11 additional participants. Each participant chooses whether to share their individual answers. The organizer sees invitation and completion status but cannot read unshared responses. Team comparisons require three shared completed responses and must never be called anonymous, because small-group identification remains possible.

No payment, subscription, editorial opt-in or manual approval for self-service assessment. Selective personal pro-bono advisory remains a separate reviewed request workflow.

## Source modules

- src/page_advisory_leadership_logic.py — question bank, weights, evidence coverage, critical gates, exercises and team aggregation
- src/page_advisory_leadership_workshop.py — private member UI and verified member-token persistence
- src/page_advisory_leadership_report.py — two-page executive PDF from user inputs
- src/page_advisory_portal.py — member route
- src/page_advisory_member_experience.py — navigation and member service card
- src/site_reader_navigation.py — same-WebSocket deep link
- src/page_public_services.py — public offer and privacy
- tests/test_leadership_workshop.py and tests/leadership_workshop_smoke_app.py — logic and UI checks
- .github/workflows/leadership-workshop-regression.yml — independent release check

## Decision methodology

Seven dimensions, 21 questions: strategy 15%, governance 15%, leadership accountability 20%, data 10%, adoption 20%, operations 10%, business value 10%.

Answers run from not established (0) to demonstrated (3). Unanswered questions are missing evidence rather than low maturity. A weighted index is withheld unless at least 18 of 21 questions are answered and each dimension has at least two responses. Critical failures in control review, stop authority or business ownership override the average.

Outcomes: Evidence incomplete; Leadership reset required; Targeted changes required; Foundations established. All results are self-reported; weights and thresholds are proposed design choices rather than validated industry benchmarks.

Dilemmas: competing investments, governance authority, pilot adoption and employee concerns. The weakest assessed dimensions determine two discussion exercises.

## Database and privacy

Supabase migrations applied: portfolio_leadership_workshop_core_v1 and leadership_participant_completion_state.

Tables: public.portfolio_leadership_workshops, public.portfolio_leadership_participants, public.portfolio_leadership_responses.

All three tables use RLS and deny anonymous reading. Workshop records are readable by owner and accepted members; invitation records by organizer and recipient; answers by respondent and, with explicit sharing, organizer. Authenticated clients cannot update workshop owner_id or assessment user_id. No service-role key is used by the new UI.

Invitations are stored but not emailed automatically. The organizer shares the branded sign-in URL manually; invitees accept or decline in Invitations and control whether answers are shared. No customer sample records are seeded.

## Release and follow-up

Focused regression: python -m unittest discover -s tests -p test_leadership_workshop.py -v

Check Python parsing, deterministic rules, PDF bytes, synthetic Streamlit rendering, database permissions, separate-account invitation and sharing, history, mobile layout and masked-domain navigation.

An organizer can remove invited or accepted non-owner participants, deleting associated responses. An invited participant can leave and delete their own answers. The organizer can permanently delete an entire workshop and its records after confirming its exact title.

Future hardening: optional transactional email with rate limits, finer-grained autosave, and a formal retention/deletion schedule before wider distribution. Any unrelated failing site workflows must be reported independently.
