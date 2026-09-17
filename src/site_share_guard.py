from __future__ import annotations

import streamlit.components.v1 as components


def inject_share_guard() -> None:
    """Keep article-share clicks out of generic contact/article-click metrics.

    Article analytics binds before this guard; generic analytics binds after it.
    The guard therefore allows the dedicated article event to be recorded, then
    stops subsequent generic document-level listeners without cancelling the
    link/button default action.
    """
    components.html(
        """
<script>
(() => {
  const win = window.parent;
  const doc = win.document;
  if (win.__jairArticleShareGuardBound) return;
  win.__jairArticleShareGuardBound = true;

  doc.addEventListener('click', event => {
    const el = event.target && event.target.closest
      ? event.target.closest('[data-hq-event]')
      : null;
    if (!el) return;
    const raw = String(el.dataset.hqEvent || '').toLowerCase();
    if (raw.startsWith('article_share_')) {
      event.stopImmediatePropagation();
    }
  }, true);
})();
</script>
""",
        height=0,
        width=0,
    )
