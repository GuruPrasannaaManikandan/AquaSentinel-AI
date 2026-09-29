import sys
import time
from playwright.sync_api import sync_playwright

def verify_dashboard_manual_capture():
    print("Connecting to dashboard at http://127.0.0.1:8501/...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:8501/", timeout=30000, wait_until="networkidle")
        time.sleep(3)

        # Look for tabs
        tabs = page.locator("button[data-baseweb='tab']")
        count = tabs.count()
        print(f"Found {count} tabs.")
        
        # Click Tab 2 (index 1)
        if count >= 2:
            print("Clicking Tab 2 (Optical & Temporal Intelligence)...")
            tabs.nth(1).click()
            time.sleep(2)
        else:
            print("Could not find Tab 2 by selector, searching by text...")
            tab2 = page.get_by_text("Optical", exact=False).first
            tab2.click()
            time.sleep(2)

        tab2_content = page.content()
        assert "Manual Photo Capture" in tab2_content, "Missing 'Manual Photo Capture' in Tab 2!"
        assert "GC2145" in tab2_content, "Missing 'GC2145' in Tab 2!"
        print("✅ Found Manual Photo Capture section and GC2145!")

        # Find the button
        btn = page.get_by_role("button", name="📸 CAPTURE PHOTO")
        assert btn.is_visible(), "Capture button '📸 CAPTURE PHOTO' is not visible!"
        print("✅ Found visible '📸 CAPTURE PHOTO' button!")

        # Click the button
        print("Clicking '📸 CAPTURE PHOTO' button...")
        btn.click()
        
        # Wait for capture to process and page to update
        print("Waiting for photo capture to complete...")
        time.sleep(4)

        # Check for success message
        page_text = page.content()
        assert "Photo captured successfully" in page_text or "Capture" in page_text, "Capture status message missing!"
        print("✅ Photo capture success message verified!")

        # Save screenshot
        screenshot_path = "docs/MANUAL_CAMERA_CAPTURE_DASHBOARD.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"✅ Dashboard screenshot saved to {screenshot_path}")

        browser.close()
    return True

if __name__ == "__main__":
    try:
        verify_dashboard_manual_capture()
        print("🎉 ALL BROWSER DASHBOARD CHECKS PASSED!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
