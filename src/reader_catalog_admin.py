"""Read-only, private CRM view of verified Executive AI Briefings readers.

This endpoint always checks the established CMS owner identity. Reader rows
are exposed to the owner only through RLS with the owner's signed JWT.
"""
from __future__ import annotations

from collections import Counter
from csv import writer
from html import escape
from io import StringIO
import time
from urllib.parse import urlencode

from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, RedirectResponse, Response

from site_cms import OWNER_EMAIL, _request_json, _rest_url, owner_refresh
from site_analytics import ANALYTICS_URL
from site_owner_http_auth import _set_session, _no_store
from site_owner_persistence import ACCESS_COOKIE, REFRESH_COOKIE, EXPIRY_COOKIE

BATCH_SIZE = 500
MAX_ROWS = 10000


def _owner(request) -> tuple[str, dict | None] | None:
    access = str(request.cookies.get(ACCESS_COOKIE) or "")
    refresh = str(request.cookies.get(REFRESH_COOKIE) or "")
    try:
        expires = int(request.cookies.get(EXPIRY_COOKIE) or "0")
    except (ValueError, TypeError):
        expires = 0
    if not refresh:
        return None
    renewal = None
    if not access or expires <= time.time() + 90:
        renewal = owner_refresh(refresh)
        access = str(renewal.get("access_token") or "")
    if not access:
        return None
    identity = _request_json(
        "GET", ANALYTICS_URL.rstrip("/") + "/auth/v1/user",
        token=access, timeout=10)
    if not isinstance(identity, dict) or str(identity.get("email") or "").strip().lower() != OWNER_EMAIL:
        return None
    return access, renewal


def _owner_read(token: str, table: str, fields: str, *, order: str) -> list[dict]:
    # Pagination uses only controlled table and column identifiers.
    if table not in ("portfolio_reader_profiles", "portfolio_reader_downloads"):
        raise ValueError("Unsupported catalog")
    rows = []
    for offset in range(0, MAX_ROWS, BATCH_SIZE):
        params = urlencode({
            "select": fields, "order": order, "limit": BATCH_SIZE, "offset": offset})
        batch = _request_json("GET", _rest_url(table + "?" + params),
                              token=token, timeout=15)
        if not isinstance(batch, list):
            raise ValueError("Invalid catalog response")
        rows.extend(batch)
        if len(batch) < BATCH_SIZE:
            break
    return rows


def _records(token: str) -> tuple[list[dict], Counter, dict]:
    profiles = _owner_read(
        token, "portfolio_reader_profiles",
        "user_id,first_name,email,newsletter_opt_in,created_at,acquisition_source",
        order="created_at.desc")
    downloads = _owner_read(
        token, "portfolio_reader_downloads", "user_id,article_slug,downloaded_at",
        order="downloaded_at.desc")
    counts = Counter(str(event.get("user_id")) for event in downloads)
    recent = {}
    for event in downloads:
        uid = str(event.get("user_id") or "")
        if uid and uid not in recent:
            recent[uid] = str(event.get("downloaded_at") or "")
    return profiles, counts, recent


def _date(value: str) -> str:
    return (value or "")[:10] or "—"


def _safe_csv(value: object) -> str:
    """Prevent CSV formula injection when opened in spreadsheet software."""
    s = str(value or "")
    return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else s


def _export(profiles: list[dict], counts: Counter, recent: dict) -> Response:
    sink = StringIO()
    out = writer(sink)
    out.writerow(["First name", "Email", "Registered", "Editorial opt-in",
                  "Acquisition source", "PDF downloads (recorded)", "Last PDF download"])
    for profile in profiles:
        uid = str(profile.get("user_id") or "")
        out.writerow([_safe_csv(profile.get("first_name")),
                      _safe_csv(profile.get("email")),
                      _date(str(profile.get("created_at") or "")),
                      "Yes" if profile.get("newsletter_opt_in") else "No",
                      _safe_csv(profile.get("acquisition_source")),
                      counts[uid], _date(recent.get(uid, ""))])
    response = Response(sink.getvalue().encode("utf-8-sig"), media_type="text/csv",
                        headers={"Content-Disposition": 'attachment; filename="executive-briefings-readers.csv"'})
    return _no_store(response)


def _dashboard(profiles: list[dict], counts: Counter, recent: dict) -> Response:
    members = len(profiles)
    opted = sum(bool(row.get("newsletter_opt_in")) for row in profiles)
    touched = sum(counts.get(str(row.get("user_id") or ""), 0) > 0 for row in profiles)
    total_events = sum(counts.values())
    rows = []
    for item in profiles:
        uid = str(item.get("user_id") or "")
        rows.append("<tr><td><strong>" + escape(str(item.get("first_name") or "—"))
                    + "</strong></td><td>" + escape(str(item.get("email") or "")) + "</td>"
                    + "<td>" + escape(_date(str(item.get("created_at") or ""))) + "</td>"
                    + "<td>" + ("Subscribed" if item.get("newsletter_opt_in") else "No") + "</td>"
                    + "<td>" + str(counts[uid]) + "</td>"
                    + "<td>" + escape(_date(recent.get(uid, ""))) + "</td></tr>")
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer">
<title>Executive Briefings | Reader catalog</title><style>
*{box-sizing:border-box}body{margin:0;color:#142d3d;background:#f5f2ed;font:14px/1.6 system-ui,-apple-system,Arial,sans-serif}
header{background:#0b1b2a;color:#fff;padding:20px max(26px,calc((100vw - 1140px)/2));display:flex;gap:22px;justify-content:space-between;flex-wrap:wrap}
header a{color:#eac1a2;text-decoration:none;font-size:12px;font-weight:700}main{max-width:1140px;margin:auto;padding:56px 25px 75px}
.kicker{color:#a26b4a;letter-spacing:.18em;font-size:10px;font-weight:800;text-transform:uppercase}
h1{font:400 clamp(37px,5vw,56px)/1.1 Georgia,serif;letter-spacing:-.025em;margin:13px 0 13px}
.intro{color:#596976;max-width:750px;margin-bottom:29px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:34px}
.stats>div{background:#fffdfa;border:1px solid #ded9d2;padding:25px 22px}.stats strong{font:400 36px Georgia,serif;display:block}
.stats span{font-size:11px;color:#687581}.sheet{background:#fffdfa;border:1px solid #d9d3ca;padding:27px}
.sheet-top{display:flex;justify-content:space-between;gap:18px;align-items:center;flex-wrap:wrap;margin-bottom:19px}
h2{font:400 29px Georgia,serif;margin:0}.export{display:inline-flex;padding:11px 17px;background:#143b52;color:white!important;text-decoration:none;font-weight:750;font-size:12px}
table{width:100%;border-collapse:collapse;text-align:left}th{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#7c6e64;background:#f5f0e9}
th,td{padding:13px 10px;border-bottom:1px solid #e9e3d9;overflow-wrap:anywhere}td{font-size:12px}
.scroll{overflow-x:auto}p.note{color:#66717a;font-size:11px;margin:17px 0 0}
@media(max-width:720px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.sheet{padding:17px}th,td{padding:10px 8px;white-space:nowrap}}
</style></head><body><header><strong>JAIR RIBEIRO / PRIVATE READER INTELLIGENCE</strong>
<a href="/?page=analytics">← Return to Portfolio Analytics</a></header><main>
<div class="kicker">Executive AI Briefings · Audience directory</div>
<h1>Known readers. Verified relationships.</h1>
<p class="intro">A confidential view of verified accounts, optional editorial subscriptions and actual PDF requests. No anonymous site views are treated as customers.</p>
<div class="stats"><div><strong>""" + str(members) + """</strong><span>Registered readers</span></div>
<div><strong>""" + str(opted) + """</strong><span>Editorial opt-ins</span></div>
<div><strong>""" + str(touched) + """</strong><span>Readers who downloaded</span></div>
<div><strong>""" + str(total_events) + """</strong><span>Recorded PDF requests</span></div></div>
<div class="sheet"><div class="sheet-top"><h2>Reader catalog</h2>
<a class="export" href="/~/+/readers-admin/export.csv">Export CSV ↓</a></div>
<div class="scroll"><table><thead><tr><th>First name</th><th>Email</th><th>Registered</th>
<th>Editorial email</th><th>Downloads</th><th>Last download</th></tr></thead><tbody>""" + (
    "".join(rows) if rows else '<tr><td colspan="6">No verified registrations yet.</td></tr>'
    ) + """</tbody></table></div><p class="note">Newsletter permissions are separate from membership. Customer contact information must only be used in line with the recorded consent and stated privacy notice. Figures are capped at 10,000 records per dataset; no values are estimated.</p>
</div></main></body></html>"""
    return _no_store(HTMLResponse(html))


async def reader_admin_route(request) -> Response:
    try:
        state = await run_in_threadpool(_owner, request)
        if state is None:
            return _no_store(RedirectResponse("/~/+/owner-auth/login?next=analytics", status_code=303))
        token, renewal = state
        profiles, counts, recent = await run_in_threadpool(_records, token)
        response = _export(profiles, counts, recent) if request.url.path.endswith("/export.csv") else _dashboard(profiles, counts, recent)
        if renewal:
            return _set_session(response, renewal)
        return _no_store(response)
    except (RuntimeError, ValueError, TimeoutError):
        return _no_store(HTMLResponse(
            "<h1>Reader catalog temporarily unavailable</h1><p>Please try again later.</p>",
            status_code=503))
