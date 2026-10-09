"""Private job-search measures: snapshots, canonical events, and linked cohorts."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date, timedelta
import re
from statistics import mean, median

EVENT_TYPES = {'evidence_event', 'history_event', 'activity_summary'}
FLAGS = {'Applications': 'is_application', 'Human interactions': 'is_human_interaction',
         'Interview-related events': 'is_interview', 'Recruiter interactions': 'is_recruiter_interaction',
         'Negative-decision flags': 'is_negative_decision', 'Follow-ups sent': 'follow_up_sent'}


def day(value):
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def norm(value):
    return ' '.join(str(value or '').casefold().split())


def canonical_events(records):
    unique = {}
    for row in records:
        if row.get('is_primary_analytics_record') is not True or row.get('record_type') not in EVENT_TYPES:
            continue
        key = row.get('logical_event_key') or row.get('source_key') or str(row['id'])
        previous = unique.get(key)
        if previous is None or (str(row.get('updated_at') or ''), int(row['id'])) > (str(previous.get('updated_at') or ''), int(previous['id'])):
            unique[key] = dict(row)
    return list(unique.values())


def process_key(row):
    employer, role = norm(row.get('employer')), norm(row.get('role'))
    if not employer or not role or any(x in role for x in ('not surfaced', 'not specified', 'unknown', 'multiple roles', 'various roles')):
        return None
    return employer, role


def family(role):
    text = norm(role)
    if re.search(r'governance|responsible ai', text):
        return 'AI / data governance'
    if re.search(r'\bai\b|artificial intelligence|genai', text):
        return 'AI leadership & roles'
    if re.search(r'data|analytics|intelligence', text):
        return 'Data & analytics'
    if re.search(r'architect|automation', text):
        return 'Architecture & automation'
    return 'Other / unclassified'


def seniority(role):
    text = norm(role)
    for label, pattern in [('VP / C-suite', r'\bvp\b|vice president|\bchief\b'), ('Director / Head', r'\bdirector\b|\bhead\b'),
                           ('Manager', r'\bmanager\b'), ('Lead / Principal', r'\blead\b|\bprincipal\b'), ('Senior', r'\bsenior\b')]:
        if re.search(pattern, text):
            return label
    return 'Other / unspecified'


def completed_interview(row):
    # Status may describe a later snapshot, so never use it to date completion.
    text = norm(row.get('activity'))
    return norm(row.get('event_type')) == 'interview_completed' or bool(re.search(r'interview (?:held|completed)|interview.*\bcompleted\b', text))


def progression(row):
    explicit = norm(row.get('stage_outcome') or row.get('event_type')).replace(' ', '_')
    return explicit in {'next_stage', 'second_interview', 'final_interview', 'reference_check', 'offer', 'offer_received', 'offer_accepted'} or norm(row.get('interaction_type')) == 'reference_check'


def offer(row):
    return norm(row.get('stage_outcome') or row.get('event_type')).replace(' ', '_') in {'offer', 'offer_received', 'offer_accepted'}


def rejection_event(row):
    return bool(row.get('is_negative_decision') and not row.get('is_application') and (
        norm(row.get('event_type')) in {'rejection', 'negative_decision'} or
        re.search(r'negative|reject|not selected|not proceed', norm(row.get('activity')))))


def earliest(rows, predicate, since=None):
    values = [day(r.get('event_date')) for r in rows if predicate(r) and day(r.get('event_date'))
              and (since is None or day(r.get('event_date')) >= since)]
    return min(values) if values else None


def ratio(n, d):
    return round(100 * n / d, 1) if d else None


def latency_summary(values):
    return {'n': len(values), 'mean': round(mean(values), 1) if values else None,
            'median': round(median(values), 1) if values else None}


def analyze(records, start, end, include_undated=True, employer='All employers'):
    events = canonical_events(records)
    if employer != 'All employers':
        events = [r for r in events if r.get('employer') == employer]
    through = [r for r in events if (day(r.get('event_date')) and day(r['event_date']) <= end) or
               (include_undated and not day(r.get('event_date')) and (day(r.get('snapshot_date')) or end) <= end)]
    window = [r for r in through if not day(r.get('event_date')) or day(r['event_date']) >= start]
    counts = {label: sum(bool(r.get(flag)) for r in window) for label, flag in FLAGS.items()}
    weekly, monthly = defaultdict(Counter), defaultdict(Counter)
    for r in window:
        d = day(r.get('event_date'))
        if not d:
            continue
        for label, predicate in [('Applications', bool(r.get('is_application'))), ('Human interactions', bool(r.get('is_human_interaction'))),
                                 ('Completed interviews', completed_interview(r)), ('Dated rejection evidence', rejection_event(r))]:
            if predicate:
                weekly[(d - timedelta(days=d.weekday())).isoformat()][label] += 1
                monthly[d.replace(day=1).isoformat()][label] += 1
    def series(data):
        return [{'Date': d, 'Measure': label, 'Events': n} for d in sorted(data) for label, n in data[d].items()]

    groups = defaultdict(list)
    for r in through:
        key = process_key(r)
        if key:
            groups[key].append(r)
    processes = []
    for key, rows in groups.items():
        rows.sort(key=lambda r: (str(r.get('event_date') or ''), int(r['id'])))
        last = rows[-1]
        applied = earliest(rows, lambda r: r.get('is_application'))
        human = earliest(rows, lambda r: r.get('is_human_interaction'), applied) if applied else None
        interview = earliest(rows, completed_interview, human) if human else None
        progressed = earliest(rows, progression, interview) if interview else None
        offered = earliest(rows, offer, progressed) if progressed else None
        rejected = earliest(rows, rejection_event, applied) if applied else None
        statuses = [r for r in rows if r.get('status') and (day(r.get('snapshot_date')) or day(r.get('event_date')) or end) <= end]
        state = max(statuses, key=lambda r: (str(r.get('snapshot_date') or r.get('event_date') or ''), str(r.get('event_date') or ''), int(r['id']))) if statuses else {}
        closed = bool(state.get('is_closed_or_paused') or state.get('is_negative_decision'))
        active = bool(state.get('is_active')) and not closed
        status = 'Closed / paused' if closed else 'Active documented' if active else 'Unresolved / unknown'
        app_row = next((r for r in rows if r.get('is_application') and day(r.get('event_date')) == applied), {}) if applied else {}
        source = app_row.get('source_channel') or 'Unrecorded'
        follow_rows = [r for r in rows if r.get('follow_up_sent') or r.get('follow_up_required') or r.get('follow_up_status') or r.get('next_step')]
        follow = max(follow_rows, key=lambda r: (str(r.get('follow_up_date') or r.get('event_date') or ''), int(r['id']))) if follow_rows else {}
        sent_rows = [r for r in rows if r.get('follow_up_sent') and (day(r.get('follow_up_date')) or day(r.get('event_date')) or end) <= end]
        last_sent = max(sent_rows, key=lambda r: (str(r.get('follow_up_date') or r.get('event_date') or ''), int(r['id']))) if sent_rows else {}
        sent_date = day(last_sent.get('follow_up_date')) or day(last_sent.get('event_date'))
        responses = [r for r in rows if r.get('response_received') is True and
                     (day(r.get('response_date')) or day(r.get('event_date'))) and sent_date and
                     sent_date <= (day(r.get('response_date')) or day(r.get('event_date'))) <= end]
        replied = bool((last_sent.get('response_received') is True and (day(last_sent.get('response_date')) or day(last_sent.get('event_date')) or end) <= end) or responses)
        waiting = bool(last_sent and not replied and not closed)
        dates = [day(r.get('event_date')) for r in rows if day(r.get('event_date'))]
        last_date = max(dates) if dates else None
        due = day(follow.get('next_step_due_date'))
        processes.append({'Employer': last['employer'], 'Role': last['role'], 'State': status,
                          'Documented status': state.get('status') or 'Unknown', 'Status as of': state.get('snapshot_date') or state.get('event_date'),
                          'Last event': last_date.isoformat() if last_date else None,
                          'Days since event': (end-last_date).days if last_date else None,
                          'Days since application': (end-applied).days if applied else None,
                          'Human events': sum(bool(r.get('is_human_interaction')) for r in rows),
                          'Interview evidence': any(r.get('is_interview') for r in rows),
                          'Completed interview': any(completed_interview(r) for r in rows),
                          'Family': family(last['role']), 'Seniority': seniority(last['role']), 'Channel': source,
                          'Recruiter involved': any(r.get('is_recruiter_interaction') for r in rows),
                          'Applied': applied, 'Human': human, 'Interview': interview, 'Progressed': progressed, 'Offered': offered,
                          'Rejection days': (rejected-applied).days if rejected and applied else None,
                          'Contact days': (human-applied).days if human and applied else None,
                          'Follow-up sent': bool(last_sent), 'Response': replied, 'Waiting': waiting,
                          'Follow-up status': follow.get('follow_up_status') or 'Unrecorded',
                          'Waiting days': (end-sent_date).days if waiting and sent_date else None,
                          'Next step': follow.get('next_step') or 'Not recorded', 'Due': due.isoformat() if due else None,
                          'Overdue': bool(due and due < end and not closed),
                          'Follow-up due': bool(not closed and (follow.get('follow_up_status') == 'candidate_follow_up_due' or (follow.get('follow_up_required') and not last_sent))),
                          'Contact': follow.get('contact_name') or last.get('contact_name') or 'Not recorded',
                          'Evidence rows': len(rows)})
    cohort = [p for p in processes if p['Applied'] and start <= p['Applied'] <= end]
    funnel = [{'Stage': label, 'Processes': sum(bool(p[field]) for p in cohort)} for label, field in
              [('Applied', 'Applied'), ('Human contact', 'Human'), ('Completed interview', 'Interview'), ('Explicit next stage', 'Progressed'), ('Offer documented', 'Offered')]]
    # Follow-ups are a parallel activity, not a required hiring stage.
    def cohorts(dimension):
        result = []
        for value in sorted({p[dimension] for p in cohort}, key=str):
            subset = [p for p in cohort if p[dimension] == value]
            humans, interviews = sum(bool(p['Human']) for p in subset), sum(bool(p['Interview']) for p in subset)
            result.append({'Group': str(value), 'Applications': len(subset), 'Human contacts': humans, 'Interviews': interviews,
                           'Human %': ratio(humans,len(subset)), 'Interview %': ratio(interviews,len(subset))})
        return result
    return {'events': window, 'counts': counts, 'weekly': series(weekly), 'monthly': series(monthly), 'processes': processes,
            'cohort': cohort, 'funnel': funnel, 'family': cohorts('Family'), 'seniority': cohorts('Seniority'),
            'channel': cohorts('Channel'), 'recruiter': cohorts('Recruiter involved'),
            'contact_latency': latency_summary([p['Contact days'] for p in cohort if p['Contact days'] is not None]),
            'rejection_latency': latency_summary([p['Rejection days'] for p in cohort if p['Rejection days'] is not None]),
            'quality': {'canonical': len(events), 'undated': sum(not day(r.get('event_date')) for r in events),
                        'unlinked': sum(process_key(r) is None for r in through),
                        'source_missing': sum(not r.get('source_channel') for r in window),
                        'mixed_application_negative': sum(bool(r.get('is_application') and r.get('is_negative_decision')) for r in window)}}
