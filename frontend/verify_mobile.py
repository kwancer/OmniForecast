from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Emulate a mobile device (e.g. Pixel 5)
        context = browser.new_context(
            viewport={'width': 393, 'height': 851},
            user_agent='Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36'
        )
        page = context.new_page()

        try:
            # Go to the local dev server (Port 3000 according to logs)
            page.goto("http://localhost:3000/")

            # Wait for the page to load (e.g. title or logo)
            page.wait_for_load_state("networkidle")

            # 1. Verify Header Hamburger
            page.screenshot(path="/home/jules/verification/mobile_home.png")

            # Click hamburger
            buttons = page.get_by_role("button").all()
            # The first button in the app bar is usually the hamburger if it's prepended.
            # However, Vuetify might have other buttons.
            # Let's find the one that is visible.
            if buttons:
                # Click the first one (Hamburger)
                buttons[0].click()
                page.wait_for_timeout(1000) # Wait for animation
                page.screenshot(path="/home/jules/verification/mobile_drawer_open.png")

                # Close drawer
                page.mouse.click(300, 300)
                page.wait_for_timeout(500)

            # 2. Verify Stepper
            page.screenshot(path="/home/jules/verification/mobile_stepper.png")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_frontend()
