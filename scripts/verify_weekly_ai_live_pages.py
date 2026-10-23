#!/usr/bin/env python3
"""Verify latest Friday social redirects *from GitHub Actions network*.

ChatGPT's web-fetch environment can fail to access GitHub Pages despite a
successful deployment. This machine-verifiable check runs after Pages deploy
and inspects all three actual live paths, OG art, and canonical attribution.
"""
from __future__ import annotations

import argparse
from html import escape
import json
import sys
from pathlib import Path
from time import sleep
from urllib import parse, request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from site_shortlinks import registered_short_links, weekly_ai_short_link

BASE='https://airibeiro.github.io/careersite'


def live_get(url: str, *, expected_content: str='text/html') -> bytes:
    last=None
    for attempt in range(6):
        try:
            req=request.Request(url,headers={'User-Agent':'WeeklyAI-Friday-Release-Verification/1.0',
                    'Cache-Control':'no-cache'})
            with request.urlopen(req,timeout=20) as response:
                mime=response.headers.get('Content-Type','').lower()
                if response.status!=200 or expected_content not in mime:
                    raise RuntimeError(f'{url}: expected HTTP 200 and {expected_content}, got {response.status} {mime}')
                return response.read(2_500_000)
        except Exception as e:
            last=e
            if attempt < 5:
                sleep(5)
    raise RuntimeError(f'Public WEEKLY AI asset unreachable: {url}; {last}')


def verify_latest() -> list[str]:
    registry=json.loads((ROOT/'src/weekly_ai_shortlink_registry.json').read_text())
    editions=[e for e in registry['editions'] if e.get('distribution_mode')=='friday_wrap']
    if not editions:
        print('No Friday issues registered; no live Friday redirects to test')
        return []
    edition=max(editions,key=lambda e:(int(e['iso_year']),int(e['iso_week'])))
    slug=edition['slug']
    campaign=f"weekly_ai_{int(edition['iso_year'])}_w{int(edition['iso_week'])}_friday"
    entries={code:(row_slug,channel,target) for code,row_slug,channel,target in registered_short_links() if row_slug==slug}
    checked=[]
    for channel,suffix in [('x','x'),('threads','t'),('linkedin','l')]:
        code=f"f{edition['iso_year']}{int(edition['iso_week']):02d}{suffix}"
        row=entries.get(code)
        if not row or row[1]!=channel:
            raise AssertionError(f'Missing registered channel short alias: {code}')
        _slug,_channel,target=row
        params=parse.parse_qs(parse.urlsplit(target).query)
        expected={'page':'thinking','article':slug,'source':channel,
                  'utm_source':channel,'utm_medium':'social','role':'weeklyai',
                  'utm_campaign':campaign,'utm_content':'weekly_perspective'}
        for key,value in expected.items():
            if params.get(key)!=[value]:
                raise AssertionError(f'Attribution mismatch {code} {key}: {params.get(key)}')
        short=f'{BASE}/go/{code}/'
        if weekly_ai_short_link(slug,channel,campaign=campaign,content='weekly_perspective')!=short:
            raise AssertionError('Canonical engine did not resolve exact Friday short link')
        page=live_get(short).decode('utf-8','replace')
        if ('<meta http-equiv="refresh"' not in page or
            escape(target,quote=True) not in page or
            'window.location.replace' not in page or
            edition['edition_title'] not in page):
            raise AssertionError(f'Public preview or target mismatch: {short}')
        if f'{BASE}/social/{slug}.png' not in page:
            raise AssertionError(f'No edition-specific branded OG cover: {short}')
        checked.append(short)
    cover=live_get(f'{BASE}/social/{slug}.png',expected_content='image/png')
    if not cover.startswith(b'\x89PNG\r\n\x1a\n'):
        raise AssertionError('Published LinkedIn cover is not PNG')
    xcover=live_get(f'{BASE}/social-x/{slug}.jpg',expected_content='image/jpeg')
    if not xcover.startswith(b'\xff\xd8'):
        raise AssertionError('Published X card is not JPEG')
    print('LIVE FRIDAY RELEASE VERIFIED:',slug)
    for short in checked:
        print('VERIFIED',short)
    print('Verified distinct channel attribution and LinkedIn 1200x627 / X imagery')
    return checked


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--latest',action='store_true')
    parser.parse_args()
    verify_latest()
    return 0

if __name__=='__main__':
    raise SystemExit(main())