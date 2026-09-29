from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1200})
    page.goto('http://127.0.0.1:8501', wait_until='networkidle')
    page.wait_for_timeout(2000)
    page.locator("button[role='tab']:has-text('Optical & Temporal Intelligence')").click()
    page.wait_for_timeout(2000)
    page.screenshot(path='docs/DASHBOARD_LIVE_TAB2_FULL_VIEW.png', full_page=True)
    browser.close()
print('SUCCESS! Captured full Tab 2 view.')
