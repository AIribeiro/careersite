"""Private, individually approved AI Portfolio Scorecard.

Uses the existing verified Advisory session. All workspace data is stored in
Supabase under row-level policies and an audited, revision-checked save RPC.
This module never uses a service-role key or an email-address-only gate.
"""
from __future__ import annotations

from copy import deepcopy
from csv import DictWriter
from io import StringIO
from urllib.parse import quote
from uuid import uuid4

import streamlit as st

from site_cms import _request_json, _rest_url

CRITERIA = (
    ("Strategic fit", "Named priority, accountable sponsor and enterprise objective"),
    ("Business value", "Attributable baseline, credible outcomes and cost"),
    ("Feasibility", "Technical, process and operational feasibility"),
    ("Capacity / opportunity cost", "People, funds and displaced priorities"),
    ("Data readiness", "Ownership, quality, access and provenance"),
    ("Adoption / ownership", "Process owner, changed work and evidence of adoption"),
    ("Risk / control readiness", "Assessments, oversight and proportionate safeguards"),
)
WEIGHTS = (15, 20, 15, 15, 15, 10, 10)
STAGES = ("Idea", "Discovery", "Pilot", "Scale review", "Operational")
GATES = ("Not checked", "Pass", "Review", "Block")
EVIDENCE = ("Not assessed", "Low", "Medium", "High")
DECISIONS = ("Unreviewed", "Proceed", "Test", "Hold", "Stop")
MAX_INITIATIVES = 30


def default_settings() -> dict:
    return {"weights": list(WEIGHTS), "advance": 78, "test": 62,
            "capacity_fte_months": 12.0, "budget_sek": 1200000.0}


def new_initiative() -> dict:
    return {
        "id": str(uuid4()), "name": "", "sponsor": "", "owner": "", "stage": "Idea",
        "scores": [0] * 7, "evidence": "Not assessed", "gate": "Not checked",
        "fte_months": 0.0, "investment_sek": 0.0, "gross_benefit_sek": 0.0,
        "run_cost_sek": 0.0, "selected": False, "sponsor_signed": False,
        "capacity_signed": False, "evidence_ref": "", "next_proof": "",
        "decision": "Unreviewed", "decision_rationale": "", "alternatives": "",
        "control_conditions": "", "decision_owner": "", "next_review": "",
    }


def normalize(payload: object) -> dict:
    raw = payload if isinstance(payload, dict) else {}
    opts = raw.get("settings") if isinstance(raw.get("settings"), dict) else {}
    weights = opts.get("weights")
    if not isinstance(weights, list) or len(weights) != 7:
        weights = list(WEIGHTS)
    try:
        weights = [int(n) for n in weights]
        if min(weights) < 0 or max(weights) > 100 or sum(weights) != 100:
            weights = list(WEIGHTS)
    except (ValueError, TypeError):
        weights = list(WEIGHTS)
    defaults = default_settings()
    defaults["weights"] = weights
    for key in ("advance", "test", "capacity_fte_months", "budget_sek"):
        try:
            val = float(opts.get(key, defaults[key]))
            defaults[key] = max(0.0, min(val, 10**10))
        except (ValueError, TypeError):
            pass
    source = raw.get("initiatives")
    valid = []
    for item in (source if isinstance(source, list) else [])[:MAX_INITIATIVES]:
        if not isinstance(item, dict):
            continue
        row = new_initiative()
        row.update({k: v for k, v in item.items() if k in row})
        scores = row.get("scores")
        if not isinstance(scores, list) or len(scores) != 7:
            scores = [0] * 7
        row["scores"] = [
            int(v) if isinstance(v, (int, float)) and 0 <= v <= 5 else 0
            for v in scores
        ]
        row["id"] = str(row["id"])[:60]
        valid.append(row)
    return {"settings": defaults, "initiatives": valid}


def evaluation(row: dict, settings: dict) -> tuple[int | None, str]:
    scores = row.get("scores") or []
    if not str(row.get("name") or "").strip():
        return None, "NAME REQUIRED"
    if not str(row.get("owner") or "").strip():
        return None, "OWNER REQUIRED"
    if len(scores) != 7 or any(not isinstance(s, int) or s < 1 or s > 5 for s in scores):
        return None, "NOT SCORED"
    value = sum(a * b for a, b in zip(scores, settings["weights"])) / 5.0
    score = int(value + 0.5)
    if row.get("evidence") in ("Not assessed", None, ""):
        return score, "EVIDENCE NEEDED"
    if row.get("gate") == "Block":
        return score, "STOP / REDESIGN"
    if row.get("gate") != "Pass":
        return score, "CONTROL REVIEW"
    if row.get("evidence") == "Low":
        return score, "VALIDATE EVIDENCE"
    if score >= float(settings["advance"]):
        return score, "ADVANCE TO CASE"
    if score >= float(settings["test"]):
        return score, "TEST / PROVE"
    return score, "DEFER / STOP"


def capacity_summary(rows: list[dict], settings: dict) -> dict:
    chosen = [r for r in rows if r.get("selected")]
    total_fte = sum(float(r.get("fte_months") or 0) for r in chosen)
    investment = sum(float(r.get("investment_sek") or 0) for r in chosen)
    net = sum(float(r.get("gross_benefit_sek") or 0)
              - float(r.get("run_cost_sek") or 0) for r in chosen)
    blocked = sum(
        1 for r in chosen
        if r.get("gate") != "Pass" or evaluation(r, settings)[1] != "ADVANCE TO CASE"
    )
    unsigned = sum(
        int(not bool(r.get("sponsor_signed")))
        + int(not bool(r.get("capacity_signed"))) for r in chosen
    )
    return {"selected": len(chosen), "fte": total_fte,
            "fte_headroom": float(settings["capacity_fte_months"]) - total_fte,
            "investment": investment,
            "budget_headroom": float(settings["budget_sek"]) - investment,
            "annual_net": net, "blocked": blocked, "unsigned": unsigned}


def _read_workspaces(token: str, uid: str) -> list[dict]:
    rows = _request_json(
        "GET",
        _rest_url("portfolio_advisory_scorecards?select=id,request_id,user_id,status,"
                  "payload,revision,approved_at,updated_at"
                  "&user_id=eq." + quote(uid, safe="") + "&order=approved_at.desc&limit=20"),
        token=token, timeout=14,
    )
    if not isinstance(rows, list):
        raise RuntimeError("Unable to verify approved workspaces")
    return rows


def _save(token: str, workspace: dict, payload: dict) -> int:
    normalized = normalize(payload)
    returned = _request_json(
        "POST", _rest_url("rpc/portfolio_advisory_scorecard_save_v1"),
        token=token, timeout=18,
        payload={"p_id": str(workspace["id"]), "p_payload": normalized,
                 "p_expected_revision": int(workspace["revision"])},
    )
    if not isinstance(returned, dict) or str(returned.get("id")) != str(workspace["id"]):
        raise RuntimeError("Save not confirmed")
    return int(returned["revision"])


def _commit(token: str, workspace: dict, payload: dict, message: str = "Saved.") -> None:
    try:
        _save(token, workspace, payload)
        st.success(message)
        st.rerun()
    except (RuntimeError, TimeoutError, ValueError, KeyError):
        st.error("Save failed or the workspace changed elsewhere. Reload your Advisory account "
                 "and confirm access before editing again. No changes were confirmed.")


def _summary_table(rows: list[dict], settings: dict) -> list[dict]:
    result = []
    for item in rows:
        score, action = evaluation(item, settings)
        result.append({
            "Initiative": str(item.get("name") or "Untitled initiative"),
            "Sponsor": str(item.get("sponsor") or "—"),
            "Owner": str(item.get("owner") or "—"),
            "Score /100": score, "Control gate": str(item.get("gate") or ""),
            "Evidence": str(item.get("evidence") or ""),
            "Suggested action": action,
            "Proposed?": "Yes" if item.get("selected") else "No",
            "Executive decision": str(item.get("decision") or "Unreviewed"),
        })
    return sorted(result, key=lambda r: (r["Score /100"] is None,
                  -(r["Score /100"] or 0)))


def _export_csv(payload: dict) -> bytes:
    out = StringIO()
    columns = ["Initiative", "Sponsor", "Owner", "Score /100", "Control gate",
               "Evidence", "Suggested action", "Proposed?", "Executive decision"]
    writer = DictWriter(out, fieldnames=columns)
    writer.writeheader()
    writer.writerows(_summary_table(payload["initiatives"], payload["settings"]))
    return out.getvalue().encode("utf-8-sig")


def _overview(data: dict) -> None:
    rows, settings = data["initiatives"], data["settings"]
    counts = capacity_summary(rows, settings)
    a, b, c = st.columns(3)
    a.metric("Initiatives", len(rows))
    b.metric("Proposed selection", counts["selected"])
    c.metric("Unresolved gates in selection", counts["blocked"])
    a, b, c = st.columns(3)
    a.metric("Capacity headroom", f'{counts["fte_headroom"]:.1f} FTE-months')
    b.metric("Budget headroom", f'{counts["budget_headroom"]:,.0f} SEK')
    c.metric("Annual net benefit (indicative)", f'{counts["annual_net"]:,.0f} SEK')
    if counts["fte_headroom"] < 0 or counts["budget_headroom"] < 0:
        st.error("Your proposed selection exceeds the available planning envelope.")
    if counts["blocked"] or counts["unsigned"]:
        st.warning("Selected initiatives have unresolved gates or approvals. "
                   "The proposal is not a funded or authorized portfolio.")
    if rows:
        st.dataframe(_summary_table(rows, settings), hide_index=True,
                     use_container_width=True)
        st.download_button("Export summary (CSV)", data=_export_csv(data),
                           file_name="ai-portfolio-scorecard-summary.csv",
                           mime="text/csv", use_container_width=False)
    else:
        st.info("Your private scorecard is empty. Add an initiative to begin.")


def _form_initiative(token: str, workspace: dict, data: dict) -> None:
    rows = data["initiatives"]
    if st.button("Add an initiative", disabled=len(rows) >= MAX_INITIATIVES,
                 key="scorecard_add_" + str(workspace["id"])):
        clone = deepcopy(data)
        clone["initiatives"].append(new_initiative())
        _commit(token, workspace, clone, "Initiative added.")
    st.caption(f"{len(rows)}/{MAX_INITIATIVES} initiatives. Enter only high-level, "
               "non-confidential portfolio information.")
    if not rows:
        return
    chosen_id = st.selectbox("Initiative to edit", [str(x["id"]) for x in rows],
                             format_func=lambda rid: next(
                                 (str(x.get("name") or "New initiative") for x in rows
                                  if str(x["id"]) == rid), rid),
                             key="scorecard_selected_" + str(workspace["id"]))
    idx = next((n for n, x in enumerate(rows) if str(x["id"]) == chosen_id), None)
    if idx is None:
        return
    row = rows[idx]
    st.markdown("#### Business decision and evidence")
    with st.form("scorecard_edit_" + chosen_id):
        name = st.text_input("Initiative name *", value=str(row.get("name") or ""),
                             max_chars=180)
        a,b = st.columns(2)
        with a:
            sponsor = st.text_input("Executive sponsor",value=str(row.get("sponsor") or ""), max_chars=160)
            stage = st.selectbox("Lifecycle stage", STAGES,
                                 index=STAGES.index(row.get("stage")) if row.get("stage") in STAGES else 0)
        with b:
            owner = st.text_input("Accountable business owner *",value=str(row.get("owner") or ""),max_chars=160)
            evidence = st.selectbox("Evidence confidence",EVIDENCE,
                                   index=EVIDENCE.index(row.get("evidence")) if row.get("evidence") in EVIDENCE else 0)
        gate = st.selectbox("Independent control gate",GATES,
                           index=GATES.index(row.get("gate")) if row.get("gate") in GATES else 0)
        st.caption("The control gate is separate from the numeric score. "
                   "'Pass' means an appropriate review has been recorded, not that the scorecard approved the use.")
        scores = []
        for i,(title,detail) in enumerate(CRITERIA):
            old = row["scores"][i]
            score = st.select_slider(f"{i+1}. {title}",options=[0,1,2,3,4,5],
                                     value=old if old in range(6) else 0,
                                     help=detail + " · 0 means not scored.")
            scores.append(int(score))
        evidence_ref = st.text_input("Evidence reference (short citation or URL)",
                                     value=str(row.get("evidence_ref") or ""),max_chars=400)
        next_proof = st.text_area("Evidence gap / next proof", value=str(row.get("next_proof") or ""),
                                  max_chars=1200,height=84)
        st.markdown("#### Resource and value estimates")
        a,b=st.columns(2)
        with a:
            fte=st.number_input("Required capacity (FTE-months)",0.0,10000.0,
                                float(row.get("fte_months") or 0),0.5)
            investment=st.number_input("One-time investment (SEK)",0.0,1e10,
                                       float(row.get("investment_sek") or 0),10000.0)
        with b:
            gross=st.number_input("Annual gross benefit (SEK)",0.0,1e10,
                                  float(row.get("gross_benefit_sek") or 0),10000.0)
            run_cost=st.number_input("Annual recurring cost (SEK)",0.0,1e10,
                                    float(row.get("run_cost_sek") or 0),10000.0)
        selected=st.checkbox("Include in proposed portfolio (not funding approval)",
                             value=bool(row.get("selected")))
        c,d=st.columns(2)
        with c:
            sponsor_signed=st.checkbox("Sponsor sign-off recorded",value=bool(row.get("sponsor_signed")))
        with d:
            capacity_signed=st.checkbox("Capacity sign-off recorded",value=bool(row.get("capacity_signed")))
        submitted=st.form_submit_button("Save initiative",type="primary")
    if submitted:
        if len(name.strip())<3:
            st.error("Provide an initiative name of at least three characters.")
        elif not owner.strip():
            st.error("Identify an accountable business owner.")
        else:
            next_data=deepcopy(data)
            next_data["initiatives"][idx].update({
                "name":name.strip(),"sponsor":sponsor.strip(),"owner":owner.strip(),
                "stage":stage,"evidence":evidence,"gate":gate,"scores":scores,
                "evidence_ref":evidence_ref.strip(),"next_proof":next_proof.strip(),
                "fte_months":float(fte),"investment_sek":float(investment),
                "gross_benefit_sek":float(gross),"run_cost_sek":float(run_cost),
                "selected":selected,"sponsor_signed":sponsor_signed,
                "capacity_signed":capacity_signed,
            })
            _commit(token,workspace,next_data,"Initiative saved.")
    with st.expander("Remove this initiative"):
        acknowledged=st.checkbox("Confirm removal of this initiative and its decision record",
                                 key="scorecard_del_ack_"+chosen_id)
        if st.button("Remove initiative",disabled=not acknowledged,
                     key="scorecard_del_"+chosen_id):
            next_data=deepcopy(data)
            next_data["initiatives"].pop(idx)
            _commit(token,workspace,next_data,"Initiative removed.")


def _capacity(data: dict) -> None:
    settings=data["settings"]
    rows=data["initiatives"]
    chosen=[r for r in rows if r.get("selected")]
    if not chosen:
        st.info("Select initiatives in the editor to compare the proposed portfolio.")
        return
    table=[]
    for r in chosen:
        gross=float(r.get("gross_benefit_sek") or 0)
        cost=float(r.get("run_cost_sek") or 0)
        net=gross-cost
        investment=float(r.get("investment_sek") or 0)
        score,action=evaluation(r,settings)
        table.append({
            "Initiative":str(r.get("name") or "Untitled"),
            "FTE-months":float(r.get("fte_months") or 0),
            "Investment SEK":investment,
            "Annual net SEK":net,
            "Payback months":round(12*investment/net,1) if net>0 else None,
            "Score":score,"Gate":r.get("gate"),"Suggested action":action,
            "Sponsor signed":bool(r.get("sponsor_signed")),
            "Capacity signed":bool(r.get("capacity_signed")),
        })
    st.dataframe(table,use_container_width=True,hide_index=True)
    st.caption("Annual net = annual gross benefit minus recurring cost. Simple payback = "
               "12 × one-time investment / annual net; excludes ramp-up, uncertainty, "
               "discounting and indirect costs. Financial values are input estimates.")
    if capacity_summary(rows,settings)["blocked"]:
        st.warning("A proposed initiative has not met its control, evidence or scoring conditions. "
                   "A high ranking is never permission to proceed.")


def _decision_record(token: str,workspace: dict,data: dict) -> None:
    rows=data["initiatives"]
    if not rows:
        st.info("Add an initiative before recording a leadership decision.")
        return
    chosen=st.selectbox("Decision record for",[str(i["id"]) for i in rows],
                        format_func=lambda rid:next(
                            (str(i.get("name") or "New initiative") for i in rows
                            if str(i["id"])==rid),rid),
                        key="scorecard_decision_"+str(workspace["id"]))
    idx=next((j for j,x in enumerate(rows) if str(x["id"])==chosen),None)
    if idx is None:
        return
    item=rows[idx]
    st.caption("The record captures an executive judgment; it is not itself an authorization.")
    with st.form("scorecard_record_"+chosen):
        decision=st.selectbox("Executive decision",DECISIONS,
                              index=DECISIONS.index(item.get("decision")) if item.get("decision") in DECISIONS else 0)
        rationale=st.text_area("Rationale, baseline and cost of doing nothing",
                               value=str(item.get("decision_rationale") or ""),max_chars=2500,height=130)
        alternatives=st.text_area("Alternatives and opportunity cost (including non-AI changes)",
                                  value=str(item.get("alternatives") or ""),max_chars=2000,height=110)
        conditions=st.text_area("Conditions, human oversight and no-go limits",
                                value=str(item.get("control_conditions") or ""),max_chars=2000,height=110)
        a,b=st.columns(2)
        with a:
            owner=st.text_input("Decision authority / approval owner",
                                value=str(item.get("decision_owner") or ""),max_chars=180)
        with b:
            day=st.text_input("Next review date (YYYY-MM-DD)",
                              value=str(item.get("next_review") or ""),max_chars=10)
        next_proof=st.text_area("What must be proved next / responsible person / deadline",
                                value=str(item.get("next_proof") or ""),max_chars=1200,height=95)
        saved=st.form_submit_button("Save decision record",type="primary")
    if saved:
        next_data=deepcopy(data)
        next_data["initiatives"][idx].update({
            "decision":decision,"decision_rationale":rationale.strip(),
            "alternatives":alternatives.strip(),"control_conditions":conditions.strip(),
            "decision_owner":owner.strip(),"next_review":day.strip(),
            "next_proof":next_proof.strip()
        })
        _commit(token,workspace,next_data,"Decision record saved.")


def _policy(token: str,workspace: dict,data: dict) -> None:
    s=data["settings"]
    st.caption("Defaults are proposed judgments, not external benchmarks. "
               "Weights must add to 100%. Changes affect all scores in your workspace.")
    with st.form("scorecard_settings_"+str(workspace["id"])):
        weights=[]
        for i,(name,desc) in enumerate(CRITERIA):
            weights.append(st.number_input(name+" weight %",min_value=0,max_value=100,
                                            value=int(s["weights"][i]),step=5,
                                            help=desc))
        st.write(f'Current total weight: **{sum(weights)}%**')
        a,b=st.columns(2)
        with a:
            advance=st.number_input("Advance to business case at score",0,100,int(s["advance"]))
            available=st.number_input("Available FTE-months",0.0,10000.0,
                                      float(s["capacity_fte_months"]),1.0)
        with b:
            test=st.number_input("Test/prove at score",0,100,int(s["test"]))
            budget=st.number_input("Planning budget SEK",0.0,1e10,
                                   float(s["budget_sek"]),10000.0)
        saved=st.form_submit_button("Save decision policy",type="primary")
    if saved:
        if sum(weights)!=100 or test>=advance:
            st.error("Weights must total 100%, and the test threshold must be below the advance threshold.")
            return
        next_data=deepcopy(data)
        next_data["settings"].update({
            "weights":[int(x) for x in weights],
            "advance":int(advance),"test":int(test),
            "capacity_fte_months":float(available),"budget_sek":float(budget)
        })
        _commit(token,workspace,next_data,"Decision policy saved.")
    st.markdown("#### Scoring anchors")
    st.write("**1** — weak or unsupported; **3** — plausible but incomplete; "
             "**5** — demonstrated and ready. Use scores 2 and 4 between anchors.")
    for name,desc in CRITERIA:
        st.markdown("**"+name+"** — "+desc)
    st.warning("Stop / hold decisions and all regulatory, privacy, security and "
               "operating controls must be assessed independently of the score.")


def render_private_scorecard(session: dict,user: dict) -> None:
    """Render only on the existing password-authenticated advisory-account page."""
    token=str(session.get("access_token") or "")
    uid=str(user.get("id") or "")
    if not token or not uid or not user.get("email_confirmed_at"):
        return
    st.markdown("## AI Portfolio Prioritization Scorecard")
    st.caption("On-demand Advisory service · Individual pro-bono approval · Private workspace")
    try:
        workspaces=_read_workspaces(token,uid)
    except (ValueError,RuntimeError,TimeoutError,KeyError):
        st.error("Could not verify Scorecard access. Retry from your Advisory account.")
        return
    if not workspaces:
        st.info("The Scorecard is available only after an Advisory engagement is "
                "approved and this service is explicitly enabled for your account. "
                "A registered account alone does not include access.")
        st.page_link("https://jairribeiro.com/?page=advisory-scorecard",
                     label="About the on-demand Scorecard service")
        return
    selected_id=st.selectbox("Approved workspace",
                              [str(x["id"]) for x in workspaces],
                              format_func=lambda val:"Approved engagement · "+
                                next((str(x.get("approved_at") or "")[:10]
                                      for x in workspaces if str(x["id"])==val),""),
                              key="scorecard_workspace_choice")
    workspace=next((x for x in workspaces if str(x["id"])==selected_id),None)
    if not workspace:
        return
    data=normalize(workspace.get("payload"))
    st.caption("Last saved: "+str(workspace.get("updated_at") or "")[:16].replace("T"," ") +
               " · Revision "+str(workspace.get("revision") or 0))
    st.warning("Use high-level, non-confidential business information only. "
               "A score never authorizes funding, regulated processing or deployment.")
    overview, initiatives, capacity, record, policy=st.tabs([
        "Portfolio overview","Initiatives","Capacity & value","Decision record","Policy & criteria"
    ])
    with overview:
        _overview(data)
    with initiatives:
        _form_initiative(token,workspace,data)
    with capacity:
        _capacity(data)
    with record:
        _decision_record(token,workspace,data)
    with policy:
        _policy(token,workspace,data)
