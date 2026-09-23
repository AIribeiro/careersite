from __future__ import annotations

from dataclasses import replace
import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components
from streamlit_quill import st_quill

from site_cms import (
    OWNER_EMAIL,
    CmsArticle,
    admin_list_articles,
    article_url,
    change_article_status,
    delete_article,
    delete_header_image,
    duplicate_article,
    ensure_owner_session,
    generate_metadata,
    owner_signin,
    owner_signup,
    save_article,
    sanitize_article_html,
    slugify,
    strip_html,
    upload_header_image,
)


def _noindex() -> None:
    components.html(
        """
<script>
(() => {
  const doc = window.parent.document;
  let robots = doc.head.querySelector('meta[name="robots"]');
  if (!robots) {
    robots = doc.createElement('meta');
    robots.setAttribute('name', 'robots');
    doc.head.appendChild(robots);
  }
  robots.setAttribute('content', 'noindex,nofollow,noarchive');
  doc.title = 'Article CMS | Jair Ribeiro';
})();
</script>
""",
        height=0,
        width=0,
    )


def _css() -> None:
    st.markdown(
        """
<style>
.block-container{max-width:1420px;padding-top:1.4rem;padding-bottom:4rem}
[data-testid="stHeader"]{background:rgba(244,240,232,.92)}
.cms-hero{padding:22px 26px;margin:0 0 20px;border:1px solid #ddd4c7;background:linear-gradient(145deg,#fffdfa,#f1e9de)}
.cms-kicker{color:#c56f3d;font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.cms-hero h1{margin:.3rem 0 .45rem;font:500 clamp(2rem,4vw,3.4rem)/1.02 Georgia,serif;color:#10131a}
.cms-hero p{max-width:850px;margin:0;color:#6f6a62;line-height:1.65}
.cms-card{padding:18px 20px;margin:0 0 12px;border:1px solid #ddd4c7;background:#fffdfa}
.cms-card h3{margin:.1rem 0 .45rem;font:500 1.35rem/1.18 Georgia,serif;color:#10131a}
.cms-card p{margin:.2rem 0;color:#6f6a62;font-size:.88rem}
.cms-status{display:inline-flex;padding:4px 8px;border:1px solid #ddd4c7;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
.cms-status-published{color:#315a43;border-color:#a7c3b1;background:#f2f8f4}
.cms-status-draft{color:#8b5c2f;border-color:#d9b38d;background:#fff7ef}
.cms-meta{font-size:.74rem;color:#777}
.cms-panel{padding:20px;border:1px solid #ddd4c7;background:#fffdfa}
.cms-panel-title{margin:0 0 14px;font:500 1.35rem/1.2 Georgia,serif}
.cms-help{font-size:.78rem;color:#6f6a62;line-height:1.55}
.cms-image{display:block;width:100%;max-height:420px;object-fit:cover;border:1px solid #ddd4c7;margin:8px 0 14px}
.cms-divider{height:1px;background:#ddd4c7;margin:20px 0}
.stButton>button,.stDownloadButton>button{border-radius:0!important}
[data-testid="stForm"]{border-radius:0!important}
</style>
""",
        unsafe_allow_html=True,
    )


def _session() -> dict | None:
    session = ensure_owner_session(st.session_state.get("cms_auth"))
    if session:
        st.session_state["cms_auth"] = session
    else:
        st.session_state.pop("cms_auth", None)
    return session


def _login() -> None:
    st.markdown(
        f"""
<div class="cms-hero">
  <div class="cms-kicker">Private authoring</div>
  <h1>Portfolio article CMS</h1>
  <p>Owner access only. Sign in with <strong>{html.escape(OWNER_EMAIL)}</strong> to publish and maintain Thinking articles.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    sign_in, setup = st.tabs(["Sign in", "First-time setup"])

    with sign_in:
        with st.form("cms_signin"):
            st.text_input("Email", value=OWNER_EMAIL, disabled=True)
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            try:
                st.session_state["cms_auth"] = owner_signin(password)
                st.success("Signed in.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with setup:
        st.caption("Use this once to create the owner account. Supabase may send a verification email before the first sign-in.")
        with st.form("cms_signup"):
            st.text_input("Owner email", value=OWNER_EMAIL, disabled=True, key="setup_email")
            password = st.text_input("Choose password", type="password", help="At least 12 characters.")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create owner account")
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = owner_signup(password)
                    if result.get("access_token"):
                        st.session_state["cms_auth"] = result
                        st.success("Owner account created and signed in.")
                        st.rerun()
                    else:
                        st.success("Account created. Check your email for the Supabase verification link, then return here and sign in.")
                except Exception as exc:
                    st.error(str(exc))


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in re.split(r"[,\n]+", value or "") if item.strip())


def _article_from_state(base: CmsArticle, prefix: str) -> CmsArticle:
    return replace(
        base,
        title=st.session_state.get(f"{prefix}_title", ""),
        subtitle=st.session_state.get(f"{prefix}_subtitle", ""),
        slug=st.session_state.get(f"{prefix}_slug", ""),
        content_html=sanitize_article_html(st.session_state.get(f"{prefix}_body", "")),
        aside_html=sanitize_article_html(st.session_state.get(f"{prefix}_aside", "")),
        excerpt=st.session_state.get(f"{prefix}_excerpt", ""),
        header_image_url=st.session_state.get(f"{prefix}_image_url", ""),
        header_image_alt=st.session_state.get(f"{prefix}_image_alt", ""),
        seo_title=st.session_state.get(f"{prefix}_seo_title", ""),
        meta_description=st.session_state.get(f"{prefix}_meta_description", ""),
        keywords=_split_csv(st.session_state.get(f"{prefix}_keywords", "")),
        hashtags=_split_csv(st.session_state.get(f"{prefix}_hashtags", "")),
        category=st.session_state.get(f"{prefix}_category", ""),
        kind=st.session_state.get(f"{prefix}_kind", "Article"),
        source_url=st.session_state.get(f"{prefix}_source_url", ""),
        featured=bool(st.session_state.get(f"{prefix}_featured", False)),
        show_tags_publicly=bool(st.session_state.get(f"{prefix}_show_tags", False)),
        read_minutes=int(st.session_state.get(f"{prefix}_read_minutes", 1) or 1),
        social_title=st.session_state.get(f"{prefix}_social_title", ""),
        social_description=st.session_state.get(f"{prefix}_social_description", ""),
    )


def _load_editor_state(article: CmsArticle, prefix: str) -> None:
    values = {
        "title": article.title,
        "subtitle": article.subtitle,
        "slug": article.slug,
        "body": article.content_html,
        "aside": article.aside_html,
        "excerpt": article.excerpt,
        "image_url": article.header_image_url,
        "image_alt": article.header_image_alt,
        "seo_title": article.seo_title,
        "meta_description": article.meta_description,
        "keywords": ", ".join(article.keywords),
        "hashtags": ", ".join(article.hashtags),
        "category": article.category,
        "kind": article.kind,
        "source_url": article.source_url,
        "featured": article.featured,
        "show_tags": article.show_tags_publicly,
        "read_minutes": article.read_minutes,
        "social_title": article.social_title,
        "social_description": article.social_description,
    }
    for name, value in values.items():
        key = f"{prefix}_{name}"
        if key not in st.session_state:
            st.session_state[key] = value


def _metadata(article: CmsArticle, prefix: str, force: bool = False) -> None:
    generated = generate_metadata(
        st.session_state.get(f"{prefix}_title", article.title),
        st.session_state.get(f"{prefix}_body", article.content_html),
        st.session_state.get(f"{prefix}_subtitle", article.subtitle),
        bool(st.session_state.get(f"{prefix}_image_url", article.header_image_url)),
    )
    mappings = {
        "slug": "slug",
        "seo_title": "seo_title",
        "meta_description": "meta_description",
        "excerpt": "excerpt",
        "category": "category",
        "social_title": "social_title",
        "social_description": "social_description",
        "header_image_alt": "image_alt",
        "read_minutes": "read_minutes",
    }
    for source, target in mappings.items():
        key = f"{prefix}_{target}"
        if force or not st.session_state.get(key):
            st.session_state[key] = generated[source]
    if force or not st.session_state.get(f"{prefix}_keywords"):
        st.session_state[f"{prefix}_keywords"] = ", ".join(generated["keywords"])
    if force or not st.session_state.get(f"{prefix}_hashtags"):
        st.session_state[f"{prefix}_hashtags"] = ", ".join(generated["hashtags"])


def _copy_button(label: str, text: str, key: str) -> None:
    safe = json.dumps(text)
    components.html(
        f"""
<button id="{key}" style="padding:9px 12px;border:1px solid #b9afa2;background:#fffdfa;cursor:pointer;font:700 12px system-ui">{html.escape(label)}</button>
<script>
document.getElementById({json.dumps(key)}).addEventListener('click', async () => {{
  try {{ await navigator.clipboard.writeText({safe}); }} catch (_) {{}}
}});
</script>
""",
        height=42,
    )


def _preview(article: CmsArticle) -> None:
    if not article.title or not strip_html(article.content_html):
        st.warning("Add a title and article body before previewing.")
        return
    from site_cms import render_cms_article

    with st.expander("Preview", expanded=True):
        st.components.v1.html(
            "<style>body{margin:0;background:#f4f0e8;font-family:Arial,sans-serif}</style>" + render_cms_article(article),
            height=900,
            scrolling=True,
        )


def _editor(article: CmsArticle, access_token: str) -> None:
    prefix = f"cms_{article.id or 'new'}"
    _load_editor_state(article, prefix)

    left, right = st.columns([1.55, .75], gap="large")
    with left:
        st.markdown('<div class="cms-kicker">Article editor</div>', unsafe_allow_html=True)
        st.text_input("Title", key=f"{prefix}_title")
        st.text_area("Subtitle / deck", key=f"{prefix}_subtitle", height=80)

        body = st_quill(
            value=st.session_state.get(f"{prefix}_body", ""),
            html=True,
            placeholder="Paste or write the complete article here…",
            key=f"{prefix}_quill",
        )
        if body is not None:
            st.session_state[f"{prefix}_body"] = body

        st.markdown("#### Header image")
        current_image = st.session_state.get(f"{prefix}_image_url", "")
        if current_image:
            st.image(current_image, use_container_width=True)
        upload = st.file_uploader(
            "Upload / replace header image",
            type=["jpg", "jpeg", "png", "webp", "avif"],
            key=f"{prefix}_upload",
        )
        upcol, rmcol = st.columns(2)
        if upload is not None and upcol.button("Upload image", key=f"{prefix}_upload_btn"):
            try:
                new_url = upload_header_image(
                    access_token,
                    st.session_state.get(f"{prefix}_slug") or st.session_state.get(f"{prefix}_title"),
                    upload.name,
                    upload.type or "application/octet-stream",
                    upload.getvalue(),
                )
                old_url = st.session_state.get(f"{prefix}_image_url", "")
                st.session_state[f"{prefix}_image_url"] = new_url
                if old_url and old_url != new_url:
                    delete_header_image(access_token, old_url)
                st.success("Header image uploaded.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if current_image and rmcol.button("Remove image", key=f"{prefix}_remove_image"):
            delete_header_image(access_token, current_image)
            st.session_state[f"{prefix}_image_url"] = ""
            st.rerun()

    with right:
        st.markdown('<div class="cms-kicker">Publishing</div>', unsafe_allow_html=True)
        if st.button("Generate / regenerate metadata", use_container_width=True, key=f"{prefix}_generate"):
            _metadata(article, prefix, force=True)
            st.success("Metadata regenerated. Every field remains editable.")
            st.rerun()

        st.text_input("Slug", key=f"{prefix}_slug")
        st.text_input("Category / topic", key=f"{prefix}_category")
        st.selectbox(
            "Format",
            ["Article", "Point of view", "Field note", "Decision note", "Framework"],
            key=f"{prefix}_kind",
        )
        st.text_area("Excerpt", key=f"{prefix}_excerpt", height=120)
        st.text_input("SEO title", key=f"{prefix}_seo_title")
        st.text_area("Meta description", key=f"{prefix}_meta_description", height=100)
        st.text_input("Keywords", key=f"{prefix}_keywords", help="Comma-separated")
        st.text_input("Hashtags", key=f"{prefix}_hashtags", help="Comma-separated")
        st.text_input("Image alt text", key=f"{prefix}_image_alt")
        st.number_input("Read time (minutes)", min_value=1, max_value=120, step=1, key=f"{prefix}_read_minutes")
        st.text_input("Social title", key=f"{prefix}_social_title")
        st.text_area("Social description", key=f"{prefix}_social_description", height=90)
        st.text_input("Original / source URL (optional)", key=f"{prefix}_source_url")
        st.checkbox("Featured", key=f"{prefix}_featured")
        st.checkbox("Show hashtags publicly", key=f"{prefix}_show_tags")

        with st.expander("Advanced article aside"):
            st.text_area("Aside HTML", key=f"{prefix}_aside", height=160)

        draft = _article_from_state(article, prefix)
        _metadata(draft, prefix, force=False)
        draft = _article_from_state(article, prefix)

        pub_label = "Update published article" if article.status == "published" else "Publish"
        save_col, pub_col = st.columns(2)
        if save_col.button("Save draft", use_container_width=True, key=f"{prefix}_save"):
            try:
                saved = save_article(access_token, replace(draft, status="draft"))
                st.session_state["cms_edit_id"] = saved.id
                st.success("Draft saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if pub_col.button(pub_label, type="primary", use_container_width=True, key=f"{prefix}_publish"):
            try:
                saved = save_article(access_token, replace(draft, status="published"))
                st.session_state["cms_edit_id"] = saved.id
                st.success("Article published.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        action1, action2 = st.columns(2)
        if action1.button("Preview", use_container_width=True, key=f"{prefix}_preview"):
            st.session_state[f"{prefix}_show_preview"] = True
        if article.id and article.status == "published" and action2.button("Unpublish", use_container_width=True, key=f"{prefix}_unpublish"):
            try:
                change_article_status(access_token, article.id, "draft")
                st.success("Article unpublished.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        _copy_button("Copy hashtags", " ".join(draft.hashtags), f"{prefix}_copy_hash")
        _copy_button(
            "Copy metadata",
            json.dumps(
                {
                    "title": draft.seo_title,
                    "description": draft.meta_description,
                    "slug": slugify(draft.slug or draft.title),
                    "keywords": list(draft.keywords),
                    "hashtags": list(draft.hashtags),
                },
                ensure_ascii=False,
                indent=2,
            ),
            f"{prefix}_copy_meta",
        )

    if st.session_state.get(f"{prefix}_show_preview"):
        _preview(_article_from_state(article, prefix))


def _extract_legacy_article(article_meta, renderer) -> tuple[str, str]:
    rendered = renderer()
    body_match = re.search(
        r'<article class="article-body">(.*?)(?:<section class="article-share">|</article>)',
        rendered,
        flags=re.S,
    )
    if body_match:
        body = body_match.group(1).strip()
    else:
        note_match = re.search(r'<article class="note-full">(.*?)</article>', rendered, flags=re.S)
        body = note_match.group(1).strip() if note_match else ""
    aside_match = re.search(r'<aside class="article-aside">(.*?)</aside>', rendered, flags=re.S)
    aside = aside_match.group(1).strip() if aside_match else ""
    return sanitize_article_html(body), sanitize_article_html(aside)


def _import_existing(access_token: str, current: list[CmsArticle]) -> None:
    existing = {article.legacy_key for article in current if article.legacy_key}
    from page_thinking import ROUTES
    from thinking_articles import ARTICLES

    imported = 0
    for meta in ARTICLES:
        if meta.key in existing:
            continue
        renderer = ROUTES.get(meta.key)
        if renderer is None:
            continue
        body, aside = _extract_legacy_article(meta, renderer)
        if not strip_html(body):
            continue
        article = CmsArticle(
            title=meta.title,
            slug=meta.slug,
            subtitle=meta.standfirst,
            content_html=body,
            aside_html=aside,
            excerpt=meta.standfirst,
            seo_title=meta.seo_title,
            meta_description=meta.seo_description,
            keywords=tuple(meta.tags),
            hashtags=tuple("#" + re.sub(r"[^A-Za-z0-9]", "", tag) for tag in meta.tags),
            category=meta.topic,
            kind=meta.kind,
            status="published",
            featured=meta.key in {"stop_ai_use_case", "roi_diagnosed_too_late"},
            legacy_key=meta.key,
            read_minutes=meta.read_minutes,
            social_title=meta.social_title,
            social_description=meta.social_description,
            published_at=f"{meta.published_iso}T12:00:00+00:00",
        )
        save_article(access_token, article)
        imported += 1
    st.success(f"Imported {imported} existing portfolio article(s).")


def _dashboard(session: dict) -> None:
    token = str(session["access_token"])
    user = session.get("user") or {}
    email_value = str(user.get("email") or OWNER_EMAIL)

    top_a, top_b = st.columns([1, .28])
    with top_a:
        st.markdown(
            """
<div class="cms-hero">
  <div class="cms-kicker">Private authoring</div>
  <h1>Portfolio article CMS</h1>
  <p>Create, edit, publish and maintain articles without changing application code.</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with top_b:
        st.caption(email_value)
        if st.button("Sign out", use_container_width=True):
            st.session_state.pop("cms_auth", None)
            st.session_state.pop("cms_edit_id", None)
            st.rerun()

    try:
        articles = admin_list_articles(token)
    except Exception as exc:
        st.error(str(exc))
        return

    edit_id = st.session_state.get("cms_edit_id")
    if edit_id == "__new__":
        article = CmsArticle()
        if st.button("← Back to articles"):
            st.session_state.pop("cms_edit_id", None)
            st.rerun()
        _editor(article, token)
        return
    if edit_id:
        article = next((item for item in articles if item.id == edit_id), None)
        if article is None:
            st.session_state.pop("cms_edit_id", None)
            st.rerun()
        if st.button("← Back to articles"):
            st.session_state.pop("cms_edit_id", None)
            st.rerun()
        _editor(article, token)
        return

    controls = st.columns([.72, .28])
    with controls[0]:
        search = st.text_input("Search articles", placeholder="Title, category or slug")
    with controls[1]:
        status_filter = st.selectbox("Status", ["All", "Published", "Draft"])

    a, b = st.columns(2)
    if a.button("＋ New article", type="primary", use_container_width=True):
        st.session_state["cms_edit_id"] = "__new__"
        st.rerun()
    if b.button("Import existing portfolio articles", use_container_width=True):
        try:
            _import_existing(token, articles)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    query = search.lower().strip()
    filtered = []
    for article in articles:
        if status_filter != "All" and article.status.lower() != status_filter.lower():
            continue
        haystack = f"{article.title} {article.slug} {article.category}".lower()
        if query and query not in haystack:
            continue
        filtered.append(article)

    if not filtered:
        st.info("No articles match the current filter.")
        return

    for article in filtered:
        badge = f'<span class="cms-status cms-status-{article.status}">{html.escape(article.status)}</span>'
        st.markdown(
            f"""
<div class="cms-card">
  {badge}
  <h3>{html.escape(article.title)}</h3>
  <p>{html.escape(article.category or "Uncategorized")} · {html.escape(article.slug)}</p>
  <div class="cms-meta">Updated {html.escape(article.updated_at[:16].replace("T", " ") if article.updated_at else "—")}{" · Featured" if article.featured else ""}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        cols = st.columns([1, 1, 1, 1, 1])
        if cols[0].button("Edit", key=f"edit_{article.id}", use_container_width=True):
            st.session_state["cms_edit_id"] = article.id
            st.rerun()
        if cols[1].button("Duplicate", key=f"dup_{article.id}", use_container_width=True):
            try:
                copy = duplicate_article(token, article)
                st.session_state["cms_edit_id"] = copy.id
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if article.status == "published":
            if cols[2].button("Unpublish", key=f"status_{article.id}", use_container_width=True):
                change_article_status(token, article.id, "draft")
                st.rerun()
            cols[3].link_button("Open", article_url(article), use_container_width=True)
        else:
            if cols[2].button("Publish", key=f"status_{article.id}", use_container_width=True):
                change_article_status(token, article.id, "published")
                st.rerun()
            cols[3].button("Open", disabled=True, key=f"open_{article.id}", use_container_width=True)

        if cols[4].button("Delete", key=f"delete_{article.id}", use_container_width=True):
            st.session_state["cms_delete_id"] = article.id

        if st.session_state.get("cms_delete_id") == article.id:
            st.warning(f'Delete “{article.title}”? This cannot be undone.')
            yes, no = st.columns(2)
            if yes.button("Confirm delete", type="primary", key=f"confirm_{article.id}", use_container_width=True):
                delete_header_image(token, article.header_image_url)
                delete_article(token, article.id)
                st.session_state.pop("cms_delete_id", None)
                st.rerun()
            if no.button("Cancel", key=f"cancel_{article.id}", use_container_width=True):
                st.session_state.pop("cms_delete_id", None)
                st.rerun()


def render_admin_dashboard() -> None:
    _noindex()
    _css()
    session = _session()
    if session is None:
        _login()
        return
    _dashboard(session)
