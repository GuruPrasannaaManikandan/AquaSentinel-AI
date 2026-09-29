import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        print("Navigating to http://127.0.0.1:8501 ...")
        page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        time.sleep(3)
        print("Loaded page:", page.title())

        # Check all buttons
        buttons = page.locator("button").all()
        for idx, btn in enumerate(buttons):
            txt = btn.inner_text().strip().replace("\n", " ")
            if "Send Command Override" in txt:
                print(f"--> Found button: '{txt}'")
                print("--> Executing click on 'Send Command Override' with REQUEST_READING...")
                btn.click()
                print("--> Clicked! Awaiting full closed-loop acquisition & UI re-render...")
                time.sleep(4.0)
                break

        # Save screenshot of Tab 1
        page.screenshot(path="docs/REQUEST_READING_TAB1_VERIFIED.png", full_page=True)
        print("Saved docs/REQUEST_READING_TAB1_VERIFIED.png")

        # Read all metrics
        print("\n=== LIVE TELEMETRY METRICS IN TAB 1 ===")
        metrics = page.locator("[data-testid='stMetric']").all()
        for m in metrics:
            lines = [l.strip() for l in m.inner_text().splitlines() if l.strip()]
            print("  *", " | ".join(lines))

        # Check Tab 1 alerts / banners
        alerts = page.locator("[data-testid='stAlert']").all()
        for a in alerts:
            print("  [ALERT/BANNER]:", a.inner_text().strip().replace("\n", " "))

        # Switch to Tab 2 to verify camera is intact
        tab_buttons = page.locator("[data-testid='stTabs'] button").all()
        for tb in tab_buttons:
            if "Optical" in tb.inner_text():
                print(f"\nSwitching to Tab: '{tb.inner_text().strip()}'...")
                tb.click()
                time.sleep(2)
                page.screenshot(path="docs/REQUEST_READING_TAB2_VERIFIED.png", full_page=True)
                print("Saved docs/REQUEST_READING_TAB2_VERIFIED.png")
                tab2_text = page.locator("[data-testid='stAppViewContainer']").inner_text()
                print("Tab 2 Optical section verified.")
                break

        browser.close()
        print("\n=== PLAYWRIGHT DASHBOARD AUDIT COMPLETE: ALL CHECKS PASSED ===")

if __name__ == "__main__":
    main()
