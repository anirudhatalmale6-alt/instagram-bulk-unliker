// Instagram Bulk Reel Unliker - Browser Console Script
// Paste this into the browser console on the Your Activity > Likes page

(async function() {
    const DELAY = (ms) => new Promise(r => setTimeout(r, ms));
    let totalUnliked = 0;

    while (true) {
        // Step 1: Click "Select" button
        const selectBtn = [...document.querySelectorAll('*')].find(
            el => el.textContent.trim() === 'Select' && el.offsetParent !== null &&
                  el.childNodes.length === 1 && el.childNodes[0].nodeType === 3
        );

        if (!selectBtn) {
            console.log('No "Select" button found. You may have no more liked content!');
            console.log('Total unliked: ' + totalUnliked);
            alert('Done! Unliked ' + totalUnliked + ' items total. If there are more, refresh the page and run the script again.');
            break;
        }

        selectBtn.click();
        console.log('Clicked Select...');
        await DELAY(2000);

        // Step 2: Click on thumbnails to select them (up to 50)
        let selected = 0;
        const images = document.querySelectorAll('img[src*="instagram"]');
        const clickedElements = new Set();

        for (const img of images) {
            if (selected >= 50) break;
            // Walk up to find the clickable container
            let container = img;
            for (let i = 0; i < 5; i++) {
                if (container.parentElement) container = container.parentElement;
            }
            // Only click items in the main grid area (not profile pics, nav icons)
            const rect = container.getBoundingClientRect();
            if (rect.width > 100 && rect.height > 100 && rect.top > 100 && !clickedElements.has(container)) {
                container.click();
                clickedElements.add(container);
                selected++;
                await DELAY(300);
            }
        }

        // Also try clicking div[role="button"] elements in the grid
        if (selected === 0) {
            const buttons = document.querySelectorAll('div[role="button"]');
            for (const btn of buttons) {
                if (selected >= 50) break;
                const rect = btn.getBoundingClientRect();
                if (rect.width > 100 && rect.height > 100 && rect.top > 150 && !clickedElements.has(btn)) {
                    btn.click();
                    clickedElements.add(btn);
                    selected++;
                    await DELAY(300);
                }
            }
        }

        console.log('Selected ' + selected + ' items');

        if (selected === 0) {
            console.log('Could not select any items.');
            alert('Could not select items. Total unliked so far: ' + totalUnliked);
            break;
        }

        await DELAY(1500);

        // Step 3: Click "Unlike" button
        const unlikeBtn = [...document.querySelectorAll('button')].find(
            el => el.textContent.trim() === 'Unlike'
        );

        if (!unlikeBtn) {
            console.log('Unlike button not found');
            alert('Unlike button not found. Total unliked so far: ' + totalUnliked);
            break;
        }

        unlikeBtn.click();
        console.log('Clicked Unlike...');
        await DELAY(2000);

        // Step 4: Handle confirmation dialog
        const confirmBtn = [...document.querySelectorAll('button')].find(
            el => el.textContent.trim() === 'Unlike'
        );
        if (confirmBtn) {
            confirmBtn.click();
            await DELAY(2000);
        }

        totalUnliked += selected;
        console.log('Batch done! Total unliked: ' + totalUnliked);

        // Wait before next batch
        await DELAY(5000);

        // Reload the page for fresh content
        window.location.reload();
        await DELAY(5000);
    }
})();
