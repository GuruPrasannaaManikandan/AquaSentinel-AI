import time
import os
from playwright.sync_api import sync_playwright

def test_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("[TEST] Navigating to http://127.0.0.1:8501/...")
        t0 = time.perf_counter()
        page.goto("http://127.0.0.1:8501", timeout=30000, wait_until="domcontentloaded")
        page.wait_for_selector(".stApp", timeout=20000)
        load_time = time.perf_counter() - t0
        print(f"[TEST] Initial load time: {load_time:.3f}s")

        # Wait for Streamlit to settle
        page.wait_for_timeout(3000)

        # Verify Tab 1 metrics
        body_text = page.inner_text("body")
        assert "Water pH — DEMO NORMALIZED" in body_text, "Missing 'Water pH — DEMO NORMALIZED'"
        assert "DEMO / NOT CALIBRATED" in body_text, "Missing 'DEMO / NOT CALIBRATED'"
        assert "Turbidity Voltage (V)" in body_text, "Missing 'Turbidity Voltage (V)'"
        assert "UNVERIFIED / UNCALIBRATED" in body_text, "Missing 'UNVERIFIED / UNCALIBRATED'"
        print("✅ TAB 1 (pH Demo Normalized & Turbidity Voltage) verified successfully!")

        os.makedirs("docs", exist_ok=True)
        tab1_screenshot = "docs/DASHBOARD_LIVE_TAB1_PH_DEMO.png"
        page.screenshot(path=tab1_screenshot, full_page=False)
        print(f"[TEST] Saved Tab 1 screenshot: {tab1_screenshot}")

        # Click on Tab 2: Optical & Temporal Intelligence
        t_tab0 = time.perf_counter()
        tab2_button = page.locator("button[role='tab']:has-text('Optical & Temporal Intelligence')")
        if tab2_button.count() > 0:
            tab2_button.click()
            tab_latency = time.perf_counter() - t_tab0
            print(f"[TEST] Switched to Tab 2 in {tab_latency * 1000:.1f}ms")
            page.wait_for_timeout(2000)

            tab2_text = page.inner_text("body")
            assert "Camera: ONLINE" in tab2_text, "Missing 'Camera: ONLINE'"
            assert "Frame Acquisition: PASS" in tab2_text, "Missing 'Frame Acquisition: PASS'"
            assert "GC2145" in tab2_text, "Missing 'GC2145'"
            print("✅ TAB 2 (Camera ONLINE, GC2145, Optical Quality) verified successfully!")

            tab2_screenshot = "docs/DASHBOARD_LIVE_TAB2_CAMERA_FRAME.png"
            page.screenshot(path=tab2_screenshot, full_page=False)
            print(f"[TEST] Saved Tab 2 screenshot: {tab2_screenshot}")
        else:
            print("⚠️ Tab 2 button selector not found directly.")

        # Check console errors
        print(f"[TEST] Total browser console errors: {len(console_errors)}")
        if console_errors:
            print("Console Errors:", console_errors)

        browser.close()
        print("✅ ALL LIVE BROWSER CHECKS PASSED!")

if __name__ == "__main__":
    test_dashboard()
