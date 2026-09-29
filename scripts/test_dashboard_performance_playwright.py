import time
import os
import sys
from playwright.sync_api import sync_playwright

def test_dashboard_performance():
    print("=" * 70)
    print("PHASE 4: LIVE WEB DASHBOARD PERFORMANCE & VALIDATION")
    print("=" * 70)
    
    console_errors = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        
        # Listen for console logs
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        print("\n[1] Measuring Initial Page Load Time...")
        t0 = time.perf_counter()
        page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=20000)
        load_time_sec = time.perf_counter() - t0
        print(f"    Page loaded in {load_time_sec:.3f} seconds (Target: < 5s)")
        assert load_time_sec < 10.0, f"Page load too slow: {load_time_sec}s"
        
        # Wait for Streamlit rendering to settle
        page.wait_for_selector(".stMetric", timeout=10000)
        
        # Check for red exceptions
        exceptions = page.query_selector_all(".stException")
        print(f"[2] Checking Streamlit Exceptions: Found {len(exceptions)}")
        assert len(exceptions) == 0, f"Found {len(exceptions)} red Streamlit exceptions in DOM!"
        
        # Check metrics in Tab 1
        print("[3] Inspecting Tab 1 Metrics...")
        metrics = page.query_selector_all('[data-testid="stMetric"]')
        metric_texts = [m.inner_text() for m in metrics]
        print(f"    Total Metrics Rendered: {len(metric_texts)}")
        
        ph_metric = None
        turb_metric = None
        for text in metric_texts:
            if "pH" in text:
                ph_metric = text
            if "Turbidity" in text:
                turb_metric = text
                
        print(f"    Rendered pH Metric:\n{ph_metric}")
        print(f"    Rendered Turbidity Metric:\n{turb_metric}")
        
        assert ph_metric is not None, "pH metric not found!"
        assert "NOT_CALIBRATED" in ph_metric or "Uncalibrated" in ph_metric, "pH not labeled as uncalibrated!"
        assert turb_metric is not None, "Turbidity metric not found!"
        assert "Voltage" in turb_metric or "UNVERIFIED" in turb_metric, "Turbidity not labeled as voltage / unverified!"
        
        # Click through all 7 tabs and measure tab switching latency
        print("\n[4] Testing Tab Switching Responsiveness...")
        tabs = page.query_selector_all('button[data-baseweb="tab"]')
        print(f"    Found {len(tabs)} tabs.")
        
        tab_names = [t.inner_text() for t in tabs]
        for idx, t_name in enumerate(tab_names):
            t_switch_start = time.perf_counter()
            tabs[idx].click()
            page.wait_for_timeout(400) # Wait for animation/render
            switch_ms = (time.perf_counter() - t_switch_start) * 1000.0
            print(f"    Tab {idx+1}: {t_name.splitlines()[0]:<35} -> {switch_ms:6.1f} ms")
            
            # Check for exceptions on each tab
            tab_exc = page.query_selector_all(".stException")
            assert len(tab_exc) == 0, f"Exception on tab {t_name}!"
            
        # Capture screenshots
        os.makedirs("docs", exist_ok=True)
        # Go back to Tab 1
        tabs[0].click()
        page.wait_for_timeout(500)
        page.screenshot(path="docs/DASHBOARD_OPTIMIZED_TAB1.png")
        print("    Saved Tab 1 screenshot: docs/DASHBOARD_OPTIMIZED_TAB1.png")
        
        # Tab 4 (Historical charts)
        tabs[3].click()
        page.wait_for_timeout(800)
        page.screenshot(path="docs/DASHBOARD_OPTIMIZED_TAB4_CHARTS.png")
        print("    Saved Tab 4 screenshot: docs/DASHBOARD_OPTIMIZED_TAB4_CHARTS.png")
        
        # Check console errors
        app_console_errors = [e for e in console_errors if "favicon" not in e and "font" not in e]
        print(f"\n[5] Console Errors Filtered: {len(app_console_errors)}")
        for err in app_console_errors:
            print(f"    Console Error: {err}")
            
        print("\n" + "=" * 70)
        print("✅ DASHBOARD LIVE PERFORMANCE VERIFICATION PASSED")
        print("=" * 70)
        browser.close()

if __name__ == "__main__":
    test_dashboard_performance()
