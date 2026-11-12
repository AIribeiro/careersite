"""Real Chromium smoke: member identity persists across HTML anchor navigation."""
import re
from playwright.sync_api import sync_playwright, expect


def run():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        try:
            page = browser.new_page()
            page.goto("http://127.0.0.1:8515/?page=briefings",
                      wait_until="domcontentloaded", timeout=60000)
            expect(page.get_by_text("READER PAGE: briefings")).to_be_visible(
                timeout=30000
            )
            before = page.get_by_text(re.compile(r"MEMBER SESSION: [0-9a-f-]{36}"))
            expect(before).to_be_visible()
            identity = before.inner_text().split(": ", 1)[1]
            for target_id, route in [
                ("smoke-briefing-a", "briefing"),
                ("smoke-catalog", "briefings"),
                ("smoke-briefing-b", "briefing"),
                ("smoke-library", "readers"),
            ]:
                page.locator("#" + target_id).click()
                expect(page.get_by_text("READER PAGE: " + route)).to_be_visible(
                    timeout=20000
                )
                now = page.get_by_text(re.compile(r"MEMBER SESSION: [0-9a-f-]{36}"))
                expect(now).to_have_text("MEMBER SESSION: " + identity)
                print(target_id, route, "session retained")
        finally:
            browser.close()


if __name__ == "__main__":
    run()
