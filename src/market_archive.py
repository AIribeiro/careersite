"""Immutable, reader-safe monthly AI/Data Market Observatory archive.

Rows are constructed at source-verification / editorial publication time.
Historical JobTech-only reconstructions never acquire evidence from a later
SCB/Brainville release by accident. This module cannot write archives.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from site_cms import _request_json, _rest_url


def _month_label(raw: str) -> str:
    day=date.fromisoformat(str(raw)[:10])
    return day.strftime("%B %Y")


def _validate_archive(item: dict) -> dict:
    kind=str(item.get("archive_kind") or "")
    points=item.get("observations")
    briefs=item.get("interpretations")
    if kind not in {"published_edition","retrospective_title_basket"}:
        raise ValueError("Unknown monthly research vintage.")
    if not isinstance(points,list) or not points or not isinstance(briefs,list):
        raise ValueError("Monthly archive is missing its frozen evidence.")
    codes=[p.get("code") for p in points]
    if not all(isinstance(c,str) and c for c in codes) or len(codes)!=len(set(codes)):
        raise ValueError("Monthly archive includes missing or duplicate evidence.")
    if kind=="retrospective_title_basket":
        if briefs or any(
            p.get("source_family")!="af_jobtech_target_demand"
            or p.get("period_complete") is not True
            or str(p.get("period_start"))[:7]!=str(item.get("month_start"))[:7]
            for p in points
        ):
            raise ValueError("Historical month contains later or unrelated research.")
    else:
        if not item.get("edition_slug") or len(briefs)<1:
            raise ValueError("Full edition requires a published interpretation set.")
        available=set(codes)
        for b in briefs:
            if not set(b.get("evidence_codes") or []).issubset(available):
                raise ValueError("Historical edition contains unsupported analysis.")
    return item


def load_market_archives(token: str) -> list[dict]:
    if not token:
        raise PermissionError("Verified Advisory member session required.")
    raw=_request_json(
        "GET",_rest_url(
          "portfolio_market_signal_monthly_archive?select=*&"
          "order=month_start.desc,first_published_at.desc&limit=150"
        ),
        token=token,timeout=15,
    )
    if not isinstance(raw,list) or len(raw)>150:
        raise RuntimeError("Monthly archive catalogue could not be verified.")
    result=[_validate_archive(item) for item in raw]
    if len({item["snapshot_key"] for item in result})!=len(result):
        raise ValueError("Repeated monthly archive identifier.")
    return result


def archive_option_label(item: dict) -> str:
    date_label=_month_label(item["month_start"])
    if item["archive_kind"]=="published_edition":
        return f"{date_label} · Full published edition"
    return f"{date_label} · Retrospective leadership archive"


def archive_coverage(item: dict) -> str:
    if item["archive_kind"]=="published_edition":
        return (
          f"Frozen published edition · {len(item['observations'])} approved "
          f"observations · {len(item['interpretations'])} executive analyses. "
          "Values remain as released even when current market data changes."
        )
    return (
      "Historical reconstruction using the narrow JobTech v1 title basket. "
      f"{len(item['observations'])} regional/national observations for the complete month, "
      "verified in November 2026. This was not a full AI/Data market edition "
      "published during the selected month. SCB adoption and consulting-market "
      "figures are intentionally absent."
    )
