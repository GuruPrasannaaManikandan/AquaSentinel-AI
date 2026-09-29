from playwright.sync_api import sync_playwright
import time

def debug_dom():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto("http://127.0.0.1:8501", wait_until="networkidle")
        time.sleep(6)
        
        # Save HTML
        html = page.content()
        with open("docs/rendered_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML saved (length: {len(html)})")
        
        # Save Text
        text = page.inner_text("body")
        with open("docs/rendered_body_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Text saved (length: {len(text)})")
        print("First 500 chars:\n", text[:500])
        print("Last 500 chars:\n", text[-500:])
        browser.close()

if __name__ == "__main__":
    debug_dom()
