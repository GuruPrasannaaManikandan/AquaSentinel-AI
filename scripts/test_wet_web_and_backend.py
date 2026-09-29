import sys
import os
import time
import json
import requests
from playwright.sync_api import sync_playwright

def test_wet_web_and_backend():
    print("=" * 70)
    print("PHASE 14, 15, 16, 17: BACKEND & WEB DASHBOARD WET VALIDATION")
    print("=" * 70)
    
    # --- PHASE 14: FASTAPI BACKEND VERIFICATION ---
    print("\n[PHASE 14] Querying FastAPI Backend on http://127.0.0.1:8000...")
    endpoints = [
        "/health",
        "/devices",
        "/devices/AQUA_FRESH_001/latest",
        "/devices/AQUA_FRESH_001/intelligence",
        "/devices/AQUA_FRESH_001/multimodal",
        "/devices/AQUA_FRESH_001/response",
        "/devices/AQUA_FRESH_001/risk-trend",
        "/system/reliability"
    ]
    
    backend_results = {}
    for ep in endpoints:
        r = requests.get(f"http://127.0.0.1:8000{ep}", timeout=5)
        print(f"  {ep:35s}: HTTP {r.status_code}")
        assert r.status_code == 200, f"Endpoint {ep} returned {r.status_code}"
        backend_results[ep] = r.json()
        
    latest_data = backend_results["/devices/AQUA_FRESH_001/latest"]
    latest_tel = latest_data["telemetry"]
    latest_dec = latest_data["decision"]
    
    print("\n[BACKEND TRACE] Verified latest wet telemetry from backend:")
    print(f"  Timestamp:  {latest_tel.get('timestamp')}")
    print(f"  pH:         {latest_tel.get('ph')}")
    print(f"  Turbidity:  {latest_tel.get('turbidity_ntu')} V")
    print(f"  Temp / Sal: {latest_tel.get('temperature_c')} / {latest_tel.get('salinity_ppt')}")
    print(f"  State:      {latest_dec.get('final_state')} ({latest_dec.get('reason_code')})")

    # --- PHASE 15 & 16: PLAYWRIGHT WEB DASHBOARD VERIFICATION ---
    print("\n[PHASE 15 & 16] Launching Chromium to inspect http://127.0.0.1:8501...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=15000)
        time.sleep(5)
        
        # Verify page title
        title = page.title()
        print(f"  Page Title: '{title}'")
        assert "Aquatic" in title
        
        # Check for exceptions
        exceptions = page.query_selector_all(".stException")
        print(f"  Streamlit Exceptions in DOM: {len(exceptions)}")
        assert len(exceptions) == 0, "Found red Streamlit exceptions in DOM!"
        
        body_text = page.inner_text("body")
        
        # Verify AQUA_FRESH_001
        assert "AQUA_FRESH_001" in body_text, "Target node AQUA_FRESH_001 not found!"
        print("  -> AQUA_FRESH_001 node is visible.")
        
        # Verify GPS Null Handling
        assert "GPS Module: Not Equipped / Inactive" in body_text, "GPS null message missing!"
        print("  -> GPS null handling confirmed: 'GPS Module: Not Equipped / Inactive'.")
        
        # Verify live values on dashboard
        print("\n[DASHBOARD METRICS CHECK]")
        metrics = page.query_selector_all('[data-testid="stMetric"]')
        print(f"  Found {len(metrics)} metric cards rendered:")
        for m in metrics[:15]:
            lines = [l.strip() for l in m.inner_text().split("\n") if l.strip()]
            if len(lines) >= 2:
                print(f"    - {lines[0]}: {lines[1]}")
                
        # Tab testing
        tabs = page.query_selector_all('button[role="tab"]') or page.query_selector_all('[data-baseweb="tab"]')
        print(f"\n[TAB VERIFICATION] Testing {len(tabs)} tabs...")
        for idx, tab in enumerate(tabs):
            tab_name = tab.inner_text().strip()
            tab.click()
            time.sleep(1)
            errs = page.query_selector_all(".stException")
            assert len(errs) == 0, f"Exception in Tab {tab_name}!"
            print(f"  Tab {idx + 1} ({tab_name}): OK")
            
        # Return to Tab 1
        if tabs:
            tabs[0].click()
            time.sleep(2)
            
        # --- PHASE 17: 60-SECOND STREAMING TEST ---
        print("\n" + "=" * 70)
        print("[PHASE 17] 60-SECOND LIVE STREAMING OBSERVATION (T+0, T+15, T+30, T+45, T+60)")
        print("=" * 70)
        
        streaming_records = []
        for interval in [0, 15, 30, 45, 60]:
            if interval > 0:
                time.sleep(15)
            tel_now = requests.get("http://127.0.0.1:8000/devices/AQUA_FRESH_001/latest").json()
            rec = {
                "checkpoint": f"T+{interval:02d}s",
                "id": tel_now["telemetry"]["id"],
                "timestamp": tel_now["telemetry"]["timestamp"],
                "ph": tel_now["telemetry"]["ph"],
                "turbidity": tel_now["telemetry"]["turbidity_ntu"],
                "temp": tel_now["telemetry"]["temperature_c"],
                "state": tel_now["decision"]["final_state"]
            }
            streaming_records.append(rec)
            print(f"  [{rec['checkpoint']}] Event ID: {rec['id']} | TS: {rec['timestamp']} | pH: {rec['ph']:6.2f} | Turb: {rec['turbidity']:6.3f} V | State: {rec['state']}")
            
        # Verify event progression
        assert streaming_records[-1]["id"] > streaming_records[0]["id"], "Event ID did not advance!"
        print(f"\n[STREAMING VERIFIED] Event ID advanced from {streaming_records[0]['id']} to {streaming_records[-1]['id']} (+{streaming_records[-1]['id'] - streaming_records[0]['id']} events).")
        
        # Save screenshot
        screenshot_path = "docs/DASHBOARD_WET_VALIDATION.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n[SCREENSHOT] Full-page wet validation screenshot saved to: {screenshot_path}")
        
        browser.close()
        
    print("=" * 70)
    print("BACKEND AND WEB DASHBOARD WET VALIDATION: PASS")
    print("=" * 70)

if __name__ == "__main__":
    test_wet_web_and_backend()
