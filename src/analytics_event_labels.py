"""Plain-language names for recorded activity, without changing event keys."""

EVENT_LABELS = {
    "page_view": "Pages opened",
    "article_view": "Articles opened",
    "impact_view": "Experience page opened",
    "lens_view": "Role perspectives explored",
    "cv_download": "CV downloads",
    "email_click": "Email links clicked",
    "linkedin_click": "LinkedIn links clicked",
    "article_click": "Article links clicked",
    "article_card_click": "Article previews clicked",
    "article_share": "Article share actions",
    "article_share_copy": "Article links copied",
    "article_share_email": "Email share selected",
    "article_share_linkedin": "LinkedIn share selected",
    "article_share_x": "X share selected",
    "engagement_ping": "Active browsing checks",
    "element_impression": "Links and cards seen",
    "cta_click": "Action buttons clicked",
    "navigation_click": "Navigation links clicked",
    "section_view": "Page sections reached",
    "performance_metric": "Page performance checks",
    "section_attention": "Section attention measured",
    "element_attention": "Link and card attention measured",
    "cta_hesitation": "Pauses near action buttons",
    "scroll_abandonment": "Scrolling stops recorded",
    "ux_signal": "Browsing experience signals",
    "first_interaction": "First interactions recorded",
    "behavior_summary": "Browsing summaries recorded",
    "audio_start": "Audio playback started",
    "audio_progress": "Listening progress recorded",
    "audio_complete": "Audio playback completed",
}


def event_label(value: object) -> str:
    key = str(value or "").strip()
    return EVENT_LABELS.get(key, key.replace("_", " ").replace("-", " ").capitalize() or "Other activity")
