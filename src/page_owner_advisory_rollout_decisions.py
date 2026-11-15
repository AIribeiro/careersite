"""Owner-only Rollout Advisory decision register.

The owner token already passed the Advisory management access check. This
module reads the existing RLS-protected assessment table and never edits client
assessments, grants entitlements, or infers customer satisfaction from QA data.
"""
from __future__ import annotations

from urllib.parse import quote

import streamlit as st
from site_cms import _rest_url, _request_json


def _owner_rollout_history(token:str)->list[dict]:
    rows=_request_json(
        "GET",_rest_url("portfolio_advisory_rollout_assessments?"
                        "select=id,user_id,request_id,created_at,answers,model_version"
                        "&order=created_at.desc&limit=150"),
        token=token,timeout=16,
    )
    if not isinstance(rows,list):
        raise RuntimeError("Could not read private rollout decision records")
    return [r for r in rows if isinstance(r,dict)]


def render_owner_rollout_decisions(token:str, people:list[dict],
                                    access:dict[str,list[dict]])->None:
    from page_advisory_rollout import assess
    from page_rollout_premium_pdf import build_action_plan
    st.subheader("Enterprise AI Rollout · Decision register")
    st.caption("Read-only management of client assessments, decisions, release gates "
               "and historical results. Permissions remain managed in Access & invitations.")
    try:
        records=_owner_rollout_history(token)
    except (RuntimeError,ValueError,TimeoutError,KeyError):
        st.error("Rollout decision history is unavailable.")
        return
    active=sum(r.get("status")=="active" for r in access.get("rollout",[]))
    real=[]
    demo=[]
    for record in records:
        try:
            outcome=assess(record["answers"])
        except (KeyError,ValueError,TypeError):
            continue
        row=(record,outcome)
        mark=record["answers"].get("demo")
        (demo if isinstance(mark,dict) and mark.get("is_demo") else real).append(row)
    a,b,c,d=st.columns(4)
    a.metric("Approved entitlements",active)
    b.metric("Client decisions",len(real))
    c.metric("Decisions requiring pause",sum(r["label"]=="PAUSE SCALING" for _,r in real))
    d.metric("Synthetic owner tests",len(demo))
    st.caption("The client metrics exclude synthetic QA assessments.")
    show_demo=st.checkbox("Include synthetic owner tests in the history table",
                          value=True,key="owner_rollout_include_demo")
    candidates=real+(demo if show_demo else [])
    candidates.sort(key=lambda item:str(item[0].get("created_at") or ""),reverse=True)
    if not candidates:
        st.info("No qualifying rollout assessments match this view.")
        return
    profiles={str(p.get("user_id") or ""):p for p in people}
    name=lambda uid:(" ".join(filter(None,[
        str(profiles.get(uid,{}).get("first_name") or ""),
        str(profiles.get(uid,{}).get("last_name") or ""),
    ])).strip() or str(profiles.get(uid,{}).get("email") or "Unknown client"))
    display=[]
    for rec,result in candidates:
        uid=str(rec.get("user_id") or "")
        ctx=rec["answers"].get("context") or {}
        example=rec["answers"].get("demo") or {}
        display.append({
            "Date":str(rec.get("created_at") or "")[:10],
            "Client":name(uid),
            "Initiative":str(ctx.get("use_case") or "Unnamed"),
            "Verdict":result["label"].replace("_"," ").title(),
            "Readiness":result["overall"],
            "Critical gates":len(result["critical_gates"]),
            "Evidence":result["confidence"],
            "Record type":"Owner test" if isinstance(example,dict) and example.get("is_demo") else "Client",
        })
    st.dataframe(display,hide_index=True,use_container_width=True,height=min(450,110+len(display)*32))
    records_by_id={str(r["id"]):(r,v) for r,v in candidates}
    chosen=st.selectbox(
        "Inspect a saved decision",list(records_by_id),
        format_func=lambda rid:(
            str(records_by_id[rid][0].get("created_at") or "")[:10]+" · "+
            str((records_by_id[rid][0]["answers"].get("context") or {}).get("use_case") or "AI rollout")+
            " · "+records_by_id[rid][1]["label"].replace("_"," ").title()
        ),
        key="owner_rollout_record",
    )
    rec,verdict=records_by_id[chosen]
    ctx=rec["answers"]["context"]
    st.markdown("#### Decision review")
    st.caption(name(str(rec.get("user_id") or ""))+" · "+
               str(rec.get("created_at") or "")[:10]+" · "+
               str(ctx.get("stage") or ""))
    st.markdown("**"+verdict["label"].replace("_"," ").title()+"**")
    st.write(verdict["verdict"])
    columns=st.columns(3)
    columns[0].metric("Readiness index",str(verdict["overall"])+"/100")
    columns[1].metric("Critical gates",len(verdict["critical_gates"]))
    columns[2].metric("Evidence confidence",verdict["confidence"])
    st.markdown("**Recommended executive actions**")
    for item in build_action_plan(rec["answers"],verdict):
        with st.expander(str(item["number"])+". "+item["title"]):
            st.write("Proposed owner: "+item["owner"]+" · Suggested timing: "+item["due"])
            st.write("Action: "+item["action"])
            st.write("Acceptance evidence: "+item["evidence"])
            st.write("Decision condition: "+item["condition"])
    st.caption("These records do not authorize deployment. To grant or revoke "
               "the service, use Access & invitations.")
