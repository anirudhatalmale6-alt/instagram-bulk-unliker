# Instagram Bulk Reel Unliker

A simple one-time tool to unlike all your liked Reels on Instagram.

## Setup (macOS)

### Step 1: Install Python (if not already installed)
Open **Terminal** (press Cmd + Space, type "Terminal", hit Enter) and run:

```
python3 --version
```

If you see a version number, you're good. If not, install it:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

### Step 2: Install the required tool
In Terminal, run these two commands one by one:

```
pip3 install playwright
python3 -m playwright install chromium
```

### Step 3: Run the script
In Terminal, run:

```
python3 bulk_unlike_reels.py
```

## How It Works

1. A Chrome browser window will open
2. You log in to Instagram normally (your password stays in the browser, the script never sees it)
3. The script navigates to Your Activity > Likes
4. It selects items in batches and clicks "Unlike" for you
5. Repeats until all liked Reels are removed

## Important Notes

- **Keep the browser window visible** while the script runs
- **Do not click anything** in the browser while the script is working
- The process adds small delays between actions to avoid triggering Instagram's rate limits
- If Instagram temporarily blocks actions, wait 15-30 minutes and run the script again
- Your login credentials are entered directly in the browser - the script never sees or stores them

## iOS Alternative

There is no way to run this script directly on iOS. Your options:
1. Run it on your Mac (recommended)
2. Use Instagram's built-in feature: Settings > Your Activity > Interactions > Likes > Select > Unlike (manual but works on iOS)
