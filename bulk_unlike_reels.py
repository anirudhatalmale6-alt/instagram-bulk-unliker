#!/usr/bin/env python3
"""
Instagram Bulk Reel Unliker v2
==============================
Automatically unlikes all your liked Reels on Instagram.
Uses JavaScript injection for reliable element detection.
"""

import time
import sys
import os

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("\n[!] Playwright is not installed.")
    print("    Run these two commands first:\n")
    print("      pip3 install playwright")
    print("      python3 -m playwright install chromium\n")
    sys.exit(1)


DELAY = 2.0
BATCH_PAUSE = 5.0


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def screenshot(page, name):
    """Save a debug screenshot."""
    path = os.path.expanduser(f"~/Desktop/insta_debug_{name}.png")
    try:
        page.screenshot(path=path)
        log(f"  Screenshot saved: {path}")
    except Exception:
        pass


def wait_for_login(page):
    """Wait for the user to log in manually."""
    log("Waiting for you to log in...")
    log("(The script will continue automatically once you're logged in)\n")
    while True:
        try:
            url = page.url
            if "instagram.com" in url and "/accounts/login" not in url and "/challenge" not in url:
                time.sleep(5)
                if "/accounts/login" not in page.url:
                    return True
        except Exception:
            pass
        time.sleep(2)


def dismiss_popups(page):
    """Dismiss any popups like 'Turn on notifications', 'Save info', etc."""
    for text in ["Not Now", "Not now", "Cancel", "Decline"]:
        try:
            btn = page.locator(f'button:has-text("{text}")').first
            if btn.is_visible(timeout=2000):
                btn.click()
                time.sleep(1)
        except Exception:
            pass


def unlike_batch_via_activity(page):
    """
    Navigate to Your Activity > Likes, select items, and unlike them.
    Returns the number of items unliked in this batch, or -1 if no items found.
    """
    # Navigate to the likes page
    log("Navigating to Your Activity > Likes...")
    page.goto("https://www.instagram.com/your_activity/interactions/likes/",
              wait_until="domcontentloaded")
    time.sleep(4)
    dismiss_popups(page)
    time.sleep(2)

    # Take a debug screenshot
    screenshot(page, "likes_page")

    # Log the page content for debugging
    page_text = page.evaluate("() => document.body.innerText")
    log(f"  Page contains {len(page_text)} chars of text")

    # Look for "Select" button using JavaScript for reliability
    select_found = page.evaluate("""() => {
        // Find all elements that contain "Select" text
        const allElements = document.querySelectorAll('*');
        for (const el of allElements) {
            if (el.childNodes.length === 1 &&
                el.childNodes[0].nodeType === 3 &&
                el.textContent.trim() === 'Select') {
                el.click();
                return true;
            }
        }
        // Try finding a link/button with Select text
        const links = document.querySelectorAll('a, button, div[role="button"], span[role="button"]');
        for (const el of links) {
            if (el.textContent.trim() === 'Select') {
                el.click();
                return true;
            }
        }
        return false;
    }""")

    if not select_found:
        log("Could not find 'Select' button on the page.")
        screenshot(page, "no_select")

        # Check if the page has any content at all
        has_content = page.evaluate("""() => {
            const imgs = document.querySelectorAll('img');
            return imgs.length;
        }""")
        log(f"  Found {has_content} images on page")

        if has_content < 5:
            log("  Page seems empty - you may have no more liked content!")
            return -1
        else:
            log("  Page has content but Select button not found")
            return -1

    log("Clicked 'Select' - entering selection mode...")
    time.sleep(DELAY)
    screenshot(page, "selection_mode")

    # Now select items by clicking on the grid thumbnails
    # Instagram shows checkboxes or clickable overlays on images
    selected = page.evaluate("""() => {
        let count = 0;
        const maxSelect = 50;

        // Method 1: Look for checkboxes
        const checkboxes = document.querySelectorAll('input[type="checkbox"], div[role="checkbox"]');
        for (const cb of checkboxes) {
            if (count >= maxSelect) break;
            cb.click();
            count++;
        }
        if (count > 0) return count;

        // Method 2: Look for grid items with images (the photo thumbnails)
        const gridImages = document.querySelectorAll('div[style*="padding-bottom"] img, div._aagv img, article img');
        for (const img of gridImages) {
            if (count >= maxSelect) break;
            // Click the parent container
            let target = img.parentElement;
            for (let i = 0; i < 3; i++) {
                if (target && target.parentElement) target = target.parentElement;
            }
            if (target) {
                target.click();
                count++;
            }
        }
        if (count > 0) return count;

        // Method 3: Click on any div that looks like a grid cell
        const cells = document.querySelectorAll('div[role="button"]');
        const mainContent = document.querySelector('main') || document.body;
        for (const cell of cells) {
            if (count >= maxSelect) break;
            const rect = cell.getBoundingClientRect();
            // Only click cells that are in the main content area (not header/nav)
            if (rect.top > 200 && rect.width > 50 && rect.height > 50 && rect.width < 400) {
                cell.click();
                count++;
            }
        }
        return count;
    }""")

    log(f"Selected {selected} items")

    if selected == 0:
        log("Could not select any items.")
        screenshot(page, "no_items_selected")
        return 0

    time.sleep(DELAY)
    screenshot(page, "items_selected")

    # Look for "Unlike" button
    unlike_clicked = page.evaluate("""() => {
        const allElements = document.querySelectorAll('button, div[role="button"], a');
        for (const el of allElements) {
            const text = el.textContent.trim();
            if (text === 'Unlike' || text === 'unlike') {
                el.click();
                return true;
            }
        }
        return false;
    }""")

    if not unlike_clicked:
        log("Could not find 'Unlike' button")
        screenshot(page, "no_unlike_btn")
        return 0

    log("Clicked 'Unlike'...")
    time.sleep(DELAY)

    # Handle confirmation dialog if it appears
    page.evaluate("""() => {
        setTimeout(() => {
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.textContent.trim() === 'Unlike') {
                    btn.click();
                    break;
                }
            }
        }, 1000);
    }""")
    time.sleep(3)

    log(f"Unliked {selected} items!")
    screenshot(page, "after_unlike")
    return selected


def main():
    print("=" * 55)
    print("   Instagram Bulk Reel Unliker v2")
    print("=" * 55)
    print()
    print("This tool will open a browser window.")
    print("You will need to:")
    print("  1. Log in to your Instagram account")
    print("  2. Sit back while the script unlikes your Reels")
    print()
    print("IMPORTANT: Keep the browser window visible.")
    print("           Do not close it until the script finishes.")
    print()
    print("Debug screenshots will be saved to your Desktop")
    print("so we can troubleshoot if anything goes wrong.")
    print()
    input("Press ENTER to start...")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # Mask automation signals
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
        """)

        log("Opening Instagram...")
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        time.sleep(3)

        # Handle cookie consent
        try:
            for text in ["Allow essential and optional cookies", "Allow all cookies", "Accept", "Allow"]:
                btn = page.locator(f'button:has-text("{text}")').first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    time.sleep(1)
                    break
        except Exception:
            pass

        wait_for_login(page)
        log("Login detected!")
        time.sleep(3)
        dismiss_popups(page)
        time.sleep(2)

        log("Starting the unlike process...\n")

        total_unliked = 0
        consecutive_failures = 0

        while consecutive_failures < 3:
            result = unlike_batch_via_activity(page)

            if result == -1:
                # No content found at all
                break
            elif result == 0:
                consecutive_failures += 1
                log(f"Batch failed (attempt {consecutive_failures}/3)")
                time.sleep(BATCH_PAUSE)
            else:
                total_unliked += result
                consecutive_failures = 0
                log(f"Total unliked so far: {total_unliked}\n")
                time.sleep(BATCH_PAUSE)

        print()
        print("=" * 55)
        if total_unliked > 0:
            log(f"DONE! Unliked {total_unliked} items in total.")
            log("If you have more liked reels, run the script again.")
        else:
            log("Could not unlike items automatically.")
            log("")
            log("Debug screenshots have been saved to your Desktop.")
            log("Please send them to me and I'll figure out what's wrong!")
            log("")
            log("Screenshots are named: insta_debug_*.png")
        print("=" * 55)
        print()

        input("Press ENTER to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
