"""Evidence-led outlook using only the already-public recruitment aggregates."""
from datetime import date


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
    st.write("Keep two tracks open: pursue the strongest documented opportunities and prepare a fallback that does not depend on a predicted start date.")
    left, right = st.columns(2)
    with left:
        st.markdown("**Now · protect momentum**")
        st.write("Privately confirm the next step and expected response date for each live conversation. "
                 "Keep targeted applications and direct human outreach going until an offer is agreed.")
        st.markdown("**In 14 days · review the evidence**")
        st.write("If there is no new human contact or stage progression, first check recording completeness, "
                 "then change one part of the search—target roles, positioning or outreach route—and review the result.")
    with right:
        st.markdown("**Plan for 30, 60 and 90 more days**")
        st.write("Privately map essential commitments and confirmed resources for each scenario. "
                 "Do not treat a predicted offer week, pending benefit decision or possible contract as secured income.")
        st.markdown("**Choose a fallback trigger in advance**")
        st.write("Set your own latest date for activating interim, contract or bridge work, allowing for its hiring lead time. "
                 "If that date arrives without a signed offer, activate the fallback while continuing the leadership search.")
    st.caption("These are planning checkpoints, not forecasts of how long the search will take. "
               "Personal finances, contacts and employer details are neither collected nor displayed here.")
    st.divider()
