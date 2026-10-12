"""Anonymous, read-only Supabase request headers for public Analytics.

Never use CMS credentials here or send private refresh/access tokens. The
Postgres EXECUTE grants apply only to aggregate reporting RPCs.
"""
from __future__ import annotations

import json
from urllib import error, request

from site_analytics import ANALYTICS_PUBLISHABLE_KEY, ANALYTICS_URL


def public_analytics_rpc_headers() -> dict[str,str]:
    return {
        "apikey": ANALYTICS_PUBLISHABLE_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_public_analytics_rpc(name: str, payload: dict | None = None) -> dict:
    if name not in ("careersite_public_job_summary_v1",
                    "careersite_public_market_summary_v1",
                    "careersite_public_hiring_inputs_v1",
                    "careersite_public_market_history_v1"):
        raise ValueError("Not an approved public summary.")
    req = request.Request(
        f"{ANALYTICS_URL.rstrip('/')}/rest/v1/rpc/{name}",
        data=json.dumps(payload or {}).encode("utf-8"),
        method="POST", headers=public_analytics_rpc_headers(),
    )
    try:
        with request.urlopen(req,timeout=18) as response:
            result=json.load(response)
    except (error.HTTPError,error.URLError,TimeoutError) as exc:
        raise RuntimeError(f"{name} is temporarily unavailable.") from exc
    if not isinstance(result,dict):
        raise RuntimeError("Unexpected anonymous reporting response.")
    if name == "careersite_public_job_summary_v1":
        # Both Swedish Market correlations and Job Search charts require
        # date+metric OBJECTS. An earlier SQL alias collision returned date
        # strings and crashed both dashboards.
        required=("applications","responses","interviews","rejections")
        for grain,date_key in (("daily","d"),("weekly","week")):
            rows=result.get(grain)
            if not isinstance(rows,list) or any(
                not isinstance(row,dict)
                or not isinstance(row.get(date_key),str)
                or any(
                    not isinstance(row.get(metric),(int,float))
                    or isinstance(row.get(metric),bool)
                    for metric in required
                )
                for row in rows
            ):
                raise RuntimeError(
                    f"Invalid public job-search {grain} response schema. "
                    "The source report is temporarily unavailable."
                )
    return result
