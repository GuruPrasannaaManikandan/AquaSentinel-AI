from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1200})
    page.goto('http://127.0.0.1:8501', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    # Capture Tab 3
    page.locator("button[role='tab']:has-text('Evidential Decision & XAI')").click()
    page.wait_for_timeout(1500)
    page.screenshot(path='docs/DASHBOARD_LIVE_TAB3_XAI.png', full_page=True)
    
    # Capture Tab 5 (Alerts)
    page.locator("button[role='tab']:has-text('Alert History & Event Store')").click()
    page.wait_for_timeout(1500)
    page.screenshot(path='docs/DASHBOARD_LIVE_TAB5_ALERTS.png', full_page=True)

    browser.close()
print('SUCCESS! Captured Tab 3 and Tab 5 views.')
