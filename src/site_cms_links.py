from __future__ import annotations

from html.parser import HTMLParser
import re


AUTHOR_NAME = "Jair Ribeiro"
AUTHOR_HREF = "?page=impact"
AUTHOR_LINK = (
    '<a href="?page=impact" target="_self" '
    'data-hq-event="article_internal_impact">Jair Ribeiro</a>'
)
AUTHOR_SIGNATURE = f'<div class="article-signature">{AUTHOR_LINK}</div>'

# Phrase -> most relevant portfolio lens. The list is deliberately conservative:
# only phrases with a clear portfolio destination are auto-linked.
LINK_RULES = (
    (
        "?page=enterprise",
        "Enterprise AI & Data Leadership",
        "article_internal_enterprise",
        (
            "enterprise AI leadership",
            "enterprise AI",
            "AI strategy",
            "data and analytics",
            "data analytics",
            "data readiness",
            "agentic AI",
            "generative AI",
        ),
    ),
    (
        "?page=transformation",
        "AI Transformation & Adoption",
        "article_internal_transformation",
        (
            "AI transformation",
            "AI adoption",
            "digital transformation",
            "change management",
            "workflow redesign",
            "workforce redesign",
        ),
    ),
    (
        "?page=governance",
        "AI Governance & Operating Model",
        "article_internal_governance",
        (
            "AI governance",
            "Responsible AI",
            "responsible AI",
            "AI operating model",
            "operating model",
            "AI CoE",
            "center of excellence",
            "centre of excellence",
            "decision rights",
        ),
    ),
    (
        "?page=consulting",
        "Business-Driven AI & Consulting",
        "article_internal_consulting",
        (
            "business-driven AI",
            "business value",
            "AI value",
            "AI ROI",
            "portfolio value",
            "value realization",
            "use case portfolio",
        ),
    ),
)

_CONTEXT_EVENT_RE = re.compile(
    r'data-hq-event=["\']article_internal_(?:enterprise|transformation|governance|consulting)["\']',
    flags=re.I,
)
_SIGNATURE_CLASS_RE = re.compile(r'class=["\'][^"\']*\barticle-signature\b[^"\']*["\']', flags=re.I)
_FINAL_AUTHOR_LINK_RE = re.compile(
    r'<a\b[^>]*>\s*Jair Ribeiro\s*</a>(?=\s*(?:</[^>]+>\s*)*$)',
    flags=re.I,
)
_FINAL_AUTHOR_TEXT_RE = re.compile(
    r'Jair Ribeiro(?=\s*(?:</[^>]+>\s*)*$)',
    flags=re.I,
)


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])",
        flags=re.I,
    )


class _CandidateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.anchor_depth = 0
        self.context_depth = 0
        self.position = 0
        self.matches: list[tuple[int, int, int, str, str, str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        name = tag.lower()
        if name == "a":
            self.anchor_depth += 1
        if name in {"p", "li"}:
            self.context_depth += 1

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name == "a":
            self.anchor_depth = max(0, self.anchor_depth - 1)
        if name in {"p", "li"}:
            self.context_depth = max(0, self.context_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.anchor_depth == 0 and self.context_depth > 0:
            for rule_index, (href, title, event, phrases) in enumerate(LINK_RULES):
                for phrase_index, phrase in enumerate(phrases):
                    match = _phrase_pattern(phrase).search(data)
                    if match:
                        # Earlier occurrence wins; for the same position prefer the
                        # longer/more specific phrase, then rule order.
                        self.matches.append(
                            (
                                self.position + match.start(),
                                -len(phrase),
                                rule_index * 100 + phrase_index,
                                phrase,
                                href,
                                title,
                                event,
                            )
                        )
        self.position += len(data)


def _select_phrases(value: str, limit: int) -> list[tuple[str, str, str, str]]:
    if limit <= 0:
        return []

    parser = _CandidateParser()
    parser.feed(value)
    candidates = sorted(parser.matches, key=lambda item: (item[0], item[1], item[2]))

    selected: list[tuple[str, str, str, str]] = []
    used_phrases: set[str] = set()
    used_destinations: set[str] = set()

    # First pass: diversify destinations so two links add navigation value.
    for _position, _specificity, _priority, phrase, href, title, event in candidates:
        phrase_key = phrase.casefold()
        if phrase_key in used_phrases or href in used_destinations:
            continue
        selected.append((phrase, href, title, event))
        used_phrases.add(phrase_key)
        used_destinations.add(href)
        if len(selected) >= limit:
            return selected

    # Second pass: if the article is strongly about one lens, allow another phrase
    # to the same destination rather than inventing a weak match.
    for _position, _specificity, _priority, phrase, href, title, event in candidates:
        phrase_key = phrase.casefold()
        if phrase_key in used_phrases:
            continue
        selected.append((phrase, href, title, event))
        used_phrases.add(phrase_key)
        if len(selected) >= limit:
            break

    return selected


class _LinkingParser(HTMLParser):
    def __init__(self, selected: list[tuple[str, str, str, str]]) -> None:
        super().__init__(convert_charrefs=False)
        self.selected = {
            phrase.casefold(): (phrase, href, title, event)
            for phrase, href, title, event in selected
        }
        self.anchor_depth = 0
        self.context_depth = 0
        self.output: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        raw = self.get_starttag_text() or f"<{tag}>"
        self.output.append(raw)
        name = tag.lower()
        if name == "a":
            self.anchor_depth += 1
        if name in {"p", "li"}:
            self.context_depth += 1

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.output.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_endtag(self, tag: str) -> None:
        self.output.append(f"</{tag}>")
        name = tag.lower()
        if name == "a":
            self.anchor_depth = max(0, self.anchor_depth - 1)
        if name in {"p", "li"}:
            self.context_depth = max(0, self.context_depth - 1)

    def handle_entityref(self, name: str) -> None:
        self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.output.append(f"&#{name};")

    def handle_data(self, data: str) -> None:
        if self.anchor_depth or self.context_depth == 0 or not self.selected:
            self.output.append(data)
            return

        working = data
        parts: list[str] = []
        while self.selected:
            best = None
            for key, (phrase, href, title, event) in self.selected.items():
                match = _phrase_pattern(phrase).search(working)
                if match is None:
                    continue
                rank = (match.start(), -len(phrase))
                if best is None or rank < best[0]:
                    best = (rank, key, match, href, title, event)

            if best is None:
                break

            _rank, key, match, href, title, event = best
            parts.append(working[: match.start()])
            label = working[match.start() : match.end()]
            parts.append(
                f'<a href="{href}" target="_self" title="{title}" '
                f'data-hq-event="{event}">{label}</a>'
            )
            working = working[match.end() :]
            self.selected.pop(key, None)

        parts.append(working)
        self.output.append("".join(parts))

    def handle_comment(self, data: str) -> None:
        self.output.append(f"<!--{data}-->")

    def html(self) -> str:
        return "".join(self.output)


def ensure_author_signature(value: str) -> str:
    html = (value or "").strip()
    if not html:
        return AUTHOR_SIGNATURE

    if _SIGNATURE_CLASS_RE.search(html):
        return html

    # Normalize an existing author link at the very end to the canonical
    # Leadership Impact destination.
    if _FINAL_AUTHOR_LINK_RE.search(html):
        return _FINAL_AUTHOR_LINK_RE.sub(AUTHOR_LINK, html, count=1)

    # If the author name already closes the article, link it in place.
    if _FINAL_AUTHOR_TEXT_RE.search(html):
        return _FINAL_AUTHOR_TEXT_RE.sub(AUTHOR_LINK, html, count=1)

    return html + AUTHOR_SIGNATURE


def enrich_article_html(value: str, max_context_links: int = 2) -> str:
    """Add two relevant portfolio cross-links and a linked Jair Ribeiro signature.

    The function is intentionally idempotent: re-saving an article will not keep
    adding links, and existing anchors are never rewritten or nested.
    """
    html = (value or "").strip()
    existing = len(_CONTEXT_EVENT_RE.findall(html))
    remaining = max(0, max_context_links - existing)

    if remaining:
        selected = _select_phrases(html, remaining)
        if selected:
            parser = _LinkingParser(selected)
            parser.feed(html)
            html = parser.html()

    return ensure_author_signature(html)
