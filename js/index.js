const TikTokScraper = require('tiktok-scraper');

async function getLatestVideo(userHandle) {
    try {
        const user = await TikTokScraper.getUserProfileInfo(userHandle);
        if (user.collector.length > 0) {
            const latestVideo = user.collector[0];
            console.log(latestVideo);
        } else {
            console.log('No videos found for this user.');
        }
    } catch (error) {
        console.error(error);
    }
}

getLatestVideo('tiktokhandle'); // replace 'tiktokhandle' with the actual TikTok channel handle
