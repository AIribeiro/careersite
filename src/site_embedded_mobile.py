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
      site.style.zoom = String(scale);
      root.setAttribute("data-jr-masked-mobile", "true");
    } else {
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
    st.html(EMBEDDED_MOBILE_SCRIPT, unsafe_allow_javascript=True)


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
})();
</script>
"""


def mount_native_masked_mobile_fix() -> None:
    """Correct device-scale when native Streamlit forms load in a masked frame."""
    st.html(NATIVE_EMBEDDED_MOBILE_SCRIPT, unsafe_allow_javascript=True)
