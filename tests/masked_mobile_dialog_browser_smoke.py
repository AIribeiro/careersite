"""Real Chromium geometry checks for Streamlit's external modal portal.

Test a normal mobile viewport and a mobile browser with an outer document
missing a viewport meta tag, as can happen with registrar URL masking.
The app is synthetic; no real accounts or auth tokens are involved.
"""
from __future__ import annotations

from playwright.sync_api import expect, sync_playwright


APP_URL = "http://127.0.0.1:8518/"
MEASURE = r"""
() => {
  const overlay = document.querySelector('[data-testid="stDialog"]');
  const panel = overlay?.querySelector(':scope > div');
  const input = overlay?.querySelector('input');
  if (!overlay || !panel || !input) return null;
  const rect = panel.getBoundingClientRect();
  return {
    physical: window.screen.width,
    layout: window.innerWidth,
    framed: window.self !== window.top,
    panelRenderedWidth: rect.width,
    panelZoom: Number(getComputedStyle(panel).zoom || 1),
    panelInlineZoom: panel.style.zoom || "",
    inputHeight: input.getBoundingClientRect().height,
    overlayOverflowY: getComputedStyle(overlay).overflowY,
    titlePresent: !!overlay.querySelector("h3"),
  };
}
"""


def inspect(page_or_frame, label: str, masked: bool) -> None:
    overlay = page_or_frame.locator('[data-testid="stDialog"]')
    expect(overlay).to_be_visible(timeout=30000)
    expect(page_or_frame.get_by_text("Explore the complete executive briefing")).to_be_visible()
    metrics = page_or_frame.evaluate(MEASURE)
    assert metrics is not None, label + ": modal/input missing"
    print(label + ": " + str(metrics), flush=True)
    assert metrics["titlePresent"], label + ": missing dialog heading"
    assert metrics["physical"] <= 430, label + ": expected phone screen"
    assert metrics["inputHeight"] >= 40, label + ": input unusably small"
    # The modal must occupy most, but not more than, the available layout
    # width. This catches a desktop-scale 920px modal in a 980px iframe.
    ratio = metrics["panelRenderedWidth"] / metrics["layout"]
    assert 0.78 <= ratio <= 1.01, (
        label + ": panel not phone-sized; width/viewport=" + str(ratio)
    )
    assert metrics["overlayOverflowY"] in ("auto", "scroll"), (
        label + ": dialog cannot scroll on short phones"
    )
    if masked:
        assert metrics["framed"], label + ": expected an iframe"
        assert metrics["layout"] >= 760, label + ": expected desktop iframe canvas"
        assert metrics["panelZoom"] >= 1.45, (
            label + ": dialog is still at desktop-scale despite article zoom"
        )
    else:
        assert metrics["layout"] <= 430, label + ": direct mobile viewport should be narrow"
        assert metrics["panelZoom"] <= 1.05, (
            label + ": regular mobile dialog was magnified unnecessarily"
        )


def run() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context(
                viewport={"width":390, "height":844},
                screen={"width":390, "height":844},
                is_mobile=True,
                has_touch=True,
                device_scale_factor=2,
            )
            direct = context.new_page()
            direct.goto(APP_URL, wait_until="domcontentloaded", timeout=60000)
            inspect(direct, "Direct iPhone viewport", masked=False)

            framed_page = context.new_page()
            # Deliberately omit the OUTER viewport tag, simulating the URL
            # masking provider's document. The inner Streamlit app has its own.
            framed_page.set_content(
                '<!doctype html><html><head><title>Masked URL</title></head>'
                '<body style="margin:0"><iframe src="' + APP_URL +
                '" style="display:block;width:100%;height:1300px;border:0">'
                '</iframe></body></html>'
            )
            inner = framed_page.frame_locator("iframe")
            expect(inner.locator('[data-testid="stDialog"]')).to_be_visible(
                timeout=30000
            )
            actual_frame = next(
                f for f in framed_page.frames
                if f is not framed_page.main_frame and "127.0.0.1:8518" in f.url
            )
            inspect(actual_frame, "Masked iPhone iframe", masked=True)
        finally:
            browser.close()


if __name__ == "__main__":
    run()
