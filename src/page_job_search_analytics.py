"""Owner-only job-search dashboard. Never cache private rows across sessions."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date
from zoneinfo import ZoneInfo
from datetime import datetime
import csv
import io
import altair as alt
import streamlit as st

from job_search_metrics import analyze, canonical_events, day, ratio, completed_interview
from page_job_search_trends import render_job_search_trends
from page_portfolio_job_correlations import render_portfolio_job_correlations
from page_job_market_insights import render_market_relationships
from site_cms import _request_json, _rest_url

FIELDS = ('id,record_type,event_date,snapshot_date,employer,role,status,event_type,stage_outcome,activity,'
          'source_channel,metric_name,metric_value,metric_value_text,interpretation,is_application,'
          'is_human_interaction,is_interview,is_recruiter_interaction,is_negative_decision,is_active,'
          'is_closed_or_paused,is_primary_analytics_record,logical_event_key,interaction_type,'
          'interaction_direction,contact_name,contact_role,follow_up_required,follow_up_sent,follow_up_date,'
          'follow_up_status,response_received,response_date,next_step,next_step_due_date,interaction_notes,'
          'source_file,source_language,source_sheet,source_row,source_key,date_basis,updated_at')


def fetch_job_records(token):
    rows, offset = [], 0
    while True:
        batch = _request_json('GET', _rest_url(
            f'job_search_analytics?select={FIELDS}&order=id.asc&limit=500&offset={offset}'), token=token)
        if not isinstance(batch, list):
            raise RuntimeError('Unexpected job-search response.')
        rows.extend(batch)
        if len(batch) < 500:
            return rows
        offset += 500
        if offset >= 100000:
            raise RuntimeError('The evidence table is too large for this view; narrow the server query before continuing.')


def bar(rows, category, value, *, color='#527bd9', percent=False, preserve_order=False):
    if not rows:
        st.info('No supporting records for this measure in the selected scope.')
        return
    clean = [r for r in rows if r.get(value) is not None]
    if not clean:
        st.info('This measure needs more complete evidence.')
        return
    hover = alt.selection_point(fields=[category], on='pointerover', clear='pointerout', empty=False)
    base = alt.Chart(alt.Data(values=clean)).encode(
        y=alt.Y(f'{category}:N', sort=[r[category] for r in clean] if preserve_order else '-x', title=None, axis=alt.Axis(labelLimit=260, domain=False, ticks=False)),
        x=alt.X(f'{value}:Q', title=value, axis=alt.Axis(tickMinStep=None if percent else 1, gridOpacity=.12)),
        tooltip=[alt.Tooltip(f'{category}:N'), alt.Tooltip(f'{value}:Q', format='.1f' if percent else ',')],
    )
    bars = base.mark_bar(cornerRadiusEnd=6).encode(color=alt.condition(hover, alt.value('#22b8b0'), alt.value(color))).add_params(hover)
    labels = base.mark_text(align='left', dx=6).encode(text=alt.Text(f'{value}:Q', format='.1f' if percent else ','))
    st.altair_chart((bars+labels).properties(height=max(190, len(clean)*34)), width='stretch')


def details(title, rows):
    with st.expander(title):
        if rows:
            st.dataframe(rows, hide_index=True, width='stretch')
        else:
            st.caption('No records in this scope.')


def rate_label(n, d):
    return f'{n/d:.0%} · {n}/{d}' if d else 'Unavailable · no denominator'


def _snapshot(records):
    snapshots = [r for r in records if r.get('record_type') == 'snapshot_metric' and r.get('snapshot_date')]
    dates = sorted({r['snapshot_date'] for r in snapshots}, reverse=True)
    st.subheader('Official job-search snapshot')
    if not dates:
        st.info('No official snapshot has been imported.')
        return
    selected = st.selectbox('Snapshot date', dates, key='job_snapshot')
    current = sorted((r for r in snapshots if r['snapshot_date'] == selected), key=lambda r: int(r['id']))
    by_name = {r['metric_name']: r for r in current}
    definitions = [('Confirmed application submissions','Documented applications'),
                   ('Explicit negative decisions','Negative decisions'),
                   ('Employer-canceled / closed / paused processes','Employer closed / paused'),
                   ('Conservative active/unresolved working figure','Active / unresolved minimum')]
    columns = st.columns(4)
    chart = []
    for column, (key, label) in zip(columns, definitions):
        r = by_name.get(key, {})
        value = r.get('metric_value')
        rendered = f'{float(value):,.0f}' if value is not None else r.get('metric_value_text') or '—'
        if value is not None and key.startswith('Conservative'):
            rendered += '+'
        column.metric(label, rendered, help=r.get('interpretation') or 'Not included in this snapshot.')
        if value is not None and key != 'Confirmed application submissions':
            chart.append({'Outcome': label, 'Processes': float(value)})
    bar(chart, 'Outcome', 'Processes')
    st.caption(f'Official reported totals as of {selected}; independent of the event filters below. '
               'Active / unresolved is a conservative accounting remainder, not a count of engaged hiring teams.')
    details('Snapshot definitions and source evidence', [{k:r.get(v) for k,v in {
        'Metric':'metric_name','Value':'metric_value','Text':'metric_value_text','Definition':'interpretation',
        'File':'source_file','Sheet':'source_sheet','Row':'source_row'}.items()} for r in current])
    history = [{'Date':r['snapshot_date'],'Metric':r['metric_name'],'Value':float(r['metric_value'])}
               for r in snapshots if r.get('metric_value') is not None and r['metric_name'] in dict(definitions)]
    if len(dates) > 1:
        st.altair_chart(alt.Chart(alt.Data(values=history)).mark_line(point=True).encode(
            x='Date:T',y='Value:Q',color='Metric:N',tooltip=['Date:T','Metric:N','Value:Q']), width='stretch')


def _cohort_chart(rows, title):
    st.subheader(title)
    plotted = []
    for row in rows:
        for metric in ('Applications','Human contacts','Interviews'):
            plotted.append({'Group':row['Group'],'Stage':metric,'Processes':row[metric]})
    if plotted:
        st.altair_chart(alt.Chart(alt.Data(values=plotted)).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('Group:N',title=None,axis=alt.Axis(labelLimit=240)),
            x=alt.X('Processes:Q',axis=alt.Axis(tickMinStep=1)), yOffset='Stage:N',
            color=alt.Color('Stage:N',scale=alt.Scale(range=['#a5b4fc','#527bd9','#22b8b0'])),
            tooltip=['Group:N','Stage:N','Processes:Q']).properties(height=max(220,len(rows)*85)),width='stretch')
    else:
        st.info('No dated, linked application processes in this cohort.')
    details('Exact counts and conversion percentages · '+title, rows)


def render_job_report(records):
    """Decision-first job analysis with optional evidence inspection."""
    events = canonical_events(records)
    if not events:
        st.info("No canonical job events are available.")
        return
    today = datetime.now(ZoneInfo("Europe/Stockholm")).date()
    observed = [day(r.get("event_date")) for r in events
                if day(r.get("event_date")) and day(r.get("event_date")) <= today]
    earliest = min(observed) if observed else today
    with st.expander("Refine dates and employer",expanded=False):
        a,b,c = st.columns([1,1,2])
        start = a.date_input("Activity from",earliest,max_value=today,key="job_start")
        end = b.date_input("Through / status as of",today,max_value=today,key="job_end")
        employer = c.selectbox("Employer",["All employers"]+
                     sorted({r["employer"] for r in events if r.get("employer")}))
        undated = st.checkbox("Include undated evidence in process lists",
                              value=True,key="job_include_undated")
    if start > end:
        st.warning("Choose an end date on or after the start date.")
        return
    report = analyze(records,start,end,undated,employer)
    rows, processes, cohort = report["events"], report["processes"], report["cohort"]
    active = [p for p in processes if p["State"]=="Active documented"]
    waiting = [p for p in processes if p["Waiting"]]
    due = [p for p in processes if p["Overdue"] or p["Follow-up due"]]
    inbound = sum(bool(r.get("is_human_interaction")) and
                  str(r.get("interaction_direction") or "").lower() in ("inbound","two_way")
                  for r in rows)

    st.caption(f"Selected evidence: {start:%d %b %Y}–{end:%d %b %Y}"
               + (f" · {employer}" if employer != "All employers" else "")
               + ". Primary, deduplicated events only; the official snapshot remains separate.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Recorded applications",report["counts"]["Applications"],
              help="Primary application events in the selected window, not the official cumulative count.")
    c2.metric("Inbound / two-way contacts",inbound,
              help="Recorded human replies and two-way contacts only; outbound messages are excluded.")
    c3.metric("Completed interviews",sum(completed_interview(r) for r in rows),
              help="Invitation and scheduled interviews do not count as completed.")
    c4.metric("Follow-up actions due",len(due),
              help="Documented follow-up requirements or overdue next steps, not inferred ATS status.")

    if due:
        st.warning(f"{len(due)} documented process(es) need a follow-up or overdue-step review. "
                   "Prioritize these over adding low-fit applications.")
    elif waiting:
        st.info(f"{len(waiting)} processes await a recorded response. "
                "Silence is not a rejection; check elapsed time and the actual next action.")
    else:
        st.caption(f"{len(active)} processes are documented as active. "
                   "No explicit overdue follow-up is recorded in the current evidence.")
    if report["quality"]["source_missing"]:
        st.caption(f"Source channel is missing for {report['quality']['source_missing']} "
                   "selected event records. Channel-level comparisons are incomplete.")

    focus = st.segmented_control(
        "Analyze",
        options=["decisions","conversion","correlations","evidence"],
        default="decisions",
        format_func=lambda v:{
            "decisions":"Decisions & momentum",
            "conversion":"Conversion & targeting",
            "correlations":"Relationships",
            "evidence":"Sources & methods",
        }[v],
        key="job_analysis_focus",
        width="stretch",
    ) or "decisions"
    st.divider()

    if focus == "decisions":
        from job_search_trends import analyze_trends, SERIES
        trend = analyze_trends(records,start,end,employer)
        recent, prior = trend["recent"], trend["previous"]
        comparable = bool(prior and trend["coverage"]["previous_dated"] >= 5
                          and trend["baseline_available"])
        st.subheader("Are applications turning into conversations?")
        if comparable:
            applications_now, applications_before = recent[SERIES[0]], prior[SERIES[0]]
            contacts_now, contacts_before = recent[SERIES[1]], prior[SERIES[1]]
            st.markdown(
                f"**Last 28 days vs previous 28:** {applications_now} applications "
                f"({applications_now-applications_before:+d}), "
                f"{contacts_now} inbound/two-way contact processes "
                f"({contacts_now-contacts_before:+d})."
            )
            if applications_now > applications_before and contacts_now <= contacts_before:
                st.info("Application volume is increasing without stronger observed contact. "
                        "Review employer access and role match before increasing volume further.")
            elif contacts_now > contacts_before:
                st.info("Recorded conversations increased. Follow through on live processes "
                        "before prioritizing more submissions.")
        else:
            st.info("Too little comparable dated evidence for a credible 28-day trend. "
                    "The chart shows recorded history, not a complete account of the market.")
        trend_group = st.segmented_control(
            "Activity cadence",["Week","Month"],default="Week",
            key="job_decision_cadence") or "Week"
        plotted = [r for r in report["weekly" if trend_group=="Week" else "monthly"]
                   if r["Measure"] in ("Applications","Human interactions","Completed interviews")]
        if plotted:
            st.altair_chart(alt.Chart(alt.Data(values=plotted)).mark_line(point=True).encode(
                x=alt.X("Date:T",title=trend_group),
                y=alt.Y("Events:Q",title="Dated primary events",
                        axis=alt.Axis(tickMinStep=1)),
                color="Measure:N",tooltip=["Date:T","Measure:N","Events:Q"]
            ).properties(height=300),width="stretch")
        else:
            st.caption("No dated events are available for the selected interval.")
        st.subheader("Next recruitment actions")
        action_rows = sorted(
            (p for p in processes if p["Overdue"] or p["Follow-up due"] or p["Waiting"]),
            key=lambda p:(not (p["Overdue"] or p["Follow-up due"]),
                          -(p["Days since event"] or 0)),
        )
        if action_rows:
            st.dataframe([{
                "Employer":p["Employer"],"Role":p["Role"],
                "Action":"Review follow-up" if p["Overdue"] or p["Follow-up due"] else "Awaiting response",
                "Days since last event":p["Days since event"],
                "Next step":p["Next step"],
                "Due":p["Due"],
            } for p in action_rows[:10]],hide_index=True,width="stretch")
            st.caption("Process status is based on imported evidence, not a live employer workflow.")
        else:
            st.caption("No outstanding next step is explicitly documented.")
        st.markdown("**Pipeline health:** "
                    f"{len(active)} active documented processes, {len(waiting)} awaiting a reply, "
                    f"{len(due)} with next steps due. These categories can overlap.")
        if st.toggle("Explore response time and full follow-up history",
                     key="job_expand_followups",value=False):
            sent=[p for p in processes if p['Follow-up sent']]
            replied=sum(p['Response'] for p in sent)
            st.metric('Response to latest recorded follow-up',rate_label(replied,len(sent)))
            st.caption('One latest sent follow-up per linked process; only explicit response evidence on or after it qualifies. '
                       'Closed processes are excluded from the waiting queue but remain in the response denominator.')
            bar([{'Process':p['Employer']+' · '+p['Role'],'Days waiting':p['Waiting days']} for p in waiting if p['Waiting days'] is not None], 'Process','Days waiting',color='#b98a45')
            action_rows=[{k:p[k] for k in ['Employer','Role','Contact','Follow-up status','Waiting days','Next step','Due','Overdue','Follow-up due']} for p in processes if p['Waiting'] or p['Follow-up due'] or p['Overdue'] or p['Follow-up status']!='Unrecorded']
            st.subheader('Next actions')
            if action_rows:
                st.dataframe(action_rows,hide_index=True,width='stretch')
            else:
                st.info('No documented follow-up requirements in this scope.')    elif focus == "conversion":
        detail = st.selectbox("Performance question",
            ["funnel","targeting","pipeline"],
            format_func=lambda x:{
                "funnel":"Where do processes stop progressing?",
                "targeting":"Which role families and channels are producing engagement?",
                "pipeline":"Which processes are still active or aging?",
            }[x],key="job_performance_detail")
        if detail == "funnel":
            st.subheader('Observed application cohort')
            st.caption('Applications dated within the activity window; subsequent evidence followed through the end date. '
                       'Each process counts once. Ordered stages allow same-day evidence because exact event times are not consistently available. '
                       'Interview completion requires explicit completion/held evidence; invitations do not qualify.')
            bar(report['funnel'],'Stage','Processes',preserve_order=True)
            n = len(cohort)
            human = sum(bool(p['Human']) for p in cohort)
            interviewed = sum(bool(p['Interview']) for p in cohort)
            progressed = sum(bool(p['Progressed']) for p in cohort)
            a,b,c = st.columns(3)
            a.metric('Application → human contact',rate_label(human,n))
            b.metric('Human → completed interview',rate_label(interviewed,human))
            c.metric('Interview → explicit next stage',rate_label(progressed,interviewed))
            st.caption('Next-stage/offer reporting needs explicit stage records or reference checks. No documented progression does not establish failure. '
                       'Follow-ups are shown separately because they are not a mandatory hiring stage.')
            st.metric('Applications per human-contact process',f'{n/human:.1f}' if human else 'Unavailable')
            st.caption('A human-contact process is not automatically a qualified conversation. These observed-cohort rates do not describe all applications in the official snapshot.')
            a,b = st.columns(2)
            for column,key,title in [(a,'contact_latency','Application → first human contact'),(b,'rejection_latency','Application → dated rejection')]:
                values=report[key]
                column.metric(title, f"{values['median']} days" if values['n'] else 'Unavailable', help='Median elapsed calendar days for matched, dated processes.')
                column.caption(f"Mean: {values['mean']} days · {values['n']} matched processes" if values['n'] else 'No matched date pairs; missing dates are never replaced with zero.')
            details('Matched cohort evidence',[{k:p[k] for k in ['Employer','Role','Applied','Human','Interview','Progressed','Offered','Contact days','Rejection days']} for p in cohort])
        elif detail == "targeting":
            st.subheader('Role families with completed-interview evidence')
            reached=Counter(p['Family'] for p in processes if p['Completed interview'])
            bar([{'Family':k,'Processes':v} for k,v in reached.items()], 'Family','Processes',color='#22b8b0')
            st.caption('All matched process histories through the end date, including processes without an imported application date. The cohort comparisons below require a dated application.')
            _cohort_chart(report['family'],'Role-family outcomes')
            _cohort_chart(report['seniority'],'Seniority outcomes')
            st.caption('Family and seniority are title-based categories, not a manual assessment of mandate or job fit. Small cohorts are descriptive, not rankings of future success.')
            if any(r['Group']!='Unrecorded' for r in report['channel']):
                _cohort_chart(report['channel'],'Recorded application channels')
            else:
                st.info('ATS vs LinkedIn conversion is unavailable: application source channels are not recorded. Outlook evidence alone does not identify the application channel.')
            _cohort_chart([dict(r,Group='Recruiter involved' if r['Group']=='True' else 'No recruiter flag recorded') for r in report['recruiter']], 'Recruiter involvement')
            st.caption('Recruiter involvement may happen after application. This is not proof of a recruiter-led acquisition route.')
            engagements = defaultdict(lambda: {'Human events':0,'Processes':0})
            for p in processes:
                if p['Human events']:
                    engagements[p['Employer']]['Human events']+=p['Human events']
                    engagements[p['Employer']]['Processes']+=1
            bar([dict(Employer=k,**v) for k,v in engagements.items()], 'Employer','Human events',color='#22b8b0')
            st.caption('Repeat company engagement counts recorded human events, including outbound follow-ups; it does not imply multiple hiring teams.')
        else:
            states=Counter(p['State'] for p in processes)
            bar([{'State':k,'Processes':v} for k,v in states.items()],'State','Processes')
            aging=[{'Process':p['Employer']+' · '+p['Role'],'Days since event':p['Days since event']} for p in active if p['Days since event'] is not None]
            st.subheader('Active-process silence')
            bar(aging,'Process','Days since event',color='#b98a45')
            st.caption('Elapsed days since the last recorded event, not proof that the employer has gone silent. Imported evidence may lag.')
            details('All documented process states',[{k:p[k] for k in ['Employer','Role','State','Documented status','Status as of','Last event','Days since event','Days since application']} for p in processes])
    elif focus == "correlations":
        st.caption("Connections are automatically recalculated from full observation histories; "
                   "date and employer filters above do not restrict the cross-dataset tests.")
        relationship = st.selectbox("Relationship to examine",
            ["portfolio","market"],
            format_func=lambda x:"Portfolio behavior ↔ recruitment" if x=="portfolio"
                else "Swedish market ↔ recruitment & portfolio",
            key="job_relationship_detail")
        if relationship == "portfolio":
            render_portfolio_job_correlations()
        else:
            render_market_relationships(records)
    else:
        source = st.selectbox("Evidence view",
            ["official","trends","events"],
            format_func=lambda x:{
                "official":"Official job-search snapshot",
                "trends":"Matured cohorts and comparison method",
                "events":"Event provenance and quality",
            }[x],key="job_evidence_detail")
        if source == "official":
            _snapshot(records)
        elif source == "trends":
            render_job_search_trends(records,start,end,employer)
        else:
            q=report['quality']
            bar([{'Measure':'Canonical event records','Records':q['canonical']},
                 {'Measure':'Undated event records','Records':q['undated']},
                 {'Measure':'Unlinkable process rows through end date','Records':q['unlinked']},
                 {'Measure':'Selected rows missing source channel','Records':q['source_missing']}], 'Measure','Records')
            st.caption(f"{q['mixed_application_negative']} selected rows carry both application and negative-decision flags. Their dates are not treated as rejection dates. "
                       'Snapshot, narrative and secondary workbook representations are excluded from event counts. Logical event keys remove duplicate primary representations.')
            columns={'Date':'event_date','Employer':'employer','Role':'role','Activity':'activity','Status':'status','Date basis':'date_basis',
                     'Type':'record_type','Event key':'logical_event_key','File':'source_file','Sheet':'source_sheet','Row':'source_row'}
            audit=[{k:r.get(v) for k,v in columns.items()} for r in sorted(rows,key=lambda r:str(r.get('event_date') or ''),reverse=True)]
            details('Canonical evidence with provenance',audit)
            if audit:
                output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=list(columns));writer.writeheader()
                for row in audit:
                    writer.writerow({k: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in row.items()})
                st.download_button('Download filtered evidence CSV',output.getvalue(),'job-search-evidence.csv','text/csv')
            details('Imported methodology',[{'Method':r.get('interpretation') or r.get('activity')} for r in records if r.get('record_type')=='methodology'])    st.caption("Source records are imported; the dashboard does not scan private email "
               "or create applications by itself.")


def render_job_search_analytics(session: dict | None = None) -> None:
    """Read private job evidence using the Analytics page's shared owner session."""
    st.title('Job Search Analytics')
    if not session or not session.get('access_token'):
        st.warning('Sign in to Portfolio Analytics to view private job-search records.')
        return
    try:
        with st.spinner('Loading private job-search evidence…'):
            records = fetch_job_records(str(session['access_token']))
    except (RuntimeError, TimeoutError):
        st.error('Private job-search data could not be loaded. Your owner session may need a fresh sign-in.')
        return
    if not records:
        st.info('No accessible job-search records. Check that you are signed in as the portfolio owner.')
        return
    render_job_report(records)
