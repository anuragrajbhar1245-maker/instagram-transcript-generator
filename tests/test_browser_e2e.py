import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_e2e_test(target_url="https://instagram-transcript-generator.onrender.com"):
    print(f"[START] Starting Playwright E2E verification on: {target_url}")
    
    console_errors = []
    failed_requests = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Monitor console errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.url} - {req.failure}"))

        print("[STEP 1] Navigating to landing page...")
        response = page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        assert response.status == 200, f"Expected status 200, got {response.status}"

        page.wait_for_load_state("networkidle")
        print("  -> Page loaded successfully with network idle.")

        # Verify Core DOM Elements
        print("[STEP 2] Verifying Core UI Elements...")
        assert page.locator("header").is_visible(), "Header is not visible"
        assert page.locator("header img[alt*='InstaTranscript']").is_visible(), "Logo is not visible"
        assert page.locator("header h1:has-text('InstaTranscript')").is_visible(), "Title is not visible"
        
        # Check input form
        url_input = page.locator("#urlInput")
        assert url_input.is_visible(), "Instagram URL input (#urlInput) is not visible"
        print("  -> Header, Logo, and URL Input verified.")

        # Check Language Select
        lang_select = page.locator("#quickLanguageSelect")
        assert lang_select.is_visible(), "Quick language selector (#quickLanguageSelect) not visible"
        options = lang_select.locator("option").all_inner_texts()
        assert len(options) >= 10, f"Expected at least 10 language options, got {len(options)}"
        print(f"  -> Language selector verified ({len(options)} options).")

        # Check Submit Button
        submit_btn = page.locator("#submitBtn")
        assert submit_btn.is_visible(), "Submit button (#submitBtn) is not visible"
        print("  -> Submit button verified.")

        # Test Auth Modal Flow (Sign In & Sign Up tabs)
        print("[STEP 3] Testing Auth Modal & Tab Switching...")
        auth_open_btn = page.locator("#authOpenBtn")
        assert auth_open_btn.is_visible(), "Sign in button (#authOpenBtn) is not visible"
        auth_open_btn.click()
        page.wait_for_timeout(400)

        auth_modal = page.locator("#authModal")
        assert auth_modal.is_visible(), "Auth modal (#authModal) did not open on click"
        print("  -> Auth modal opened.")

        # Switch to Register tab
        tab_register = page.locator("#authTabRegister")
        tab_register.click()
        page.wait_for_timeout(300)

        register_form = page.locator("#registerForm")
        assert register_form.is_visible(), "Register form (#registerForm) is not visible after tab switch"
        assert page.locator("#registerEmail").is_visible(), "Register email input not visible"
        assert page.locator("#registerPassword").is_visible(), "Register password input not visible"
        print("  -> Switched to Sign Up tab and verified form fields.")

        # Switch back to Login tab
        tab_login = page.locator("#authTabLogin")
        tab_login.click()
        page.wait_for_timeout(300)
        assert page.locator("#loginForm").is_visible(), "Login form (#loginForm) not visible after tab switch"
        print("  -> Switched back to Sign In tab.")

        # Close Auth Modal
        close_auth_btn = page.locator("#closeAuthBtn")
        close_auth_btn.click()
        page.wait_for_timeout(300)
        assert not auth_modal.is_visible(), "Auth modal did not close on close button click"
        print("  -> Auth modal closed successfully.")

        # Test History Drawer / Modal
        print("[STEP 4] Testing History Drawer...")
        history_btn = page.locator("#historyBtn")
        assert history_btn.is_visible(), "History button (#historyBtn) is not visible"
        history_btn.click()
        page.wait_for_timeout(400)

        history_modal = page.locator("#historyModal")
        assert history_modal.is_visible(), "History modal (#historyModal) did not open"
        print("  -> History modal opened.")

        close_history_btn = page.locator("#closeHistoryBtn")
        close_history_btn.click()
        page.wait_for_timeout(300)
        assert not history_modal.is_visible(), "History modal did not close"
        print("  -> History modal closed successfully.")

        # Capture Verification Screenshot
        screenshot_path = "tests/e2e_verification_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"[STEP 5] Captured full-page screenshot at '{screenshot_path}'.")

        # Verify Console Logs & Network Cleanliness
        print("[STEP 6] Verifying runtime error logs...")
        critical_console_errors = [e for e in console_errors if "favicon" not in e and "third-party" not in e]
        print(f"  -> Console errors detected: {len(critical_console_errors)}")
        print(f"  -> Failed network requests: {len(failed_requests)}")
        assert len(critical_console_errors) == 0, f"Detected critical console errors: {critical_console_errors}"

        browser.close()
        print("[SUCCESS] Playwright E2E verification completed successfully with 100% assertions passed!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://instagram-transcript-generator.onrender.com"
    run_e2e_test(target)
