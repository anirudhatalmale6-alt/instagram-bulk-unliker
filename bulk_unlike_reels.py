#!/usr/bin/env python3
"""
Instagram Bulk Reel Unliker
===========================
Automatically unlikes all your liked Reels on Instagram.

How it works:
1. Opens a browser window for you to log in manually
2. Navigates to your liked Reels via Your Activity
3. Selects and unlikes them in batches

Requirements: Python 3.8+, playwright
Install:  pip3 install playwright && python3 -m playwright install chromium
Run:      python3 bulk_unlike_reels.py
"""

import time
import sys

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("\n[!] Playwright is not installed.")
    print("    Run these two commands first:\n")
    print("      pip3 install playwright")
    print("      python3 -m playwright install chromium\n")
    sys.exit(1)


# --- Settings ---
DELAY_BETWEEN_ACTIONS = 2.0   # seconds between clicks (stay safe from rate limits)
BATCH_PAUSE = 5.0             # seconds to pause between batches
SCROLL_PAUSE = 3.0            # seconds to wait after scrolling for content to load
MAX_RETRIES = 3               # retry attempts per action


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def wait_for_login(page):
    """Wait for the user to log in manually."""
    log("Waiting for you to log in...")
    log("(The script will continue automatically once you're logged in)\n")

    while True:
        try:
            # Check if we're on a logged-in page
            url = page.url
            if "instagram.com" in url and "/accounts/login" not in url and "/challenge" not in url:
                # Verify we're actually logged in by checking for profile icon
                try:
                    page.wait_for_selector('svg[aria-label="Settings"]', timeout=3000)
                    return True
                except PwTimeout:
                    pass
                try:
                    page.wait_for_selector('a[href*="/direct/"]', timeout=3000)
                    return True
                except PwTimeout:
                    pass
                try:
                    page.wait_for_selector('span[role="link"]', timeout=3000)
                    return True
                except PwTimeout:
                    pass
                # If URL changed from login, give benefit of the doubt after waiting
                time.sleep(3)
                if "/accounts/login" not in page.url:
                    return True
        except Exception:
            pass
        time.sleep(2)


def unlike_via_your_activity(page):
    """
    Uses Instagram's 'Your Activity' > 'Likes' page to bulk-unlike reels.
    This is the most reliable method as it uses Instagram's own UI.
    """
    total_unliked = 0

    while True:
        # Navigate to Your Activity > Likes
        log("Navigating to Your Activity > Likes...")
        page.goto("https://www.instagram.com/your_activity/interactions/likes/", wait_until="networkidle")
        time.sleep(SCROLL_PAUSE)

        # Check if there are any liked items
        # Look for the "Select" button which appears when there are liked items
        select_btn = None
        try:
            # Try to find "Select" button
            select_btn = page.locator('text="Select"').first
            select_btn.wait_for(timeout=8000)
        except PwTimeout:
            # Try alternative selectors
            try:
                select_btn = page.locator('button:has-text("Select")').first
                select_btn.wait_for(timeout=5000)
            except PwTimeout:
                log("No 'Select' button found - you may have no more liked content!")
                break

        # Click "Select" to enter selection mode
        log("Entering selection mode...")
        select_btn.click()
        time.sleep(DELAY_BETWEEN_ACTIONS)

        # Select items (Instagram shows them as a grid)
        # Find all selectable items
        selected_count = 0
        items = page.locator('div[role="button"][tabindex="0"]').all()

        # Try clicking on individual reel thumbnails to select them
        # Instagram's Your Activity page shows items as clickable thumbnails
        clickable_items = page.locator('div[role="checkbox"], div[role="button"] img, button[aria-label*="select"], div[class*="select"]').all()

        if not clickable_items:
            # Try a broader selector for grid items
            clickable_items = page.locator('div._aagu, div._aagv, div._aagw').all()

        if not clickable_items:
            # Fallback: try to find any image containers in the grid
            clickable_items = page.locator('div[style*="padding"] > div > div > div').all()

        # Select up to 50 items at a time (Instagram's limit)
        batch_size = min(50, len(clickable_items))

        if batch_size == 0:
            log("No selectable items found on this page.")
            # Try the alternative approach
            break

        log(f"Found {len(clickable_items)} items, selecting up to {batch_size}...")

        for i in range(batch_size):
            try:
                clickable_items[i].click()
                selected_count += 1
                time.sleep(0.3)
            except Exception:
                continue

        if selected_count == 0:
            log("Could not select any items.")
            break

        log(f"Selected {selected_count} items")
        time.sleep(DELAY_BETWEEN_ACTIONS)

        # Click "Unlike" button
        unlike_btn = None
        for text in ["Unlike", "unlike"]:
            try:
                unlike_btn = page.locator(f'button:has-text("{text}")').first
                unlike_btn.wait_for(timeout=5000)
                break
            except PwTimeout:
                continue

        if not unlike_btn:
            log("Could not find 'Unlike' button")
            break

        unlike_btn.click()
        time.sleep(DELAY_BETWEEN_ACTIONS)

        # Confirm if there's a confirmation dialog
        try:
            confirm_btn = page.locator('button:has-text("Unlike")').first
            confirm_btn.wait_for(timeout=3000)
            confirm_btn.click()
            time.sleep(DELAY_BETWEEN_ACTIONS)
        except PwTimeout:
            pass

        total_unliked += selected_count
        log(f"Unliked batch of {selected_count} items (total so far: {total_unliked})")

        time.sleep(BATCH_PAUSE)

    return total_unliked


def unlike_via_scrolling(page):
    """
    Alternative method: scroll through liked reels and unlike them individually.
    Used as fallback if the Your Activity method doesn't work well.
    """
    log("Trying alternative method: scrolling through liked reels...")

    # Try the Reels-specific liked page
    page.goto("https://www.instagram.com/your_activity/interactions/likes/", wait_until="networkidle")
    time.sleep(SCROLL_PAUSE)

    # Try to filter to just Reels if possible
    try:
        reels_filter = page.locator('text="Reels"').first
        reels_filter.wait_for(timeout=5000)
        reels_filter.click()
        time.sleep(DELAY_BETWEEN_ACTIONS)
    except PwTimeout:
        log("No Reels filter available, processing all liked content...")

    # Now try to find Sort & Filter to sort by oldest first
    try:
        sort_btn = page.locator('text="Sort & Filter"').first
        sort_btn.wait_for(timeout=3000)
        sort_btn.click()
        time.sleep(1)
    except PwTimeout:
        pass

    total_unliked = 0
    no_items_count = 0

    while no_items_count < 3:
        # Look for the select/manage interface
        try:
            select_btn = page.locator('text="Select"').first
            select_btn.wait_for(timeout=5000)
            select_btn.click()
            time.sleep(DELAY_BETWEEN_ACTIONS)
        except PwTimeout:
            no_items_count += 1
            log(f"Cannot find Select button (attempt {no_items_count}/3)")
            page.reload()
            time.sleep(SCROLL_PAUSE)
            continue

        # Try to select all visible items
        selected = 0
        # Click on grid thumbnails
        thumbs = page.locator('div[role="button"]').all()
        for thumb in thumbs[:50]:
            try:
                box = thumb.bounding_box()
                if box and box["y"] > 100:  # Skip header buttons
                    thumb.click()
                    selected += 1
                    time.sleep(0.2)
            except Exception:
                continue

        if selected == 0:
            no_items_count += 1
            continue

        # Unlike
        try:
            unlike_btn = page.locator('button:has-text("Unlike")').first
            unlike_btn.wait_for(timeout=5000)
            unlike_btn.click()
            time.sleep(DELAY_BETWEEN_ACTIONS)

            # Confirm
            try:
                confirm = page.locator('button:has-text("Unlike")').first
                confirm.wait_for(timeout=3000)
                confirm.click()
            except PwTimeout:
                pass

            total_unliked += selected
            log(f"Unliked {selected} items (total: {total_unliked})")
            no_items_count = 0
        except PwTimeout:
            log("Unlike button not found")
            no_items_count += 1

        time.sleep(BATCH_PAUSE)

    return total_unliked


def main():
    print("=" * 55)
    print("   Instagram Bulk Reel Unliker")
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
    input("Press ENTER to start...")
    print()

    with sync_playwright() as p:
        # Launch a visible browser (not headless) so user can log in
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # Go to Instagram login
        log("Opening Instagram...")
        page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        time.sleep(2)

        # Handle cookie consent if it appears
        try:
            cookie_btn = page.locator('button:has-text("Allow"), button:has-text("Accept")').first
            cookie_btn.wait_for(timeout=3000)
            cookie_btn.click()
            time.sleep(1)
        except PwTimeout:
            pass

        # Wait for user to log in
        wait_for_login(page)
        log("Login detected! Starting the unlike process...\n")
        time.sleep(3)

        # Method 1: Use Your Activity page (most reliable)
        total = unlike_via_your_activity(page)

        if total == 0:
            # Method 2: Try scrolling approach as fallback
            total = unlike_via_scrolling(page)

        print()
        print("=" * 55)
        if total > 0:
            log(f"DONE! Unliked {total} items in total.")
        else:
            log("Could not unlike items automatically.")
            log("This might mean:")
            log("  - You have no liked Reels")
            log("  - Instagram changed their UI layout")
            log("")
            log("TIP: You can also do it manually:")
            log("  Settings > Your Activity > Interactions > Likes")
            log("  Then use Select > pick items > Unlike")
        print("=" * 55)
        print()

        input("Press ENTER to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
