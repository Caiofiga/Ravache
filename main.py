from TikTokApi import TikTokApi
from flask import Flask, request, jsonify, render_template
from playwright.sync_api import BrowserContext, Browser
import os
import asyncio


app = Flask(__name__)

# get your own ms_token from your cookies on tiktok.com
ms_token = "IYN0NbOzlUTlI2-08wAS8eleK9to-eXA-DTWeXtb5A5UdDcB7jBQyGkK6je-bUxaUQC3UH6RhV1nnd2DjrydCurQNiFReePtKEEzu0MiyaY6NZ-zLCHPdi4OvG_jQZBqgQUq_9eMGaVY"
context = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}


async def getVideos():
    async with TikTokApi() as api:

        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=5, headless=True, context_options=context)
        videos = [video async for video in api.user(username="aaaldv").videos()]
        videos.sort(key=lambda x: x['createTime'], reverse=True)
        newest_video = videos[0] if videos else None
        return newest_video


@app.route('/')
def about():
    newest_video = asyncio.run(getVideos())
    return render_template("html/index.html")


if __name__ == '__main__':

    app.run(debug=True)
