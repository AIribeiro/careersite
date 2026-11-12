"""Public, passwordless Executive Briefings membership and verified PDF delivery.

Independent of the privileged owner/CMS session. No anonymous table writes and
no privileged Supabase key is ever exposed to the browser.
"""
from __future__ import annotations

import os
import re
import time
from html import escape
from urllib.parse import parse_qs, quote, urlencode, urlsplit

from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from site_cms import _request_json, _rest_url
from site_analytics import ANALYTICS_URL
from thinking_articles import BASE_URL

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL = re.compile(r"^[^@\s<>]{1,64}@[^@\s<>]{1,189}$")
COOKIE_OPTIONS = dict(max_age=60 * 86400, httponly=True,
                      secure=True, samesite="lax", path="/")
ACCESS, REFRESH, EXPIRY = "portfolio_reader_at", "portfolio_reader_rt", "portfolio_reader_exp"
CONSENT_VERSION = "2026-11-reader-v1"
ROI_SLUG = "ai-roi-what-executives-must-prove-before-scaling"
AUTHORITY_SLUG = "ai-was-approved-who-can-stop-it"


def _clean_slug(value: str) -> str:
    value = str(value or "").strip().lower()
    return value if len(value) <= 120 and SLUG.fullmatch(value) else ""


def _target(request) -> str:
    return _clean_slug(request.query_params.get("next") or "")


def _auth_callback_origin() -> str:
    """Use an explicit, validated origin when testing sign-in on another app.

    Production defaults to the canonical Streamlit origin. A staging instance
    may set PORTFOLIO_READER_CALLBACK_ORIGIN in Streamlit secrets. Do not
    trust an unvalidated request Host header as an authentication redirect.
    """
    override = str(os.environ.get("PORTFOLIO_READER_CALLBACK_ORIGIN") or "").strip()
    if not override:
        return BASE_URL.rstrip("/")
    url = urlsplit(override)
    if (url.scheme != "https" or not url.hostname or
            not url.hostname.endswith(".streamlit.app") or
            url.username or url.password or url.port or
            url.path not in ("", "/") or url.query or url.fragment):
        raise ValueError("Invalid reader authentication callback origin")
    return "https://" + url.hostname.lower()


def _no_cache(response: Response) -> Response:
    response.headers.update({
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache",
        "X-Robots-Tag": "noindex,nofollow,noarchive",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    })
    return response


def _set_cookies(response: Response, session: dict) -> Response:
    expiration = int(session.get("expires_at") or
                     time.time() + int(session.get("expires_in") or 0))
    for key, value in ((ACCESS, session["access_token"]),
                       (REFRESH, session["refresh_token"]),
                       (EXPIRY, str(expiration))):
        response.set_cookie(key, str(value), **COOKIE_OPTIONS)
    return _no_cache(response)


def _clear_cookies(response: Response) -> Response:
    for name in (ACCESS, REFRESH, EXPIRY):
        response.delete_cookie(name, path="/", secure=True,
                               httponly=True, samesite="lax")
    return _no_cache(response)


def _same_origin(request) -> bool:
    if request.headers.get("sec-fetch-site") == "cross-site":
        return False
    source = request.headers.get("origin") or request.headers.get("referer") or ""
    if source:
        parsed = urlsplit(source)
        return parsed.scheme == "https" and parsed.hostname in {
            urlsplit(BASE_URL).hostname, (request.url.hostname or "").lower()}
    return request.headers.get("sec-fetch-site") == "same-origin"


async def _form(request, limit=4096) -> dict:
    if int(request.headers.get("content-length") or "0") > limit:
        raise ValueError("Too much data")
    body = await request.body()
    if len(body) > limit:
        raise ValueError("Too much data")
    values = parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
    return {key: item[0] for key, item in values.items() if item}


def _refresh(refresh_token: str) -> dict:
    if not refresh_token or len(refresh_token) > 4096:
        raise ValueError("Invalid session")
    response = _request_json(
        "POST", ANALYTICS_URL.rstrip("/") + "/auth/v1/token?grant_type=refresh_token",
        payload={"refresh_token": refresh_token}, timeout=10)
    if not isinstance(response, dict) or not response.get("access_token") or not response.get("refresh_token"):
        raise ValueError("Invalid reader session")
    return response


def _verified_user(access_token: str) -> dict:
    identity = _request_json(
        "GET", ANALYTICS_URL.rstrip("/") + "/auth/v1/user",
        token=access_token, timeout=10)
    if not isinstance(identity, dict) or not identity.get("id") or not identity.get("email_confirmed_at"):
        raise ValueError("Verified email required")
    return identity


def _session(request) -> tuple[dict | None, dict | None]:
    access = str(request.cookies.get(ACCESS) or "")
    refresh = str(request.cookies.get(REFRESH) or "")
    try:
        expiry = int(request.cookies.get(EXPIRY) or "0")
    except (ValueError, TypeError):
        expiry = 0
    if not refresh:
        return None, None
    if access and expiry > time.time() + 90:
        try:
            return {"access_token": access, "refresh_token": refresh, "expires_at": expiry}, _verified_user(access)
        except (RuntimeError, ValueError, TimeoutError):
            return None, None
    try:
        new_session = _refresh(refresh)
        return new_session, _verified_user(new_session["access_token"])
    except (RuntimeError, ValueError, TimeoutError):
        return None, None


def _attach(response: Response, request, session: dict | None) -> Response:
    if session and str(request.cookies.get(REFRESH) or "") != str(session["refresh_token"]):
        return _set_cookies(response, session)
    return _no_cache(response)


def _get_profile(token: str, user_id: str) -> dict | None:
    rows = _request_json(
        "GET", _rest_url("portfolio_reader_profiles?select=*&user_id=eq." + quote(user_id, safe="") + "&limit=1"),
        token=token)
    return rows[0] if isinstance(rows, list) and rows else None


def _register_profile(session: dict, user: dict) -> dict:
    token = session["access_token"]
    user_id = str(user["id"])
    existing = _get_profile(token, user_id)
    if existing:
        return existing
    metadata = user.get("user_metadata") if isinstance(user.get("user_metadata"), dict) else {}
    first_name = str(metadata.get("reader_first_name") or "").strip()[:80]
    opted_in = metadata.get("reader_editorial_opt_in") is True
    payload = {
        "user_id": user_id,
        "email": str(user["email"]).strip().lower(),
        "first_name": first_name,
        "newsletter_opt_in": opted_in,
        "newsletter_consent_at": _utc_now() if opted_in else None,
        "consent_notice_version": CONSENT_VERSION if opted_in else None,
        "acquisition_source": "briefing_pdf",
    }
    rows = _request_json("POST", _rest_url("portfolio_reader_profiles"),
                         token=token, payload=payload, prefer="return=representation")
    if opted_in:
        _log_consent(token, user_id, True, "registration")
    return rows[0] if isinstance(rows, list) and rows else payload


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _log_consent(token: str, user_id: str, enabled: bool, source: str) -> None:
    _request_json(
        "POST", _rest_url("portfolio_reader_consent_events"),
        token=token,
        payload={"user_id": user_id, "subscribed": bool(enabled),
                 "notice_version": CONSENT_VERSION, "source": source})


def _layout(title: str, body: str, *, notice: str = "") -> HTMLResponse:
    message = '<p role="status" class="notice">' + escape(notice) + '</p>' if notice else ""
    doc = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="referrer" content="no-referrer">
<title>""" + escape(title) + """ | Executive AI Briefings</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f4f0e8;color:#173046;
font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
nav{background:#0b1727;color:#f8f5f0;padding:18px max(24px,calc((100vw - 1090px)/2))}
nav a{color:inherit;text-decoration:none;font-size:13px;font-weight:700}
main{max-width:1090px;margin:0 auto;padding:clamp(36px,6vw,80px) 24px}
section{max-width:670px;background:#fffdfa;border:1px solid #d9d3ca;padding:clamp(26px,5vw,52px);
box-shadow:0 15px 40px rgba(12,35,53,.05)}
.kicker{font-size:10px;font-weight:800;color:#ae673e;letter-spacing:.16em;text-transform:uppercase}
h1{font:400 clamp(34px,5vw,52px)/1.08 Georgia,serif;letter-spacing:-.03em;margin:13px 0 22px}
h2{font:400 26px/1.2 Georgia,serif;margin:25px 0 8px}
p{color:#4b5b65;margin:0 0 18px}label{display:block;font-weight:700;font-size:12px;margin:19px 0 7px}
input[type=text],input[type=email]{width:100%;border:1px solid #b8c0c4;background:#fff;
padding:13px 14px;border-radius:3px;font:inherit;min-height:47px}
input:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid #bc815b;outline-offset:3px}
.check{display:flex;gap:12px;align-items:start;margin:23px 0}.check input{margin-top:5px;flex-shrink:0}
.check label{font-weight:400;margin:0;line-height:1.5}
button,.button{display:inline-flex;align-items:center;justify-content:center;min-height:47px;
background:#13344b;color:#fff!important;border:1px solid #13344b;border-radius:3px;
font:750 13px/1.35 Arial,sans-serif;text-decoration:none;padding:13px 21px;cursor:pointer}
button:hover,.button:hover{background:#23536b}
.small{font-size:12px;color:#63727b;line-height:1.6;margin-top:17px}
.note{border-top:1px solid #ddd9d1;padding-top:20px;margin-top:27px}
a{color:#9c5d3a}.notice{padding:13px 17px;background:#f0e8df;border-left:3px solid #a86542;color:#173046}
.library-item{display:flex;align-items:start;justify-content:space-between;gap:16px;
padding:17px 0;border-bottom:1px solid #e3ded7}.library-item strong{display:block;font:400 19px/1.3 Georgia,serif}
.library-item a{flex-shrink:0;text-decoration:none;font-size:12px;font-weight:800}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}
footer{max-width:1090px;margin:auto;padding:18px 24px 45px;font-size:12px;color:#65727d}
footer a{margin-right:16px}
@media(max-width:560px){.library-item{display:block}.library-item a{display:inline-block;margin-top:9px}}
</style></head><body><nav><a href="/?page=briefings">JAIR RIBEIRO / EXECUTIVE AI BRIEFINGS</a></nav>
<main><section><div class="kicker">Reader access · Complimentary</div><h1>""" + escape(title) + "</h1>" + message + body + """</section></main>
<footer><a href="/?page=briefings">All briefings</a><a href="/~/+/readers/privacy">Privacy &amp; data</a><a href="/?page=contact">Contact</a></footer>
</body></html>"""
    return _no_cache(HTMLResponse(doc))


def _login(request, *, notice: str = "") -> Response:
    # Submit to the currently open Cloud-proxied URL. This avoids the
    # forwarding layer rewriting an explicit action into /readers/request.
    description = (
        "Read every briefing online without an account. Register once to save printable "
        "executive infographics to your personal library. No password or payment required."
    )
    body = (f"<p>{description}</p>" +
        '<form method="post">'
        '<label for="first_name">First name</label>'
        '<input id="first_name" name="first_name" type="text" autocomplete="given-name" maxlength="80" required>'
        '<label for="email">Email address</label>'
        '<input id="email" name="email" type="email" autocomplete="email" maxlength="254" required>'
        '<div class="check"><input id="editorial" name="editorial" type="checkbox" value="yes">'
        '<label for="editorial">Also send me new Executive AI Briefings and occasional AI leadership resources. '
        'Optional; unsubscribe whenever you wish.</label></div>'
        '<button type="submit">Email my secure access link →</button></form>'
        '<p class="small">Already a reader? <a href="/~/+/readers/signin">Sign in using your email</a>.</p>'
        '<p class="small">We use your email to verify access and maintain your download library. '
        'Editorial emails are only sent if you select the optional checkbox. '
        '<a href="/~/+/readers/privacy">How your data is used</a>.</p>')
    return _layout("Take the briefings with you", body, notice=notice)


def _returning_signin(request) -> Response:
    # Keep the Cloud proxy path and any ?next=slug query on form submission.
    return _layout("Welcome back",
        '<p>Enter your registered email. We will send a secure, one-time access link. '
        'No password or name entry required.</p>'
        '<form method="post">'
        '<input type="hidden" name="intent" value="signin">'
        '<label for="email">Email address</label>'
        '<input id="email" name="email" type="email" autocomplete="email" maxlength="254" required>'
        '<button type="submit">Email my sign-in link →</button></form>'
        '<p class="small">New here? <a href="/~/+/readers/login">Register for free</a>.</p>')


def _confirm_page(request) -> Response:
    slug = _target(request)
    js_next = "/~/+/readers/library" + ("?highlight=" + quote(slug) if slug else "")
    # The magic-link tokens arrive in the URL fragment; never send them to an
    # analytics script, store them in localStorage or leave them in browser history.
    body = ('<p id="status" role="status">Verifying your secure access link…</p>'
            '<p class="small">If this link has expired, '
            '<a href="/~/+/readers/login">request a new one</a>.</p>'
            '<script>'
            '(async function(){'
            'const status=document.getElementById("status");'
            'const p=new URLSearchParams(location.hash.slice(1));'
            'const token=p.get("refresh_token");'
            'history.replaceState(null,"",location.pathname+location.search);'
            'if(!token){status.textContent="This access link is missing its verification details. Please request a new link.";return;}'
            'try{const res=await fetch("/~/+/readers/session",{method:"POST",credentials:"same-origin",'
            'headers:{"Content-Type":"application/x-www-form-urlencoded"},'
            'body:new URLSearchParams({refresh_token:token,next:' + repr(slug) + '}).toString()});'
            'if(!res.ok)throw Error("verification");'
            'location.replace(' + repr(js_next) + ');'
            '}catch(e){status.textContent="The link could not be verified. Request a new sign-in email.";}})();'
            '</script>')
    return _layout("Confirming your access", body)


def _library(request, profile: dict) -> Response:
    slug = _clean_slug(request.query_params.get("highlight") or "")
    from site_cms import fetch_published_articles
    articles = [a for a in fetch_published_articles()
                if str(a.kind).strip().casefold() == "executive briefing"]
    articles.sort(key=lambda a: str(a.published_at or a.created_at or ""), reverse=True)
    rows = []
    for item in articles:
        article_slug = _clean_slug(item.slug)
        if not article_slug or not has_briefing_pdf(article_slug):
            continue
        label = "Open PDF" if article_slug != slug else "Download your PDF"
        rows.append('<div class="library-item"><div><strong>' + escape(item.title) + '</strong>'
                    '<span class="small">Executive briefing · Complimentary PDF</span></div>'
                    '<a href="/~/+/readers/download/' + escape(article_slug, quote=True) +
                    '.pdf" target="_self">' + label + ' ↓</a></div>')
    user_first_name = str(profile.get("first_name") or "").strip()
    greeting = "Welcome, " + escape(user_first_name) + "." if user_first_name else "Welcome to your library."
    selected = next((a for a in articles if _clean_slug(a.slug) == slug and has_briefing_pdf(slug)), None)
    selected_card = (
        '<div class="notice"><strong>Your requested briefing is ready.</strong><br>' +
        escape(selected.title) + '<div class="actions"><a class="button" href="/~/+/readers/download/' +
        escape(slug, quote=True) + '.pdf">Download selected PDF ↓</a></div></div>'
        if selected else ""
    )
    body = ('<p>' + greeting + ' Your secure downloads are available here. '
            'The full editorial editions remain free to read and share online.</p>'
            + selected_card
            + (''.join(rows) if rows else '<p>There are no published briefing downloads yet.</p>')
            + '<div class="actions"><a class="button" href="/~/+/readers/preferences">My preferences</a>'
            '<a class="button" href="/?page=briefings">Read online</a></div>'
            '<form method="post" action="/~/+/readers/signout" class="note">'
            '<button type="submit">Sign out</button></form>')
    return _layout("Your executive library", body)


def _privacy() -> Response:
    return _layout("Privacy and reader data",
        '<p>This free reader service is operated by Jair Ribeiro. We collect '
        'your name, verified email, download activity and any optional editorial '
        'email preference to provide your account and understand resource use.</p>'
        '<h2>Choice and control</h2><p>You can access the library without subscribing '
        'to email updates. You can withdraw editorial email consent in My preferences. '
        'Access and correction requests, data export and deletion requests can be sent '
        'using the <a href="/?page=contact">portfolio contact page</a>.</p>'
        '<h2>Storage</h2><p>Reader accounts and records are held in the portfolio\'s '
        'Supabase database. Verification links are delivered by its authentication '
        'email service. We do not sell reader contact details. We retain account '
        'records while the membership remains active, subject to legal requirements '
        'and erasure requests. Briefing downloads are free.</p>'
        '<p class="small">Notice version: ' + CONSENT_VERSION + '.</p>')


def _preferences(profile: dict, *, notice: str = "") -> Response:
    checked = ' checked' if profile.get("newsletter_opt_in") else ""
    body = ('<p>Update your name and editorial email choice. '
            'Your briefing downloads remain available regardless of your subscription preference.</p>'
            '<form method="post" action="/~/+/readers/preferences">'
            '<label for="first_name">First name</label>'
            '<input id="first_name" name="first_name" type="text" required maxlength="80" value="' +
            escape(str(profile.get("first_name") or ""), quote=True) + '">'
            '<div class="check"><input type="checkbox" id="editorial" name="editorial" value="yes"' + checked + '>'
            '<label for="editorial">Send me new Executive AI Briefings and occasional AI leadership resources.</label></div>'
            '<button type="submit">Save preferences</button></form>'
            '<p class="small">Email: ' + escape(str(profile.get("email") or "")) + '</p>'
            '<a href="/~/+/readers/library">← Back to your library</a>')
    return _layout("Reader preferences", body, notice=notice)


async def reader_route(request) -> Response:
    action = str(request.path_params.get("action") or "")
    # Legacy ASGI GET routes now point to the supported Streamlit page.
    # The old HTML POST endpoints are intentionally not used for signup.
    if request.method == "GET" and action in {
        "login", "signin", "library", "preferences", "confirm"
    }:
        return _no_cache(RedirectResponse("/?page=readers", status_code=303))
    if action == "privacy" and request.method == "GET":
        return _privacy()
    if action == "confirm" and request.method == "GET":
        return _confirm_page(request)
    if action == "signin" and request.method == "GET":
        return _returning_signin(request)
    if action in {"request", "login", "signin"} and request.method == "POST":
        if not _same_origin(request):
            return _no_cache(Response("Forbidden", status_code=403))
        try:
            form = await _form(request)
            first = str(form.get("first_name") or "").strip()
            email = str(form.get("email") or "").strip().lower()
            returning = action == "signin" or form.get("intent") == "signin"
            if (not returning and not first) or len(first) > 80 or not EMAIL.fullmatch(email) or len(email) > 254:
                return _login(request, notice="Enter your name and a valid email address.")
            slug = _target(request)
            redirect = _auth_callback_origin() + "/~/+/readers/confirm" + ("?next=" + quote(slug) if slug else "")
            url = ANALYTICS_URL.rstrip("/") + "/auth/v1/otp?" + urlencode({"redirect_to": redirect})
            opted_in = form.get("editorial") == "yes"
            await run_in_threadpool(_request_json, "POST", url, payload={
                "email": email, "create_user": not returning,
                "data": ({} if returning else {"reader_first_name": first,
                         "reader_editorial_opt_in": opted_in,
                         "reader_notice_version": CONSENT_VERSION})
            })
            return _layout("Check your inbox",
                "<p>We have requested a one-time access link. Open the email to verify your address "
                "and continue to the library.</p>"
                '<p class="small">If it does not arrive, check spam or try again in a minute. '
                'For security, links expire and work only once.</p>')
        except (RuntimeError, ValueError, TimeoutError):
            return _login(request, notice="We could not send the access link. Please try again shortly.")
    if action == "session" and request.method == "POST":
        if not _same_origin(request):
            return _no_cache(Response("Forbidden", status_code=403))
        try:
            form = await _form(request, limit=8192)
            session = await run_in_threadpool(_refresh, str(form.get("refresh_token") or ""))
            user = await run_in_threadpool(_verified_user, session["access_token"])
            await run_in_threadpool(_register_profile, session, user)
            return _set_cookies(JSONResponse({"verified": True}), session)
        except (RuntimeError, ValueError, TimeoutError, KeyError):
            return _no_cache(JSONResponse({"verified": False}, status_code=401))
    session, user = await run_in_threadpool(_session, request)
    if action == "login" and request.method == "GET":
        if session and user:
            return _attach(RedirectResponse("/~/+/readers/library", status_code=303), request, session)
        return _login(request)
    if not session or not user:
        return _clear_cookies(RedirectResponse(
            "/~/+/readers/login" + ("?next=" + quote(_target(request)) if _target(request) else ""),
            status_code=303))
    if action == "signout" and request.method == "POST":
        if not _same_origin(request):
            return _no_cache(Response("Forbidden", status_code=403))
        try:
            await run_in_threadpool(
                _request_json, "POST",
                ANALYTICS_URL.rstrip("/") + "/auth/v1/logout",
                token=session["access_token"], payload={})
        except (RuntimeError, ValueError, TimeoutError):
            pass
        return _clear_cookies(RedirectResponse("/?page=briefings", status_code=303))
    try:
        profile = await run_in_threadpool(_register_profile, session, user)
        if action == "library" and request.method == "GET":
            return _attach(_library(request, profile), request, session)
        if action == "preferences":
            if request.method == "GET":
                return _attach(_preferences(profile), request, session)
            if request.method == "POST":
                if not _same_origin(request):
                    return _no_cache(Response("Forbidden", status_code=403))
                form = await _form(request)
                first = str(form.get("first_name") or "").strip()
                if not first or len(first) > 80:
                    return _attach(_preferences(profile, notice="Enter a first name of up to 80 characters."), request, session)
                subscribed = form.get("editorial") == "yes"
                previous = bool(profile.get("newsletter_opt_in"))
                payload = {
                    "first_name": first,
                    "newsletter_opt_in": subscribed,
                    "newsletter_consent_at": (_utc_now() if subscribed and not previous else
                                               profile.get("newsletter_consent_at") if subscribed else None),
                    "consent_notice_version": CONSENT_VERSION if subscribed else None,
                    "updated_at": _utc_now()
                }
                await run_in_threadpool(
                    _request_json, "PATCH",
                    _rest_url("portfolio_reader_profiles?user_id=eq." + quote(user["id"], safe="")),
                    token=session["access_token"], payload=payload)
                if previous != subscribed:
                    await run_in_threadpool(
                        _log_consent, session["access_token"], user["id"], subscribed, "preferences")
                return _attach(_preferences({**profile, **payload}, notice="Your preferences have been saved."),
                               request, session)
    except (RuntimeError, ValueError, TimeoutError):
        return _layout("Temporarily unavailable", "<p>Your reader account could not be loaded. Please try again.</p>")
    return _no_cache(Response("Not found", status_code=404))


def _pdf_for_article(slug: str) -> bytes | None:
    from site_cms import fetch_public_article
    article = fetch_public_article(slug)
    if not article or str(article.kind).strip().casefold() != "executive briefing":
        return None
    if str(article.status) != "published":
        return None
    if slug == ROI_SLUG:
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "static" / "briefing-ai-roi-proof-before-scale.pdf"
        return path.read_bytes() if path.is_file() else None
    if slug == AUTHORITY_SLUG:
        from briefing_authority_artwork import artwork_pdf
        return artwork_pdf()
    from briefing_approved_asset_renderer import verified_pdf_for_article
    return verified_pdf_for_article(article)


def has_briefing_pdf(slug: str) -> bool:
    """Only advertise PDFs that are actually present in the published bundle."""
    slug = _clean_slug(slug)
    if slug in (ROI_SLUG, AUTHORITY_SLUG):
        return True
    from briefing_approved_asset_renderer import load_bundle, ArtworkError
    try:
        return bool(slug and load_bundle(slug))
    except ArtworkError:
        return False


def reader_download_cta(slug: str) -> str:
    """Small editorial utility, not a promotional paywall."""
    slug = _clean_slug(slug)
    if not slug or not has_briefing_pdf(slug):
        return ""
    return ("""<aside class="reader-resource-cta" data-analytics-section="briefing-pdf-download">
<style>.site .reader-resource-cta{display:flex;align-items:center;justify-content:space-between;
gap:20px;flex-wrap:wrap;background:#e9efee;border:1px solid #cfdbda;padding:24px 28px;margin:27px 0}
.site .reader-resource-cta span{font:800 10px/1.5 Arial,sans-serif;letter-spacing:.12em;
text-transform:uppercase;color:#916346}
.site .reader-resource-cta h3{font:500 26px/1.18 Georgia,serif;margin:6px 0;color:#18364a}
.site .reader-resource-cta p{font:13px/1.6 Arial,sans-serif;color:#52616e;margin:0}
.site .reader-resource-cta a{display:inline-flex;justify-content:center;align-items:center;
min-height:46px;padding:12px 19px;background:#163b51;color:#fff!important;
text-decoration:none!important;font:750 12px/1.4 Arial,sans-serif}
@media(max-width:650px){.site .reader-resource-cta a{width:100%}}</style>
<div><span>Complimentary executive resource</span><h3>Keep the decision framework at hand.</h3>
<p>Access the A4 infographic PDF with one verified reader account. Online reading remains free.</p>
</div><a data-hq-event="briefing_reader_pdf" href="/?page=briefing&amp;article=""" +
            escape(slug, quote=True) + """&amp;pdf=1" target="_blank" rel="noopener">Download PDF ↓</a></aside>""")


async def reader_download(request) -> Response:
    slug = _clean_slug(request.path_params.get("slug") or "")
    if not slug:
        return _no_cache(Response("Not found", status_code=404))
    session, user = await run_in_threadpool(_session, request)
    if not session or not user:
        return _clear_cookies(RedirectResponse(
            "/~/+/readers/login?next=" + quote(slug), status_code=303))
    try:
        await run_in_threadpool(_register_profile, session, user)
        pdf = await run_in_threadpool(_pdf_for_article, slug)
        if not pdf:
            return _attach(_layout("Resource unavailable",
                '<p>This edition does not currently have a verified PDF. '
                '<a href="/?page=briefings">Read the briefing online</a>.</p>'), request, session)
        await run_in_threadpool(
            _request_json, "POST", _rest_url("portfolio_reader_downloads"),
            token=session["access_token"],
            payload={"user_id": user["id"], "article_slug": slug, "source": "pdf_download"})
        response = Response(pdf, media_type="application/pdf", headers={
            "Content-Disposition": 'attachment; filename="' + slug + '-executive-infographic.pdf"',
        })
        return _attach(response, request, session)
    except (RuntimeError, ValueError, TimeoutError, OSError):
        return _attach(_layout("Temporarily unavailable",
            "<p>We could not deliver the PDF. Please try again shortly.</p>"), request, session)
