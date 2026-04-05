#!/usr/bin/env python3
"""
Instagram Bulk Reel Unliker v5
Uses Instagram's internal API for reliable unliking.
"""

import time
import sys
import json

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
    print("  Instagram Bulk Reel Unliker v5")
    print("=" * 50)
    print()
    print("This version uses Instagram's internal API")
    print("for reliable unliking that actually works.")
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
        print("=" * 50)
        print("  LOG IN to Instagram in the browser window.")
        print("  Complete ALL steps (password, verification, etc)")
        print("  When you see your Instagram feed, come back here.")
        print("=" * 50)
        print()
        input("Press ENTER here AFTER you are fully logged in...")
        print()

        log("Checking login status...")
        time.sleep(2)

        # Dismiss popups
        for _ in range(3):
            try:
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const t = b.textContent.trim();
                        if (t === 'Not Now' || t === 'Not now' || t === 'Save Info') {
                            b.click(); return true;
                        }
                    }
                    return false;
                }""")
                time.sleep(2)
            except Exception:
                break

        # Get CSRF token and cookies for API calls
        csrf_token = page.evaluate("""() => {
            // Try to get from cookie
            const cookies = document.cookie.split(';');
            for (const c of cookies) {
                const [name, val] = c.trim().split('=');
                if (name === 'csrftoken') return val;
            }
            // Try meta tag
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) return meta.getAttribute('content');
            return null;
        }""")

        if not csrf_token:
            log("Could not get CSRF token. Make sure you're logged in!")
            input("Press ENTER to close...")
            browser.close()
            return

        log(f"Got session token: {csrf_token[:10]}...")

        # Test that we're logged in by fetching user info
        user_check = page.evaluate("""() => {
            return document.cookie.includes('ds_user_id');
        }""")

        if not user_check:
            log("Not properly logged in. Please try again.")
            input("Press ENTER to close...")
            browser.close()
            return

        log("Login confirmed! Starting to fetch liked posts...")
        print()

        total_unliked = 0
        max_id = ""
        empty_rounds = 0

        while empty_rounds < 3:
            # Fetch liked posts using Instagram's internal API
            url_suffix = f"&max_id={max_id}" if max_id else ""
            liked_data = page.evaluate(f"""async () => {{
                try {{
                    const resp = await fetch('https://www.instagram.com/api/v1/feed/liked/?count=50{url_suffix}', {{
                        method: 'GET',
                        headers: {{
                            'X-CSRFToken': '{csrf_token}',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-IG-App-ID': '936619743392459',
                        }},
                        credentials: 'include',
                    }});
                    if (!resp.ok) return {{ error: resp.status + ' ' + resp.statusText }};
                    const data = await resp.json();
                    return data;
                }} catch(e) {{
                    return {{ error: e.message }};
                }}
            }}""")

            if not liked_data or "error" in liked_data:
                error_msg = liked_data.get("error", "unknown") if liked_data else "no response"
                log(f"Error fetching liked posts: {error_msg}")

                if "429" in str(error_msg) or "rate" in str(error_msg).lower():
                    log("Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                    continue

                empty_rounds += 1
                time.sleep(5)
                continue

            items = liked_data.get("items", [])
            next_max_id = liked_data.get("next_max_id", "")
            more_available = liked_data.get("more_available", False)

            if not items:
                log("No more liked posts found!")
                break

            log(f"Found {len(items)} liked posts in this batch")

            # Unlike each post
            for i, item in enumerate(items):
                media_id = item.get("id") or item.get("pk") or item.get("media_id")
                if not media_id:
                    continue

                # Convert pk to proper media_id format if needed
                media_pk = str(item.get("pk", media_id))

                unlike_result = page.evaluate(f"""async () => {{
                    try {{
                        const resp = await fetch('https://www.instagram.com/api/v1/web/likes/' + '{media_pk}' + '/unlike/', {{
                            method: 'POST',
                            headers: {{
                                'X-CSRFToken': '{csrf_token}',
                                'X-Requested-With': 'XMLHttpRequest',
                                'X-IG-App-ID': '936619743392459',
                                'Content-Type': 'application/x-www-form-urlencoded',
                            }},
                            credentials: 'include',
                        }});
                        if (!resp.ok) return {{ error: resp.status }};
                        return {{ success: true }};
                    }} catch(e) {{
                        return {{ error: e.message }};
                    }}
                }}""")

                if unlike_result and unlike_result.get("success"):
                    total_unliked += 1
                    caption = ""
                    try:
                        caption = item.get("caption", {}).get("text", "")[:40] if item.get("caption") else ""
                    except Exception:
                        pass
                    if (i + 1) % 5 == 0 or i == 0:
                        log(f"  Unliked {i+1}/{len(items)} in batch (total: {total_unliked})")
                else:
                    error = unlike_result.get("error", "unknown") if unlike_result else "no response"
                    log(f"  Failed to unlike item {i+1}: {error}")

                    if "429" in str(error):
                        log("  Rate limited! Waiting 60 seconds...")
                        time.sleep(60)
                    elif "400" in str(error) or "403" in str(error):
                        # Try alternate endpoint
                        unlike_result2 = page.evaluate(f"""async () => {{
                            try {{
                                const resp = await fetch('https://www.instagram.com/web/likes/' + '{media_pk}' + '/unlike/', {{
                                    method: 'POST',
                                    headers: {{
                                        'X-CSRFToken': '{csrf_token}',
                                        'X-Requested-With': 'XMLHttpRequest',
                                    }},
                                    credentials: 'include',
                                }});
                                if (!resp.ok) return {{ error: resp.status }};
                                return {{ success: true }};
                            }} catch(e) {{
                                return {{ error: e.message }};
                            }}
                        }}""")
                        if unlike_result2 and unlike_result2.get("success"):
                            total_unliked += 1

                # Delay between unlikes to avoid rate limiting
                time.sleep(1.5)

            log(f"Batch complete! Total unliked: {total_unliked}\n")
            empty_rounds = 0

            if more_available and next_max_id:
                max_id = next_max_id
                log("Fetching next batch...")
                time.sleep(5)
            else:
                log("No more liked posts to fetch!")
                break

        print()
        print("=" * 50)
        if total_unliked > 0:
            log(f"DONE! Successfully unliked {total_unliked} posts.")
            log("Check your phone - the likes should be gone now!")
            log("Run the script again if there are more to remove.")
        else:
            log("Could not unlike any posts.")
            log("This might mean:")
            log("  - Your session expired (try logging in again)")
            log("  - Instagram blocked the requests temporarily")
            log("  - The API endpoints have changed")
            log("Please send me a screenshot of what Terminal shows.")
        print("=" * 50)
        print()

        input("Press ENTER to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
