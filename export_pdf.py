from playwright.sync_api import sync_playwright
import time

def export_to_pdf():
    print("Launching headless browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        print("Navigating to viewer...")
        page.goto("http://localhost:8000/viewer.html", wait_until="networkidle")
        
        # Give MathJax an extra 5 seconds just to be absolutely sure all LaTeX is rendered
        print("Waiting for MathJax to finish rendering LaTeX...")
        time.sleep(5) 
        
        print("Exporting to PDF...")
        page.pdf(
            path="Physics_Question_Bank.pdf",
            format="A4",
            print_background=True, # Keeps the dark theme if print CSS is disabled, but we added a print CSS so it will be white
            margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
        )
        
        browser.close()
        print("Successfully exported to Physics_Question_Bank.pdf!")

if __name__ == "__main__":
    export_to_pdf()
