from TikTokApi import TikTokApi
from flask import Flask, request, jsonify, render_template
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, db, firestore
import asyncio


app = Flask(__name__)

# get your own ms_token from your cookies on tiktok.com
ms_token = "IYN0NbOzlUTlI2-08wAS8eleK9to-eXA-DTWeXtb5A5UdDcB7jBQyGkK6je-bUxaUQC3UH6RhV1nnd2DjrydCurQNiFReePtKEEzu0MiyaY6NZ-zLCHPdi4OvG_jQZBqgQUq_9eMGaVY"
context = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}


async def getTiktokVideos():
    async with TikTokApi() as api:

        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=5, headless=True, context_options=context)
        videos = []
        async for video in api.user(username="aaaldv.einstein").videos():
            videos.append({"create_time": video.create_time, "id": video.id})
            videos.sort(key=lambda x: x['create_time'], reverse=True)
        return videos[0]['id']


def GetGoogleSheets():

    # Fetch the service account key JSON file contents
    cred = credentials.Certificate('sheetviewerkey.json')

    # Initialize the app with a service account, granting admin privileges

    if firebase_admin._apps.__len__() == 0:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    prods = []
    for document in db.collection(u'prods').stream():
        prods.append({
            "name": document.to_dict()["name"],
            "price": document.to_dict()["price"],
            "details": document.to_dict()["details"],
            "imglink": "static/img/"+document.to_dict()["imglink"]
        })

    events = []
    for document in db.collection(u'events').stream():
        events.append({
            "name": document.to_dict()["name"],
            "date": document.to_dict()["date"],
            "details": document.to_dict()["details"],
            "imglink": "static/img/"+document.to_dict()["imglink"],
            "dtlink": document.to_dict()["dtlink"]
        })
    return events, prods


@app.route('/')
def about():
    tiktokid = asyncio.run(getTiktokVideos())
    tiktokvideo = "https://www.tiktok.com/@aaaldv.einstein/video/" + tiktokid
    events, products = GetGoogleSheets()
    return render_template("index.html", events=events, products=products, tiktokvideo=tiktokvideo, tiktokid=tiktokid)


if __name__ == '__main__':

    app.run(debug=True)
