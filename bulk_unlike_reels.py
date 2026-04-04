#!/usr/bin/env python3
"""
Instagram Bulk Reel Unliker v4
Waits for manual confirmation after login.
"""

import time
import sys
import os

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("\n[!] Playwright not installed. Run:")
    print("    pip3 install playwright")
    print("    python3 -m playwright install chromium\n")
    sys.exit(1)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def main():
    print("=" * 50)
    print("  Instagram Bulk Reel Unliker v4")
    print("=" * 50)
    print()
    input("Press ENTER to open the browser...")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML; like Gecko) Chrome/121.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")

        log("Opening Instagram...")
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        time.sleep(3)

        # Dismiss cookie popup
        try:
            for txt in ["Allow essential and optional cookies", "Allow all cookies", "Accept", "Allow"]:
                btn = page.locator(f'button:has-text("{txt}")').first
                if btn.is_visible(timeout=1500):
                    btn.click()
                    time.sleep(1)
                    break
        except Exception:
            pass

        print()
        print(">>> LOG IN to Instagram in the browser window.")
        print(">>> Complete ALL steps (password, email verify, etc.)")
        print(">>> When you see your Instagram feed, come back here.")
        print()
        input(">>> Press ENTER here AFTER you are fully logged in...")
        print()

        log("Great! Now navigating to your liked content...")
        time.sleep(2)

        # Dismiss popups
        for _ in range(3):
            try:
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const t = b.textContent.trim();
                        if (t === 'Not Now' || t === 'Not now') { b.click(); return true; }
                    }
                    return false;
                }""")
                time.sleep(1)
            except Exception:
                break

        total_unliked = 0
        consecutive_fails = 0
        round_num = 0

        while consecutive_fails < 3:
            round_num += 1
            log(f"--- Round {round_num} ---")

            # Navigate to likes page
            log("Going to Your Activity > Likes...")
            page.goto("https://www.instagram.com/your_activity/interactions/likes/",
                       wait_until="domcontentloaded")
            time.sleep(6)

            # Dismiss popups
            try:
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        if (b.textContent.trim() === 'Not Now') { b.click(); return; }
                    }
                }""")
                time.sleep(1)
            except Exception:
                pass

            # Screenshot for debugging
            debug_path = os.path.expanduser(f"~/Desktop/insta_debug_round{round_num}.png")
            try:
                page.screenshot(path=debug_path)
                log(f"  Screenshot saved: {debug_path}")
            except Exception:
                pass

            # Check if Select exists
            page_text = page.evaluate("() => document.body ? document.body.innerText : ''")
            log(f"  Page text length: {len(page_text)}")

            if "Select" not in page_text:
                log("  No 'Select' found on page!")
                log(f"  First 300 chars: {page_text[:300]}")
                consecutive_fails += 1
                time.sleep(3)
                continue

            # Click Select
            log("  Clicking 'Select'...")
            clicked = page.evaluate("""() => {
                // Try exact match on leaf text nodes
                const all = document.querySelectorAll('a, span, div, button, p');
                for (const el of all) {
                    if (el.childNodes.length === 1 &&
                        el.childNodes[0].nodeType === 3 &&
                        el.textContent.trim() === 'Select') {
                        el.click();
                        return 'clicked ' + el.tagName + ' (exact)';
                    }
                }
                // Broader: any visible element with Select text
                for (const el of all) {
                    if (el.textContent.trim() === 'Select' &&
                        el.offsetParent !== null &&
                        el.getBoundingClientRect().width > 0) {
                        el.click();
                        return 'clicked ' + el.tagName + ' (broad)';
                    }
                }
                return 'not found';
            }""")
            log(f"  Result: {clicked}")

            if 'not found' in clicked:
                consecutive_fails += 1
                continue

            time.sleep(3)

            # Take screenshot after entering selection mode
            try:
                page.screenshot(path=os.path.expanduser(f"~/Desktop/insta_debug_select{round_num}.png"))
            except Exception:
                pass

            # Select items by clicking thumbnails
            log("  Selecting items...")
            selected = page.evaluate("""() => {
                let count = 0;
                const maxSel = 50;
                const seen = new Set();

                // Get all images on page
                const imgs = document.querySelectorAll('img');
                for (const img of imgs) {
                    if (count >= maxSel) break;

                    const rect = img.getBoundingClientRect();
                    // Grid thumbnails: reasonably sized, below header
                    if (rect.width > 80 && rect.height > 80 && rect.top > 140 && rect.left > 300) {
                        const id = Math.round(rect.left) + '_' + Math.round(rect.top);
                        if (seen.has(id)) continue;
                        seen.add(id);

                        // Click the image itself
                        img.click();
                        count++;
                    }
                }
                return count;
            }""")
            log(f"  Clicked {selected} thumbnails")

            if selected == 0:
                # Try alternative: click parent divs
                selected = page.evaluate("""() => {
                    let count = 0;
                    const divs = document.querySelectorAll('div[role="button"]');
                    for (const d of divs) {
                        if (count >= 50) break;
                        const r = d.getBoundingClientRect();
                        if (r.width > 80 && r.height > 80 && r.top > 140 && r.left > 300) {
                            d.click();
                            count++;
                        }
                    }
                    return count;
                }""")
                log(f"  Alt method: clicked {selected} divs")

            if selected == 0:
                log("  Could not select any items!")
                try:
                    page.screenshot(path=os.path.expanduser(f"~/Desktop/insta_debug_noselect{round_num}.png"))
                except Exception:
                    pass
                consecutive_fails += 1
                continue

            time.sleep(2)

            # Screenshot after selection
            try:
                page.screenshot(path=os.path.expanduser(f"~/Desktop/insta_debug_selected{round_num}.png"))
            except Exception:
                pass

            # Check for Unlike button
            unlike_text = page.evaluate("""() => {
                const all = document.querySelectorAll('button, div[role="button"], a, span');
                const found = [];
                for (const el of all) {
                    const t = el.textContent.trim();
                    if (t.toLowerCase().includes('unlike') || t.toLowerCase().includes('deselect') || t.toLowerCase().includes('remove')) {
                        found.push(el.tagName + ': ' + t.substring(0, 30));
                    }
                }
                return found.join(' | ') || 'none found';
            }""")
            log(f"  Unlike-related buttons: {unlike_text}")

            # Click Unlike
            unlike_result = page.evaluate("""() => {
                const btns = document.querySelectorAll('button, div[role="button"]');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Unlike') {
                        b.click();
                        return 'clicked';
                    }
                }
                // Try case-insensitive
                for (const b of btns) {
                    if (b.textContent.trim().toLowerCase() === 'unlike') {
                        b.click();
                        return 'clicked (case-insensitive)';
                    }
                }
                return 'not found';
            }""")
            log(f"  Unlike button: {unlike_result}")

            if 'not found' in unlike_result:
                try:
                    page.screenshot(path=os.path.expanduser(f"~/Desktop/insta_debug_nounlike{round_num}.png"))
                except Exception:
                    pass
                consecutive_fails += 1
                continue

            time.sleep(3)

            # Confirm dialog
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Unlike') { b.click(); return; }
                }
            }""")
            time.sleep(2)

            total_unliked += selected
            consecutive_fails = 0
            log(f"  Unliked! Total so far: {total_unliked}\n")
            time.sleep(5)

        print()
        print("=" * 50)
        if total_unliked > 0:
            log(f"DONE! Unliked {total_unliked} items total.")
            log("Run the script again if you have more!")
        else:
            log("Could not unlike items automatically.")
            log("")
            log("Please send me the screenshots from your Desktop:")
            log("  (files named insta_debug_*.png)")
            log("I'll use them to fix the script for your account.")
        print("=" * 50)
        print()

        input("Press ENTER to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
