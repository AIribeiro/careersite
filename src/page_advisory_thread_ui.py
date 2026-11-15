"""Shared, accessible advisory correspondence presentation.

Client and owner read the same chronological messages through separate, RLS
protected entry points. This file only renders escaped text and does not grant
permissions or perform writes.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

THREAD_UI_VERSION = "shared_dialogue_20261115"
_ZONE = ZoneInfo("Europe/Stockholm")
CSS = """
<style>
.ad-dialogue{width:100%;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:#1d354a}
.ad-dialogue *{box-sizing:border-box}
.ad-dialogue .day{display:flex;gap:16px;align-items:center;justify-content:center;
  font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
  color:#718093;margin:24px 0 14px}
.ad-dialogue .day:before,.ad-dialogue .day:after{content:"";height:1px;
  flex:1;background:#e4ddd3}
.ad-dialogue .message{max-width:88%;padding:17px 20px;margin:10px 0 18px;
  background:#fffdfa;border:1px solid #e0d9cd;border-left:3px solid #b58260;
  box-shadow:0 2px 12px rgba(14,33,54,.03)}
.ad-dialogue .message.mine{margin-left:auto;background:#f0f4f5;
  border-color:#d7e1e3;border-left-color:#6e8b9c}
.ad-dialogue .message .meta{display:flex;justify-content:space-between;
  flex-wrap:wrap;gap:5px 15px;margin-bottom:9px}
.ad-dialogue .message .who{color:#203b52;font-size:12px;font-weight:800}
.ad-dialogue .message .when{color:#63768a;font-size:11px;white-space:nowrap}
.ad-dialogue .message .body{font-size:14px;line-height:1.72;white-space:pre-wrap;
  overflow-wrap:anywhere;color:#344b60}
.ad-dialogue .empty{padding:24px;border:1px solid #e2d9cd;
  background:#fffdfa;color:#516678;line-height:1.7;font-size:13px}
.ad-dialogue .thread-footer{font-size:11px;color:#68798a;margin:12px 0}
.ad-dialogue .casebar{display:flex;flex-wrap:wrap;gap:8px 25px;
  padding:15px 20px;background:#f8f4ec;border:1px solid #ded7ca}
.ad-dialogue .casebar span{font-size:11px;font-weight:800;color:#3f566a}
.ad-dialogue .casebar b{color:#986442}
.ad-dialogue .notice{border-left:4px solid #a77a58;border-top:1px solid #e2d8ca;
  border-right:1px solid #e2d8ca;border-bottom:1px solid #e2d8ca;
  background:#fffdf9;padding:15px 19px;margin:15px 0}
.ad-dialogue .notice small{display:block;color:#9f6746;letter-spacing:.1em;
  font-weight:800;font-size:10px;text-transform:uppercase;margin-bottom:7px}
.ad-dialogue .notice p{font-size:13px;line-height:1.65;color:#394e61;
  margin:0;white-space:pre-wrap;overflow-wrap:anywhere}
@media(max-width:700px),(max-device-width:700px){
 .ad-dialogue .message{max-width:100%;padding:15px 16px;margin:9px 0 13px}
 .ad-dialogue .casebar{padding:12px;gap:8px 14px}
}
</style>
"""


def _safe(value: object, limit: int = 8000) -> str:
    return escape(str(value if value is not None else "")[:limit], quote=True)


def _time(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
        return parsed.astimezone(_ZONE)
    except (ValueError, TypeError, OverflowError):
        return None


def pretty_date(value: object) -> str:
    dt = _time(value)
    return dt.strftime("%d %b %Y") if dt else str(value or "")[:10] or "Not recorded"


def pretty_time(value: object) -> str:
    dt = _time(value)
    return dt.strftime("%H:%M") if dt else str(value or "")[11:16]


def render_casebar(status: str, submitted: object, count: int,
                   *, needs_response: bool = False) -> None:
    badge = "<span><b>REPLY NEEDED</b></span>" if needs_response else ""
    st.html(CSS + '<div class="ad-dialogue"><div class="casebar">'
            '<span>STATUS · ' + _safe(status, 90) + '</span>'
            '<span>SUBMITTED · ' + _safe(pretty_date(submitted)) + '</span>'
            '<span>MESSAGES · ' + str(count) + '</span>' +
            badge + '</div></div>')


def render_notice(label: str, text: object) -> None:
    if str(text or "").strip():
        st.html(CSS + '<div class="ad-dialogue"><div class="notice">'
                '<small>' + _safe(label, 90) + '</small><p>' +
                _safe(text, 2500) + '</p></div></div>')


def render_thread(messages: list[dict], *,
                  viewer: str, client_name: str = "Client",
                  limit: int = 150) -> None:
    """Readable dates, sender identities and separated messages for both roles.

    'mine' describes the actual viewer, not an inferred read receipt.
    """
    if not messages:
        st.html(CSS + '<div class="ad-dialogue"><div class="empty">'
                'No messages yet. The first response will appear here.</div></div>')
        return
    pieces: list[str] = []
    previous_day = ""
    for msg in messages:
        dt = _time(msg.get("created_at"))
        day = dt.date().isoformat() if dt else str(msg.get("created_at") or "")[:10]
        if day != previous_day:
            pieces.append('<div class="day"><span>' +
                          _safe(pretty_date(msg.get("created_at"))) +
                          '</span></div>')
            previous_day = day
        advisor = msg.get("sender") == "advisor"
        own = (advisor and viewer == "advisor") or (not advisor and viewer == "client")
        who = "Jair Ribeiro · Advisory" if advisor else client_name
        classes = "message mine" if own else "message"
        pieces.append(
            '<article class="' + classes + '">'
            '<div class="meta"><span class="who">' + _safe(
                "You · Advisor" if advisor and own else
                "You" if not advisor and own else who, 110
            ) + '</span>'
            '<time class="when">' + _safe(pretty_time(msg.get("created_at"))) +
            '</time></div>'
            '<div class="body">' + _safe(msg.get("body")) + '</div></article>'
        )
    if len(messages) >= limit:
        pieces.append('<p class="thread-footer">Showing the most recent ' +
                      str(limit) + ' messages.</p>')
    st.html(CSS + '<div class="ad-dialogue">' + "".join(pieces) + '</div>')
