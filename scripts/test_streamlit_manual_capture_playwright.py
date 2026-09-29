import time
import os
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "reports", "camera_verification")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    print("Launching Chromium via Playwright to verify Streamlit manual capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8501 ...")
        page.goto("http://127.0.0.1:8501", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        print("Page loaded. Clicking Tab 2: Optical & Temporal Intelligence...")
        tab2 = page.locator("button[role='tab']:has-text('Optical & Temporal Intelligence')")
        tab2.wait_for(timeout=10000)
        tab2.click()
        time.sleep(2)

        # Look for the Camera card or capture button
        print("Looking for camera section...")
        cam_header = page.locator("text=Physical ESP32-CAM")
        cam_header.first.wait_for(timeout=10000)
        print("Found camera section!")

        # Scroll into view
        cam_header.first.scroll_into_view_if_needed()
        time.sleep(1)

        # Capture #0 (Initial state)
        init_shot = os.path.join(SCREENSHOTS_DIR, "playwright_cam_00_initial.png")
        page.screenshot(path=init_shot)
        print(f"Captured initial screenshot: {init_shot}")

        # Find the capture button
        btn = page.locator("button:has-text('CAPTURE PHOTO')")
        print("Found capture button count:", btn.count())

        # Click Capture Photo #1
        print("\n--- CLICKING CAPTURE PHOTO (Capture #1) ---")
        btn.first.click()
        
        # Wait for Streamlit rerun and success message or new frame
        print("Waiting for capture #1 to process...")
        time.sleep(8)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        shot1 = os.path.join(SCREENSHOTS_DIR, "playwright_cam_01_after_first_capture.png")
        page.screenshot(path=shot1)
        print(f"Captured screenshot #1: {shot1}")

        # Read text
        card_text1 = page.locator("div[data-testid='stAlert']").all_text_contents()
        print("Alerts after Capture #1:", card_text1)

        # Click Capture Photo #2
        print("\n--- CLICKING CAPTURE PHOTO (Capture #2) ---")
        btn = page.locator("button:has-text('CAPTURE PHOTO')")
        btn.first.click()

        print("Waiting for capture #2 to process...")
        time.sleep(8)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        shot2 = os.path.join(SCREENSHOTS_DIR, "playwright_cam_02_after_second_capture.png")
        page.screenshot(path=shot2)
        print(f"Captured screenshot #2: {shot2}")

        card_text2 = page.locator("div[data-testid='stAlert']").all_text_contents()
        print("Alerts after Capture #2:", card_text2)

        browser.close()
        print("\nPlaywright manual capture verification complete!")

if __name__ == "__main__":
    run()
