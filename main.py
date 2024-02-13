from flask import Flask, request, jsonify, render_template
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, db, firestore
import asyncio


app = Flask(__name__)

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
    events.sort(key=lambda x: x['date'], reverse=True)
    events[0]["isMain"] = True

    return events, prods


@app.route('/')
def about():
    #tiktokid = asyncio.run(getTiktokVideos())
    tiktokvideo = "https://www.tiktok.com/@aaaldv.einstein/video/7312864902778080518"
    tiktokid = "7312864902778080518"
    events, products = GetGoogleSheets()
    return render_template("index.html", events=events, products=products, tiktokvideo=tiktokvideo, tiktokid=tiktokid)


@app.route('/admin')
def admin():
    return render_template("admin.html")


if __name__ == '__main__':

    app.run(debug=True)
