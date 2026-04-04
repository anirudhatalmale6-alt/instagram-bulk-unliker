#!/usr/bin/env python3
"""
Instagram Bulk Reel Unliker v3
Uses JavaScript injection for reliable automation.
"""

import time
import sys

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
    print("  Instagram Bulk Reel Unliker v3")
    print("=" * 50)
    print()
    print("A browser will open. Log in to Instagram.")
    print("The script will start automatically after login.")
    print()
    input("Press ENTER to begin...")
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

        log("Opening Instagram login page...")
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

        log("Waiting for you to log in...")
        log("(Log in normally in the browser window)\n")

        # Wait for login
        while True:
            try:
                url = page.url
                if "instagram.com" in url and "/accounts/login" not in url and "/challenge" not in url:
                    time.sleep(5)
                    if "/accounts/login" not in page.url:
                        break
            except Exception:
                pass
            time.sleep(2)

        log("Login detected!")
        time.sleep(3)

        # Dismiss "Turn on notifications" or "Save info" popups
        for _ in range(3):
            try:
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const t = b.textContent.trim();
                        if (t === 'Not Now' || t === 'Not now' || t === 'Cancel' || t === 'Decline') {
                            b.click(); return true;
                        }
                    }
                    return false;
                }""")
                time.sleep(2)
            except Exception:
                break

        total_unliked = 0
        consecutive_fails = 0

        while consecutive_fails < 3:
            # Navigate to likes page
            log("Going to Your Activity > Likes...")
            page.goto("https://www.instagram.com/your_activity/interactions/likes/",
                       wait_until="domcontentloaded")
            time.sleep(5)

            # Dismiss any popups again
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

            # Check page content
            page_text = page.evaluate("() => document.body ? document.body.innerText : ''")
            log(f"  Page loaded ({len(page_text)} chars)")

            if "Select" not in page_text:
                log("  'Select' not found on page.")
                log(f"  Page text preview: {page_text[:200]}")
                consecutive_fails += 1
                time.sleep(3)
                continue

            # Click Select
            clicked = page.evaluate("""() => {
                const all = document.querySelectorAll('a, span, div, button, p');
                for (const el of all) {
                    if (el.childNodes.length === 1 &&
                        el.childNodes[0].nodeType === 3 &&
                        el.textContent.trim() === 'Select') {
                        el.click();
                        return 'clicked: ' + el.tagName;
                    }
                }
                // Broader search
                for (const el of all) {
                    if (el.textContent.trim() === 'Select' && el.offsetParent !== null) {
                        el.click();
                        return 'clicked-broad: ' + el.tagName;
                    }
                }
                return 'not-found';
            }""")
            log(f"  Select button: {clicked}")

            if 'not-found' in clicked:
                consecutive_fails += 1
                time.sleep(3)
                continue

            time.sleep(3)

            # Select grid items by clicking on them
            selected = page.evaluate("""() => {
                let count = 0;
                const maxSelect = 50;
                const clicked = new Set();

                // Find all images in the grid area
                const allImgs = document.querySelectorAll('img');
                for (const img of allImgs) {
                    if (count >= maxSelect) break;

                    const rect = img.getBoundingClientRect();
                    // Grid images are typically square-ish and in the main content area
                    if (rect.width > 80 && rect.height > 80 && rect.top > 150 && rect.top < 2000) {
                        // Walk up to find clickable parent
                        let target = img;
                        for (let i = 0; i < 6; i++) {
                            if (target.parentElement) target = target.parentElement;
                        }

                        const key = target.innerHTML.substring(0, 50);
                        if (!clicked.has(key)) {
                            // Try clicking the image itself first
                            img.click();
                            clicked.add(key);
                            count++;
                        }
                    }
                }

                if (count === 0) {
                    // Try clicking div containers
                    const divs = document.querySelectorAll('div[role="button"], div[tabindex="0"]');
                    for (const div of divs) {
                        if (count >= maxSelect) break;
                        const rect = div.getBoundingClientRect();
                        if (rect.width > 80 && rect.height > 80 && rect.top > 150) {
                            div.click();
                            count++;
                        }
                    }
                }

                return count;
            }""")

            log(f"  Clicked on {selected} items")

            if selected == 0:
                log("  Could not select any items.")
                consecutive_fails += 1
                time.sleep(3)
                continue

            time.sleep(2)

            # Check if items are actually selected (look for visual indicator or Unlike button)
            has_unlike = page.evaluate("""() => {
                const btns = document.querySelectorAll('button, div[role="button"]');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Unlike') return true;
                }
                return false;
            }""")

            if not has_unlike:
                log("  Unlike button not visible yet. Trying to click thumbnails directly...")
                # Try clicking on the actual thumbnail containers more precisely
                selected2 = page.evaluate("""() => {
                    let count = 0;
                    // Try all possible clickable areas
                    const containers = document.querySelectorAll('div > div > img');
                    for (const img of containers) {
                        if (count >= 50) break;
                        const rect = img.getBoundingClientRect();
                        if (rect.top > 150 && rect.width > 50) {
                            img.parentElement.click();
                            count++;
                        }
                    }
                    return count;
                }""")
                log(f"  Second attempt: clicked {selected2} items")
                time.sleep(2)

                has_unlike = page.evaluate("""() => {
                    const btns = document.querySelectorAll('button, div[role="button"]');
                    for (const b of btns) {
                        if (b.textContent.trim() === 'Unlike') return true;
                    }
                    return false;
                }""")

            if not has_unlike:
                log("  Still no Unlike button. Taking screenshot for debugging...")
                try:
                    import os
                    path = os.path.expanduser("~/Desktop/insta_debug.png")
                    page.screenshot(path=path)
                    log(f"  Screenshot saved to: {path}")
                except Exception:
                    pass
                consecutive_fails += 1
                time.sleep(3)
                continue

            # Click Unlike
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button, div[role="button"]');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Unlike') { b.click(); return; }
                }
            }""")
            log("  Clicked Unlike...")
            time.sleep(3)

            # Confirm dialog if present
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent.trim() === 'Unlike') { b.click(); return; }
                }
            }""")
            time.sleep(2)

            total_unliked += selected
            consecutive_fails = 0
            log(f"  Batch done! Total unliked so far: {total_unliked}\n")
            time.sleep(5)

        print()
        print("=" * 50)
        if total_unliked > 0:
            log(f"DONE! Unliked {total_unliked} items.")
            log("Run the script again if you have more!")
        else:
            log("Could not unlike items automatically.")
            log("Check Desktop for insta_debug.png screenshot")
            log("and send it to me so I can see what's happening.")
        print("=" * 50)
        print()

        input("Press ENTER to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
