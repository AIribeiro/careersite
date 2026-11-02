from __future__ import annotations

"""Owner-only Content Studio interface for the Executive Briefing Infographic Engine."""

import json

import streamlit as st
import streamlit.components.v1 as components

from briefing_infographic_engine import (
    PATTERNS, REVIEW_KEYS, generate_infographic_spec,
    render_svg, source_fingerprint, svg_image_data, validate_spec,
)
from briefing_infographic_store import (
    approve_infographic, fetch_owner_infographic, has_approved_visual,
    reject_infographic, save_infographic_draft,
)

REVIEW_DESCRIPTIONS = {
    "factual_accuracy": "Factual integrity — visual claims agree with the briefing and sources.",
    "originality": "Originality — independent editorial architecture, not traced from the reference.",
    "anonymity": "Anonymity — no employer or identifiable client/project information.",
    "readability": "Executive scan — clear hierarchy, legible labels and precise takeaway.",
    "mobile": "Responsive preview — inspected compact-width diagram, no lost information.",
    "content_fit": "Decision value — the graphic helps the reader make the briefing's decision.",
}


def _preview_svg(spec: dict) -> None:
    desktop=svg_image_data(render_svg(spec))
    mobile=svg_image_data(render_svg(spec,mobile=True))
    st.caption("Desktop composition")
    components.html(
        '<div style="background:#e8ebea;padding:10px">'
        f'<img alt="Desktop infographic preview" src="{desktop}" '
        'style="display:block;width:100%;height:auto"></div>',
        height=460,scrolling=True
    )
    st.caption("Compact/mobile composition")
    components.html(
        '<div style="width:340px;max-width:100%;margin:auto;background:#e8ebea;padding:6px">'
        f'<img alt="Mobile infographic preview" src="{mobile}" '
        'style="display:block;width:100%;height:auto"></div>',
        height=430,scrolling=True
    )


def render_briefing_infographic_editor(article, draft, access_token: str, prefix: str) -> bool:
    """One save/preview/review/approval lifecycle; True only for current approval."""
    if draft.kind.strip().casefold()!="executive briefing":
        return True
    with st.expander("Executive Briefing · Infographic Engine",expanded=True):
        st.caption(
            "Each briefing needs one original decision graphic. This structured "
            "generator creates a reviewable SVG; it does not automatically verify "
            "facts or reproduce a reference infographic."
        )
        if not article.id:
            st.info("Save the article as a draft before generating its infographic.")
            return False

        try:
            row=fetch_owner_infographic(article.id,access_token)
        except (RuntimeError,ValueError) as exc:
            st.error(f"Could not load infographic: {exc}")
            return False

        same_source=source_fingerprint(article)==source_fingerprint(draft)
        if not same_source:
            st.warning(
                "The article text has unsaved changes. Save it as a draft, "
                "regenerate/review the graphic, then publish the updated edition."
            )

        state_key=f"{prefix}_ebi_json"
        loaded_key=f"{prefix}_ebi_loaded_revision"
        signature=(str(article.id), int(row.get("revision",0)) if row else 0)
        if st.session_state.get(loaded_key)!=signature:
            seeded=row["spec"] if row else generate_infographic_spec(article)
            st.session_state[state_key]=json.dumps(seeded,indent=2,ensure_ascii=False)
            st.session_state[f"{prefix}_ebi_alt"]=(
                row.get("alt_text","") if row else
                "Original executive decision infographic for "+article.title+
                ". It explains the evidence and responsibilities required before approval."
            )
            st.session_state[f"{prefix}_ebi_caption"]=(
                row.get("caption","") if row else
                "Original executive decision infographic by Jair Ribeiro."
            )
            st.session_state[loaded_key]=signature

        current=row.get("status") if row else "not generated"
        st.caption(
            f"Status: {current.upper()} · "
            f"Version: {row.get('revision',0) if row else 0} · "
            f"Source: {'current' if same_source else 'unsaved edits'}"
        )
        from briefing_infographic_ai import (
            configured_infographic_model, infographic_model_key,
            generate_strategic_infographic_spec,
        )
        g_ai,g_rules=st.columns(2)
        ai_requested=g_ai.button(
            "Generate strategic concept with AI",
            key=f"{prefix}_ebi_generate_ai",
            use_container_width=True,disabled=not same_source,
        )
        rules_requested=g_rules.button(
            "Generate structured fallback",
            key=f"{prefix}_ebi_generate_rules",
            use_container_width=True,disabled=not same_source,
        )
        st.caption(
            "AI concept: explicit owner request via OpenRouter · "
            + configured_infographic_model()
            + " · ZDR and data collection denied. The article text is sent to "
              "the selected provider only when clicked. Both methods require human review."
        )
        if ai_requested:
            key=infographic_model_key()
            if not key:
                st.warning("OPENROUTER_API_KEY unavailable. Use structured fallback.")
            else:
                try:
                    with st.spinner("Drafting a subject-specific visual decision model…"):
                        proposed=generate_strategic_infographic_spec(key,draft)
                    st.session_state[state_key]=json.dumps(
                        proposed,indent=2,ensure_ascii=False
                    )
                    st.info("AI-generated concept ready for editorial correction, preview and review.")
                except (RuntimeError,ValueError) as exc:
                    st.error(str(exc))
        if rules_requested:
            st.session_state[state_key]=json.dumps(
                generate_infographic_spec(draft),
                indent=2,ensure_ascii=False
            )
            st.info("Rule-based structure ready. Rewrite generic proof points before approval.")
        st.text_area(
            "Infographic strategy and proof points (JSON)",
            key=state_key,height=235,
            help="Edit the pattern, title, deck, items and executive conclusion. "
                 "Supported patterns: "+", ".join(PATTERNS),
        )
        st.text_area(
            "Accessible explanation / alt text",
            key=f"{prefix}_ebi_alt",height=100,
        )
        st.text_area(
            "Visual caption",key=f"{prefix}_ebi_caption",height=80,
        )
        candidate=None
        try:
            candidate=json.loads(st.session_state[state_key])
            validate_spec(candidate)
        except (ValueError,TypeError,KeyError) as exc:
            st.warning(f"Complete the infographic specification: {exc}")

        pcol,scol=st.columns(2)
        if pcol.button(
            "Preview desktop + mobile",key=f"{prefix}_ebi_preview",
            disabled=candidate is None,use_container_width=True
        ):
            st.session_state[f"{prefix}_ebi_show_preview"]=True
        if scol.button(
            "Save infographic draft",key=f"{prefix}_ebi_save",
            disabled=candidate is None or not same_source,use_container_width=True
        ):
            try:
                save_infographic_draft(
                    access_token,draft,candidate,
                    st.session_state[f"{prefix}_ebi_alt"],
                    st.session_state[f"{prefix}_ebi_caption"],
                )
                st.success("A versioned infographic draft has been saved. Review before approval.")
                st.rerun()
            except (RuntimeError,ValueError) as exc:
                st.error(str(exc))

        if candidate and st.session_state.get(f"{prefix}_ebi_show_preview"):
            try:
                _preview_svg(candidate)
            except (RuntimeError,ValueError,TypeError) as exc:
                st.error(f"Visual preview could not be rendered: {exc}")

        if row and row.get("editorial_note"):
            st.caption("Last review note: "+str(row["editorial_note"])[:320])
        with st.expander("Infographic readership analytics",expanded=False):
            try:
                from site_cms import _request_json, _rest_url
                from urllib.parse import quote
                query=_rest_url(
                    "careersite_briefing_infographic_analytics_v1?"
                    "select=article_view_sessions,infographic_view_sessions,"
                    "view_reach_pct,seconds_per_exposed_session,revision"
                    f"&slug=eq.{quote(article.slug,safe='')}&limit=1"
                )
                metrics=_request_json("GET",query,token=access_token)
                if isinstance(metrics,list) and metrics:
                    m=metrics[0]
                    cols=st.columns(3)
                    cols[0].metric("Visual readers",int(m.get("infographic_view_sessions") or 0))
                    cols[1].metric(
                        "Article reach",
                        str(m["view_reach_pct"])+"%" if m.get("view_reach_pct") is not None else "—"
                    )
                    cols[2].metric(
                        "Attention per reader",
                        str(m["seconds_per_exposed_session"])+"s"
                        if m.get("seconds_per_exposed_session") is not None else "—"
                    )
                    st.caption(
                        "Observed first-party section exposure and attention; "
                        "not evidence of comprehension or conversion. "
                        "Historical views before infographic deployment are in the denominator."
                    )
                else:
                    st.caption("No infographic readership records yet.")
            except (RuntimeError,ValueError,TypeError) as exc:
                st.caption("Analytics unavailable: "+str(exc)[:150])

        approved=has_approved_visual(draft,access_token) and same_source
        if approved:
            st.success("An approved infographic is current. New drafts do not remove it from the published reader.")

        if row and row.get("status")=="draft" and same_source:
            st.markdown("**Review the saved version before approval**")
            checks={}
            for name in REVIEW_KEYS:
                checks[name]=st.checkbox(
                    REVIEW_DESCRIPTIONS[name],key=f"{prefix}_ebi_review_{name}"
                )
            st.text_area(
                "Review notes / required corrections",
                key=f"{prefix}_ebi_review_note",height=100,
            )
            up_to_date = candidate==row.get("spec")
            if not up_to_date:
                st.warning("Unsaved visual changes. Save the draft again before approval.")
            c1,c2=st.columns(2)
            if c1.button(
                "Approve and insert",
                key=f"{prefix}_ebi_approve",
                disabled=not all(checks.values()) or not up_to_date,
                use_container_width=True,
            ):
                try:
                    approve_infographic(
                        access_token,draft,row,checks,
                        st.session_state.get(f"{prefix}_ebi_review_note",""),
                    )
                    st.success("Infographic approved. It will appear in this briefing once published.")
                    st.rerun()
                except (RuntimeError,ValueError) as exc:
                    st.error(str(exc))
            if c2.button("Reject visual",key=f"{prefix}_ebi_reject",use_container_width=True):
                try:
                    reject_infographic(
                        access_token,row,
                        st.session_state.get(f"{prefix}_ebi_review_note",""),
                    )
                    st.rerun()
                except (RuntimeError,ValueError) as exc:
                    st.error(str(exc))
        else:
            st.caption("Publishing requires an approved, current infographic. "
                       "No graphics are auto-approved when generated.")
        return approved
