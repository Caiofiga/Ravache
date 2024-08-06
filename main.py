from flask import Flask, render_template, redirect, request, session, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_bootstrap import Bootstrap5
import firebase_admin
import wtforms
import secrets
import os 
from firebase_admin import credentials, db, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import asyncio
import threading
import base64
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
events, products = [], []
revalidate = False
checktime = datetime.max
data_lock = threading.Lock()
bcrypt = Bcrypt(app)
# Bootstrap-Flask requires this line
bootstrap = Bootstrap5(app)
# Flask-WTF requires this line
csrf = CSRFProtect(app)
loginManager = LoginManager()
loginManager.init_app(app)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = wtforms.BooleanField('Remember Me')
    submit = SubmitField('Login')

 # Fetch the service account key JSON file contents
cred = credentials.Certificate('sheetviewerkey.json')

 

#user class that extends usermixins
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


    @loginManager.user_loader
    def get(user_id):
        user_dict = db.collection(u'users').document(user_id).get()
        if user_dict.exists:
            user_data = user_dict.to_dict()
            user = User(id=user_dict.id, username=user_data['username'], password=user_data['password'])
            return user
        return None

if firebase_admin._apps.__len__() == 0:
    firebase_admin.initialize_app(cred)
db = firestore.client()

def GetGoogleSheets():

   
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
            'id': document.id,
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
    if s is not None:
        return ' '.join(s.split()[:count])

@loginManager.unauthorized_handler
def unauthorized():
    return redirect('/login')

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

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.ico', mimetype='image')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    global events, products, checktime, revalidate

    if request.method == 'POST':
        print('yee')
        if 'deleteEventButton' in request.form:
            print(request.form['deleteEventButton'])
        else:
            pass # unknown
    elif request.method == 'GET':
        if (checktime - datetime.now()) > timedelta(minutes=10) or revalidate:
            with data_lock:
                events, products = GetGoogleSheets()
                checktime = datetime.now()
                revalidate = False
                print('revalidated')
        if request.cookies.get('admin') == 'true':
            return render_template("admin.html", events=events, products=products)
        else: login()
        return render_template("admin.html", events=events, products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        queries = db.collection(u'users').where(filter=FieldFilter("username", "==", form.username.data)).stream()
        user_dict = None
        for query in queries:
            user_dict = query.to_dict()
            user_dict['id'] = query.id
            break
        if user_dict is None:
            flash ('User not found')
            return render_template("login.html", form=form)
        if bcrypt.check_password_hash(user_dict['password'], form.password.data):
            user = User(user_dict['id'], user_dict['username'], user_dict['password'])
            login_user(user, remember=form.remember.data if form.remember.data else False)
            if user.is_authenticated:
                return redirect('/admin')
        
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    user = "xa"
    password = "xa"
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_ref = db.collection(u'users').document()
    user_ref.set({
        u'username': user,
        u'password': hashed_password
    })
    return "0"

@app.route('/add', methods=['POST'])
def add():
    global events, products, checktime, revalidate
    if request.method == 'POST':
        match request.form.get('type'):
            case 'event':
                try:
                    eventtoadd = eventtoadd(request.form.get('name'), request.form.get('date'), request.form.get('details'), request.form.get('imageb64'))
                    newdoc = db.collection(u'prods').document()
                    newdoc.set({
                        u'name': eventtoadd.name,
                        u'date': eventtoadd.date,
                        u'details': eventtoadd.details,
                        u'imglink': eventtoadd.imglink
                    })

                    #db.collection(u'prods').document(request.form.get('id')).delete()
                    print("Received")
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + str(e)
            case 'product':
                try:
                    print(request.form.get('db'))
                    prodtoadd = Newproduct(request.form.get('name'), request.form.get('price'), request.form.get('details'), request.form.get('imageb64'))
                    newdoc = db.collection(u'prods').document()
                    newdoc.set({
                        u'name': prodtoadd.name,
                        u'price': prodtoadd.price,
                        u'details': prodtoadd.details,
                        u'imglink': prodtoadd.imglink
                    })

                    #db.collection(u'prods').document(request.form.get('id')).delete()
                    print("Received")
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + str(e)

@app.route('/delete', methods=['POST'])
def delete():
    global events, products, checktime, revalidate
    if request.method == 'POST':
        match request.form.get('type'):
            case 'event':
                try:
                    db.collection(u'events').document(request.form.get('id')).delete()
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + e
            case 'product':
                try:
                    db.collection(u'prods').document(request.form.get('id')).delete()
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + e
   
class Newproduct():
    def __init__(self, name, price, details, imgb64):
        sanitized_name = name.replace('\\', '_')
        self.name = sanitized_name
        self.price = price
        self.details = details
        with open(f'static/img/{self.name}.png', 'wb') as f:
            f.write(base64.b64decode(imgb64))
            self.imglink = f'{self.name}.png'

class NewEvent():
    def __init__(self, name, date, details, imgb64):
        sanitized_name = name.replace('\\', '_')
        self.name = sanitized_name
        self.date = date
        self.details = details
        with open(f'static/img/{self.name}.png', 'wb') as f:
            f.write(base64.b64decode(imgb64))
            self.imglink = f'{self.name}.png'






if __name__ == '__main__':

    app.run(debug=True)
