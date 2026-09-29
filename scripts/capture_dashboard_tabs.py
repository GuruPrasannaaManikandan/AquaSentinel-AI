from playwright.sync_api import sync_playwright
import time

def capture_tabs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})
        page.goto('http://127.0.0.1:8501', wait_until='networkidle')
        time.sleep(5)
        
        # Look for buttons or tab roles
        tabs = page.query_selector_all('button[role="tab"]') or page.query_selector_all('[role="tab"]')
        print('Found tabs with role=tab:', [t.inner_text() for t in tabs])
        
        # Print all metrics visible on initial render (Tab 1 is active by default in Streamlit)
        print('--- Active Tab Metrics ---')
        metrics = page.query_selector_all('[data-testid="stMetric"]')
        for m in metrics:
            print('  Metric:', m.inner_text().replace('\n', ' : '))
            
        page.screenshot(path='docs/dashboard_tab1_live.png', full_page=True)
        print('Saved docs/dashboard_tab1_live.png')
        
        # Click on Tab 3 (Evidential Decision & XAI)
        for t in tabs:
            if 'Decision' in t.inner_text() or 'XAI' in t.inner_text():
                print('Clicking tab:', t.inner_text())
                t.click()
                time.sleep(2)
                page.screenshot(path='docs/dashboard_tab3_decision.png', full_page=True)
                print('Saved docs/dashboard_tab3_decision.png')
                print('--- Tab 3 Metrics ---')
                metrics3 = page.query_selector_all('[data-testid="stMetric"]')
                for m in metrics3:
                    print('  Metric:', m.inner_text().replace('\n', ' : '))
                break

        browser.close()

if __name__ == '__main__':
    capture_tabs()
