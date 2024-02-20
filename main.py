from flask import Flask, render_template, redirect
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, db, firestore
import asyncio
import threading
from datetime import datetime, timedelta, timezone


app = Flask(__name__)
events, products = [], []
checktime = datetime.max
data_lock = threading.Lock()

def GetGoogleSheets():

    # Fetch the service account key JSON file contents
    cred = credentials.Certificate('sheetviewerkey.json')

    # Initialize the app with a service account, granting admin privileges

    if firebase_admin._apps.__len__() == 0:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    prods = []
    prodocuments =  db.collection(u'prods').stream()
    for document in prodocuments:
        doc_dict = document.to_dict()  # Fetch document data once to optimize
        prods.append({
            "name": doc_dict["name"],
            "price": f"R${doc_dict['price']}",
            "details": doc_dict["details"],
            "imglink": f"static/img/{doc_dict['imglink']}",
            "id": document.id
        })

    events = []
    eventdocuments = db.collection(u'events').stream()
    for document in eventdocuments:
        doc_dict = document.to_dict()
        events.append({
            "name": doc_dict["name"],
            "date": doc_dict["date"],
            "details": doc_dict["details"],
            "imglink": f"static/img/{doc_dict['imglink']}",
            "dtlink": doc_dict["dtlink"],
            "isMain": False  # Initialize all events as not main
        })

    # Make 'now' timezone-aware, matching Firestore's UTC timezone
    now = datetime.now(timezone.utc)
    closest_delta = timedelta.max
    closest_event_index = None

    for index, event in enumerate(events):
        event_time = event["date"]  # Directly use the datetime object
        delta = event_time - now
        if delta < timedelta(0):
            event['date'] = f"{event_time.day}/{event_time.month}/{event_time.year}"
        else:
            months = delta.days // 30  # Calculate approximate months
            days = delta.days % 30  # Calculate the remainder of days

            # Event is in the future and closer than any previously found
            event['date'] = f"{months} {'month' if months <= 1 else 'months'}, {days} {'day' if days <= 1 else 'days'} from now"

    # Check if this event is the closest future event so far
            if delta < closest_delta:
                # Mark previous closest event as not main if it exists
                if closest_event_index is not None:
                    events[closest_event_index]["isMain"] = False

                closest_delta = delta
                closest_event_index = index
                event["isMain"] = True

    # Ensure only the closest event is marked as main after the loop
    if closest_event_index is not None:
        for index, event in enumerate(events):
            event["isMain"] = index == closest_event_index

    return events, prods


@app.template_filter('first_words')
def first_words(s, count=2):
    return ' '.join(s.split()[:count])



@app.route('/')
def about():
    global events, products, checktime

    

    if (checktime - datetime.now()) > timedelta(minutes=10):
        with data_lock:
            print(data_lock)
            events, products = GetGoogleSheets()
            checktime = datetime.now()
    return render_template("index.html")


@app.route('/loja')
def store():
    global events, products, checktime
    if (checktime - datetime.now()) > timedelta(minutes=10):
        with data_lock:
            events, products = GetGoogleSheets()
            checktime = datetime.now()
    return render_template("loja.html", products=products)

@app.route('/eventos')
def events():
    global events, products, checktime
    if (checktime - datetime.now()) > timedelta(minutes=10):
        with data_lock:
            events, products = GetGoogleSheets()
            checktime = datetime.now()
    return render_template("eventos.html", events=events)


@app.route('/admin')
def admin():
    global events, products, checktime
    if (checktime - datetime.now()) > timedelta(minutes=10):
        with data_lock:
            events, products = GetGoogleSheets()
            checktime = datetime.now()
    return render_template("admin.html", events=events, products=products)


if __name__ == '__main__':

    app.run(debug=True)
