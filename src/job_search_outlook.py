"""Evidence-led outlook using only the already-public recruitment aggregates."""
from datetime import date, timedelta
from statistics import median
from math import ceil


def outlook(jobs, stages, today):
    def count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    windows = {"recent": {k: 0 for k in ("applications", "responses", "interviews")},
               "prior": {k: 0 for k in ("applications", "responses", "interviews")}}
    latest = None
    for row in (jobs or {}).get("daily", []):
        try:
            day = date.fromisoformat(row["d"])
        except (KeyError, ValueError, TypeError):
            continue
        age = (today - day).days
        if age < 0:
            continue
        if count(row.get("responses")) or count(row.get("interviews")):
            latest = max(latest, day) if latest else day
        key = "recent" if age < 28 else "prior" if age < 56 else None
        if key:
            for metric in windows[key]:
                windows[key][metric] += count(row.get(metric))
    recent = windows["recent"]
    recent_stages = 0
    stale_stages = 0
    # Stage ages are 30-day buckets, not precise last-contact dates.
    fresh_inputs = False
    try:
        fresh_inputs = 0 <= (today - date.fromisoformat(stages["as_of"])).days <= 1
    except (KeyError, ValueError, TypeError):
        pass
    for row in (stages or {}).get("stage_buckets", []) if fresh_inputs else []:
        if row.get("stage") not in ("conversation", "interview", "progression"):
            continue
        if row.get("stage_weight") == 1 and row.get("age_month_index") == 0:
            recent_stages += count(row.get("n"))
        else:
            stale_stages += count(row.get("n"))
    if not jobs:
        verdict = "Not enough available evidence to judge current momentum."
    elif recent["interviews"]:
        verdict = "Yes—recent completed interviews are credible evidence of employer engagement."
    elif recent["responses"]:
        verdict = "There is recent human interest, but the evidence is earlier-stage."
    elif recent_stages:
        verdict = "Recent recorded pipeline stages are encouraging, but new opportunity generation is not yet confirmed."
    else:
        verdict = "Current evidence does not establish continuing opportunity generation."
    caution = ("Recent engagement does not prove these processes remain open or that an offer will follow."
               if recent["responses"] or recent["interviews"] else
               "No recorded recent interaction is not proof of no interest; check that the source records are up to date.")
    return dict(verdict=verdict, caution=caution, latest=latest,
                recent=recent, prior=windows["prior"], fresh_stages=recent_stages,
                stale_stages=stale_stages, stages_available=fresh_inputs,
                jobs_available=bool(jobs))


def preparation_plan(jobs, stages, today):
    """Transparent decision rules, not learned probabilities or financial advice."""
    model = outlook(jobs, stages, today)
    days = set()
    for row in (jobs or {}).get('daily', []):
        try:
            day = date.fromisoformat(row['d'])
            if 0 <= (today-day).days < 90 and (float(row.get('responses') or 0)>0 or float(row.get('interviews') or 0)>0):
                days.add(day)
        except (ValueError, TypeError, KeyError):
            continue
    days = sorted(days)
    gaps = [(b-a).days for a,b in zip(days,days[1:])]
    typical = median(gaps) if len(gaps)>=3 else None
    # Review interval is an explicit policy applied to observed cadence.
    interval = min(14, max(3, ceil(typical*1.5))) if typical is not None else 7
    quiet = (today-model['latest']).days if model['latest'] else None
    declining = (model['prior']['responses']>0 and
                 model['recent']['responses']<model['prior']['responses'] and
                 model['recent']['interviews']<=model['prior']['interviews'])
    unsupported_volume = (model['recent']['applications']>model['prior']['applications'] and
                          model['recent']['responses']<=model['prior']['responses'])
    if not model['jobs_available'] or not model['stages_available']:
        priority = 'Verify evidence before changing course'
        reason = 'Activity or current-stage inputs are unavailable or out of date.'
        action = 'Refresh the records and confirm current process status. Missing data must not trigger a pessimistic conclusion.'
        fallback = 'Keep contingency options ready; there is not enough current evidence to change their urgency.'
    elif quiet is None or (quiet >= interval and not model['fresh_stages']):
        priority = 'Bring contingency preparation forward'
        reason = (f'No recorded human engagement for {quiet} days; no recently recorded active human-stage process.'
                  if quiet is not None else 'No dated human engagement or recent active human-stage process is recorded.')
        action = 'Verify that records are complete, confirm older processes, and prioritize routes to new human conversations.'
        fallback = 'Review the next 30 days first and shortlist realistic interim or bridge options now. Prepare 60- and 90-day alternatives alongside the leadership search.'
    elif declining or (quiet is not None and quiet >= interval):
        priority = 'Review slowing momentum'
        reason = ('Contacts fell versus the previous 28 days without an increase in interviews.' if declining
                  else f'{quiet} days since the latest recorded human engagement exceeds the {interval}-day review interval.')
        action = 'Confirm next steps in the existing pipeline and test one change in targeting or outreach. Keep the strongest processes moving.'
        fallback = 'Make the 30-day fallback practical now: check availability and lead times for interim options, while retaining 60- and 90-day scenarios.'
    elif model['recent']['interviews'] and model['fresh_stages']:
        priority = 'Protect interview momentum; keep alternatives ready'
        reason = f"{model['recent']['interviews']} completed interview events in 28 days and {model['fresh_stages']} recently recorded active human-stage processes."
        action = 'Prioritize interview preparation and agreed next steps, while continuing selective applications and outreach.'
        fallback = 'Maintain the 30/60/90-day contingency plan. Current engagement supports continued pursuit, but does not justify relying on a start date.'
    else:
        priority = 'Convert early interest into next steps'
        reason = f"{model['recent']['responses']} human-contact events and {model['recent']['interviews']} completed interview events in 28 days."
        action = 'Seek a concrete next step from current conversations and keep generating new ones.'
        fallback = 'Prepare the 30-day fallback now; early interest is not secured work. Keep 60- and 90-day alternatives available.'
    if unsupported_volume and model['jobs_available']:
        action += ' Applications increased without more contacts: review fit and access to decision-makers before adding volume.'
    due = model['latest'] + timedelta(days=interval) if model['latest'] else None
    return dict(priority=priority,reason=reason,action=action,fallback=fallback,
                review_date=due,review_due=due is None or due<=today,
                interval=interval,typical_gap=typical,gap_sample=len(gaps))


def render_search_outlook(jobs, stages, today):
    import streamlit as st
    model = outlook(jobs, stages, today)
    st.subheader("Am I still generating credible job opportunities?")
    st.markdown(f"**{model['verdict']}**")
    st.write(model["caution"])
    a, b, c = st.columns(3)
    for col, key, label in ((a, "responses", "Human contacts · 28 days"),
                            (b, "interviews", "Completed interviews · 28 days")):
        col.metric(label, model["recent"][key] if model["jobs_available"] else "Unavailable",
                   delta=f"{model['recent'][key] - model['prior'][key]:+d} vs previous 28 days" if model["jobs_available"] else None,
                   delta_color="off")
    c.metric("Recorded active human-stage processes · <30d",
             model["fresh_stages"] if model["stages_available"] else "Unavailable")
    st.caption("Contacts and interviews are deduplicated process-day events; they may overlap and must not be added. "
               "The third card uses distinct latest-stage processes, excludes provisionally active records and is not a live employer status.")
    if model["latest"]:
        st.caption(f"Latest recorded human-contact or completed-interview date: {model['latest']:%d %b %Y} "
                   f"· {(today-model['latest']).days} days ago. Reporting checked {today:%d %b %Y}; this is not proof the import is complete.")
    if model["stale_stages"]:
        st.info(f"{model['stale_stages']} other human-stage processes are older or only provisionally active. "
                "Confirm their status before relying on them in a plan.")
    if model["recent"]["applications"] > model["prior"]["applications"] and model["recent"]["responses"] <= model["prior"]["responses"]:
        st.info("Applications rose without a rise in recorded human contacts. Review role fit and routes to a real conversation before increasing volume.")
    st.caption("Portfolio traffic and market signals provide context, not proof of a job opportunity. "
               "These rules refresh with the source data; they are not a calibrated offer prediction.")
    st.subheader("If the next job takes longer: prepare without assuming failure")
    plan = preparation_plan(jobs, stages, today)
    st.markdown(f"**{plan['priority']}**")
    st.write(f"Why this recommendation: {plan['reason']}")
    left, right = st.columns(2)
    with left:
        st.markdown("**Current search priority**")
        st.write(plan['action'])
        st.markdown('**Review now**' if plan['review_due'] else f"**Next evidence review · {plan['review_date']:%d %b %Y}**")
        if plan['typical_gap'] is not None:
            st.write(f"Observed median gap between human-engagement dates: {plan['typical_gap']:g} days "
                     f"({plan['gap_sample']} gaps within 90 days). Review interval: {plan['interval']} days.")
        else:
            st.write('Too few engagement dates to estimate a cadence. A 7-day review interval is used as a planning default.')
        st.caption('Review date is anchored to the last recorded contact or interview, not reset when the page refreshes. New evidence can change the recommendation immediately.')
    with right:
        st.markdown("**Contingency preparation priority**")
        st.write(plan['fallback'])
        st.markdown("**Choose a fallback trigger in advance**")
        st.write("Set your own latest date for activating interim, contract or bridge work, allowing for its hiring lead time. "
                 "If that date arrives without a signed offer, activate the fallback while continuing the leadership search.")
    st.caption('Policy: where at least three observed gaps exist, review after 1.5× the median gap, bounded to 3–14 days. '
               'This is an adjustable planning rule, not a statistically validated threshold. The 30/60/90-day scenarios remain stress tests; '
               'their preparation priority changes with the evidence. Personal resources and bridge-work lead times are not known, so no automatic income deadline is inferred. '
               "These are planning checkpoints, not forecasts of how long the search will take. "
               "Personal finances, contacts and employer details are neither collected nor displayed here.")
    st.divider()
