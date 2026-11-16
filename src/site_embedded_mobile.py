"""Narrow-device fallback for sites embedded in a legacy masked URL-forwarding frame.

A masking provider can omit <meta name="viewport"> on its *outer* document.
That makes the child iframe approximately 980 CSS pixels wide on a 390 px
phone, preventing the portfolio's existing max-width breakpoints from firing.

This module cannot modify the parent page (the browser correctly blocks it).
Instead it reuses existing mobile CSS at the physical device-width breakpoint
and, only for embedded mobile sessions with an oversized layout viewport,
adjusts the portfolio's visual scale to fit the actual screen.

It is intentionally a presentation fallback, not a solution for third-party
cookies, authentication callbacks, SEO, or canonical article URLs.
"""

from __future__ import annotations

from functools import lru_cache
import re

import streamlit as st


_SIMPLE_MAX_WIDTH = re.compile(
    r"@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)\s*\{",
    flags=re.IGNORECASE,
)


@lru_cache(maxsize=8)
def support_masked_mobile_media(css: str) -> str:
    """Reuse existing phone breakpoints when an outer iframe reports 980px.

    A browser inside a masking frame can report a desktop *layout* width
    while correctly reporting a phone-sized *device* width. Adding a second
    media-condition is intentionally no-op for normally responsive pages.
    """
    return _SIMPLE_MAX_WIDTH.sub(
        lambda match: (
            "@media(max-width:" + match.group(1) + "px), "
            "(max-device-width:" + match.group(1) + "px){"
        ),
        css,
    )


# A URL-masking outer frame without a viewport meta tag can give an
# iPhone iframe a 980px CSS layout while scaling it down to the screen.
# Keep a scoped no-JavaScript fallback for this combination. Normal mobile
# viewports and desktop displays do not match.
MASKED_FRAME_FALLBACK_CSS = r"""
<style>
@media screen and (min-width:760px) and (max-device-width:700px) {
  .site:not(.native-shell):not(.reader-shell) {zoom:2.5}
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:2.5}
}
@media screen and (min-width:760px) and (max-device-width:359px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:2.9}
}
@media screen and (min-width:760px) and (min-device-width:360px) and (max-device-width:375px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:2.65}
}
@media screen and (min-width:760px) and (min-device-width:401px) and (max-device-width:430px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:2.36}
}
@media screen and (min-width:760px) and (min-device-width:431px) and (max-device-width:480px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:2.14}
}
@media screen and (min-width:760px) and (min-device-width:481px) and (max-device-width:600px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:1.8}
}
@media screen and (min-width:760px) and (min-device-width:601px) and (max-device-width:700px) {
  .site:not(.native-shell):not(.reader-shell),
  [data-testid="stAppViewContainer"]:has(.native-shell-header, .reader-shell) {zoom:1.48}
}
</style>
"""

EMBEDDED_MOBILE_SCRIPT = r"""
<script>
(function () {
  "use strict";
  // Run once per browser document but recheck after Streamlit page rerenders.
  function applyMaskedMobileFix() {
    var root = document.documentElement;
    var site = document.querySelector(".site");
    if (!site) return;

    var framed = false;
    try { framed = (window.self !== window.top); }
    catch (_error) { framed = true; }

    var deviceWidth = Number(window.screen && window.screen.width) || 0;
    var layoutWidth = Number(window.innerWidth) || 0;
    var needsFix = framed &&
      deviceWidth >= 280 && deviceWidth <= 720 &&
      layoutWidth >= 760 && layoutWidth > deviceWidth * 1.45;

    if (needsFix) {
      // A typical non-responsive outer wrapper creates a 980px iframe on a
      // 390px phone. CSS zoom reduces the available CSS layout width, while
      // enlarging the content back to an ordinary mobile-readable scale.
      var scale = Math.min(3.5, layoutWidth / deviceWidth);
      // zoom changes the layout width available to an auto-sized element.
      // Without an explicit phone-width canvas the Advisory two-column grid
      // can collapse into narrow slivers and the header links spill sideways.
      // Match the working native-form adapter: size first, then zoom.
      site.style.setProperty("width", deviceWidth + "px", "important");
      site.style.setProperty("min-width", "0", "important");
      site.style.setProperty("max-width", "none", "important");
      site.style.zoom = String(scale);
      root.setAttribute("data-jr-masked-mobile", "true");
    } else {
      site.style.removeProperty("width");
      site.style.removeProperty("min-width");
      site.style.removeProperty("max-width");
      site.style.removeProperty("zoom");
      root.removeAttribute("data-jr-masked-mobile");
    }
  }

  if (!window.__jrMaskedMobileFix) {
    window.__jrMaskedMobileFix = applyMaskedMobileFix;
    window.addEventListener("resize", applyMaskedMobileFix, {passive: true});
    window.addEventListener("orientationchange", applyMaskedMobileFix);
  }
  window.__jrMaskedMobileFix();
})();
</script>
"""


def mount_masked_mobile_fix() -> None:
    """Mount only for public pages, after the portfolio HTML has been emitted."""
    # Render styling independently so the fallback survives blocked scripts.
    st.html(MASKED_FRAME_FALLBACK_CSS)
    st.html(EMBEDDED_MOBILE_SCRIPT, unsafe_allow_javascript=True)



# Streamlit 1.64 renders st.dialog in a React Aria modal portal rather than as
# a child of the portfolio .site element. Scaling .site in a masked iframe
# therefore leaves the login dialog unreadably small. Target only the Reader
# dialogs (marked in their body), and scale the *panel* rather than the fixed
# overlay so the backdrop and scroll behavior remain intact.
READER_DIALOG_MOBILE_CSS = r"""
<style>
@media (max-width:700px), (max-device-width:700px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {
    box-sizing:border-box!important;
    padding:8px 0 max(10px,env(safe-area-inset-bottom))!important;
    align-items:flex-start!important;
    overflow-y:auto!important;
    -webkit-overflow-scrolling:touch;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) > div {
    box-sizing:border-box!important;
    width:calc(100vw - 24px)!important;
    max-width:calc(100vw - 24px)!important;
    min-width:0!important;
    margin:8px auto!important;
    border-radius:10px!important;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [role="dialog"] {
    box-sizing:border-box;min-width:0!important;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) h3 {
    font-size:clamp(21px,5.8vw,27px)!important;
    line-height:1.17!important;
    overflow-wrap:anywhere;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) h2,
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) p,
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) label {
    overflow-wrap:anywhere;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [data-testid="stForm"],
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [data-testid="stTextInput"] {
    box-sizing:border-box;min-width:0;max-width:100%;width:100%;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) input {
    box-sizing:border-box;max-width:100%;min-height:44px;
    font-size:16px!important;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [data-testid="stRadio"] [role="radiogroup"] {
    flex-wrap:wrap!important;row-gap:8px;column-gap:14px;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [data-testid="stFormSubmitButton"] button,
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) [data-testid="stButton"] button {
    min-height:44px;white-space:normal!important;
  }
}
/* The outer URL-masking document may omit viewport metadata. The iframe then
   gets a 980px CSS canvas on a real phone. This is a CSS-only fallback; when
   JavaScript is permitted it sets the exact zoom and panel width. */
@media screen and (min-width:760px) and (max-device-width:700px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {
    --jr-dialog-zoom:2.5;--jr-dialog-width:366px;
  }
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) > div {
    zoom:var(--jr-dialog-zoom)!important;
    width:var(--jr-dialog-width)!important;
    max-width:var(--jr-dialog-width)!important;
    margin:8px auto!important;
  }
}
@media screen and (min-width:760px) and (max-device-width:359px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:2.9;--jr-dialog-width:320px}
}
@media screen and (min-width:760px) and (min-device-width:360px) and (max-device-width:375px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:2.65;--jr-dialog-width:345px}
}
@media screen and (min-width:760px) and (min-device-width:401px) and (max-device-width:430px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:2.36;--jr-dialog-width:404px}
}
@media screen and (min-width:760px) and (min-device-width:431px) and (max-device-width:480px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:2.14;--jr-dialog-width:450px}
}
@media screen and (min-width:760px) and (min-device-width:481px) and (max-device-width:600px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:1.8;--jr-dialog-width:520px}
}
@media screen and (min-width:760px) and (min-device-width:601px) and (max-device-width:700px) {
  [data-testid="stDialog"]:has(.jr-reader-dialog-marker) {--jr-dialog-zoom:1.48;--jr-dialog-width:630px}
}
</style>
"""

READER_DIALOG_MOBILE_SCRIPT = r"""
<script>
(function () {
  "use strict";
  function adaptReaderDialog() {
    const overlay = document.querySelector('[data-testid="stDialog"]:has(.jr-reader-dialog-marker)');
    if (!overlay) return;
    // Streamlit 1.64: fixed React Aria overlay > modal panel > [role=dialog].
    const panel = overlay.querySelector(':scope > div') ||
      overlay.querySelector('[role="dialog"]')?.parentElement;
    if (!panel) return;

    let framed = false;
    try { framed = window.self !== window.top; }
    catch (_error) { framed = true; }
    const physical = Number(window.screen && window.screen.width) || 0;
    const layout = Number(window.innerWidth) || 0;
    const masked = framed && physical >= 280 && physical <= 720 &&
      layout >= 760 && layout > physical * 1.45;
    if (masked) {
      const ratio = Math.min(3.5, layout / physical);
      const available = Math.max(240, physical - 24);
      // The overlay stays fixed at viewport size. Only its panel grows to
      // phone-readable scale; the panel remains centered and scrollable.
      panel.style.setProperty('zoom', String(ratio), 'important');
      panel.style.setProperty('width', available + 'px', 'important');
      panel.style.setProperty('max-width', available + 'px', 'important');
      panel.style.setProperty('min-width', '0', 'important');
      overlay.setAttribute('data-jr-reader-modal-mobile', 'masked');
    } else {
      panel.style.removeProperty('zoom');
      panel.style.removeProperty('width');
      panel.style.removeProperty('max-width');
      panel.style.removeProperty('min-width');
      overlay.removeAttribute('data-jr-reader-modal-mobile');
    }
  }
  if (!window.__jrReaderDialogMobileFix) {
    window.__jrReaderDialogMobileFix = adaptReaderDialog;
    window.addEventListener('resize', adaptReaderDialog, {passive:true});
    window.addEventListener('orientationchange', adaptReaderDialog);
    // Dialogs can re-mount after a Streamlit fragment rerun. The observer
    // only watches child changes, avoiding loops from style updates.
    const observer = new MutationObserver(adaptReaderDialog);
    observer.observe(document.documentElement, {childList:true,subtree:true});
  }
  window.__jrReaderDialogMobileFix();
})();
</script>
"""


def mount_reader_dialog_mobile_fix() -> None:
    """Present the Reader login modal at readable phone size, including masking."""
    st.html(
        READER_DIALOG_MOBILE_CSS +
        '<span class="jr-reader-dialog-marker" aria-hidden="true" '
        'style="display:none"></span>'
    )
    st.html(READER_DIALOG_MOBILE_SCRIPT, unsafe_allow_javascript=True)


NATIVE_EMBEDDED_MOBILE_SCRIPT = r"""
<script>
(function () {
  "use strict";
  // Streamlit's native forms are siblings of the branded HTML rather than
  // children of .site; zooming .site alone cannot fix the password inputs.
  function adjustNativeLayout() {
    var app = document.querySelector('[data-testid="stAppViewContainer"]');
    if (!app || !(document.querySelector('.native-shell-header') || document.querySelector('.reader-shell'))) return;

    var framed = false;
    try { framed = window.self !== window.top; }
    catch (_error) { framed = true; }

    var physical = Number(window.screen && window.screen.width) || 0;
    var viewport = Number(window.innerWidth) || 0;
    var oversizedFrame =
      framed && physical >= 280 && physical <= 720 &&
      viewport >= 760 && viewport > physical * 1.45;
    if (oversizedFrame) {
      // An outer frame missing viewport metadata can appear 980 CSS px wide
      // on a 390 px phone. The browser shrinks everything to desktop size.
      // Give the entire Streamlit app a phone-sized layout canvas and zoom
      // it back to readable physical size, INCLUDING native form controls.
      var ratio = Math.min(3.5, viewport / physical);
      app.style.setProperty('width', physical + 'px', 'important');
      app.style.setProperty('min-width', '0', 'important');
      app.style.setProperty('max-width', physical + 'px', 'important');
      app.style.zoom = String(ratio);
      document.documentElement.setAttribute('data-jr-native-masked-mobile','true');
    } else {
      app.style.removeProperty('width');
      app.style.removeProperty('min-width');
      app.style.removeProperty('max-width');
      app.style.removeProperty('zoom');
      document.documentElement.removeAttribute('data-jr-native-masked-mobile');
    }
  }

  if (!window.__jrNativeMobileFix) {
    window.__jrNativeMobileFix = adjustNativeLayout;
    window.addEventListener('resize', adjustNativeLayout, {passive:true});
    window.addEventListener('orientationchange', adjustNativeLayout);
  }
  window.__jrNativeMobileFix();
  // Streamlit may mount native forms and the portfolio shell after this
  // script is inserted. Apply once when those elements become available.
  const ready = () => !!document.querySelector('[data-testid="stAppViewContainer"]') &&
    !!(document.querySelector('.native-shell-header') || document.querySelector('.reader-shell'));
  if (!ready() && !window.__jrNativeMobileObserver) {
    const observer = new MutationObserver(() => {
      if (!ready()) return;
      observer.disconnect();
      window.__jrNativeMobileObserver = null;
      window.__jrNativeMobileFix();
    });
    window.__jrNativeMobileObserver = observer;
    observer.observe(document.documentElement, {childList:true, subtree:true});
  }
})();
</script>
"""


def mount_native_masked_mobile_fix() -> None:
    """Correct device-scale when native Streamlit forms load in a masked frame."""
    # Native forms need the same scaling even when scripts cannot execute.
    st.html(MASKED_FRAME_FALLBACK_CSS)
    st.html(NATIVE_EMBEDDED_MOBILE_SCRIPT, unsafe_allow_javascript=True)
