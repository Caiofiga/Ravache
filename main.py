from flask import Flask, render_template, redirect, request, session, flash, send_file, jsonify
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
    username = StringField('Nome do Usuario', validators=[
                           DataRequired(), Length(min=2, max=20)], render_kw={"class": "form-control"})
    password = PasswordField('Senha', validators=[DataRequired()], render_kw={
                             "class": "form-control"})
    remember = wtforms.BooleanField('Remember Me', render_kw={
                                    "class": "form-check-input"})
    submit = SubmitField('Login', render_kw={"class": "btn btn-primary"})

 # Fetch the service account key JSON file contents


class AddUserForm(FlaskForm):
    username = StringField('Nome do Usuario', validators=[
                           DataRequired(), Length(min=2, max=20)], render_kw={"class": "form-control newUserName"})
    password = PasswordField('Senha', validators=[DataRequired()], render_kw={
                             "class": "form-control newUserPassword"})

    submit = SubmitField('Adicionar', render_kw={"class": "btn btn-primary"})

 # Fetch the service account key JSON file contents


cred = credentials.Certificate('sheetviewerkey.json')


# user class that extends usermixins
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
            user = User(
                id=user_dict.id, username=user_data['username'], password=user_data['password'])
            return user
        return None


if firebase_admin._apps.__len__() == 0:
    firebase_admin.initialize_app(cred)
db = firestore.client()


def GetGoogleSheets():

    prods = []
    prodocuments = db.collection(u'prods').stream()
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
            event['date'] = f"{
                event_time.day}/{event_time.month}/{event_time.year}"
        else:
            months = delta.days // 30  # Calculate approximate months
            days = delta.days % 30  # Calculate the remainder of days

            # Event is in the future and closer than any previously found
            event['date'] = f"{months} {'month' if months <= 1 else 'months'}, {
                days} {'day' if days <= 1 else 'days'} from now"

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


@app.route('/admin')
@login_required
def admin():
    adminevents()


@app.route('/adminusers', methods=['GET', 'POST'])
@login_required
def adminusers():

    usersdb = db.collection(u'users').stream()
    users = []
    for user in usersdb:
        users.append(user._data['username'])
    form = AddUserForm()
    if form.validate_on_submit():
        try:
            queries = db.collection(u'users').where(filter=FieldFilter(
                "username", "==", form.username.data)).stream()
            user_exists = False
            for query in queries:
                user_exists = True
                break  # If at least one document is found, the user exists
            if not user_exists:
                hashed_password = bcrypt.generate_password_hash(
                    form.password.data).decode('utf-8')
                new_user = {
                    'username': form.username.data,
                    'password': hashed_password,
                    # Add any other fields you need to store for the user
                }
                db.collection(u'users').add(new_user)
                return render_template('/admin-users.html', form=form, users=users, success=True, username=form.username.data)
                # upload to firestore
            else:
                return render_template("admin-users.html", form=form, users=users, error=True, message="Usuario com esse nome ja existe")
        except Exception as e:
            print(str(e))
            return render_template("admin-users.html", form=form, users=users, error=True, message=str(e))
    return render_template("admin-users.html", form=form, users=users)


@app.route('/adminevents', methods=['GET', 'POST'])
@login_required
def adminevents():
    global events, products, checktime, revalidate

    if request.method == 'POST':
        print('yee')
        if 'deleteEventButton' in request.form:
            print(request.form['deleteEventButton'])
        else:
            pass  # unknown
    elif request.method == 'GET':
        if (checktime - datetime.now()) > timedelta(minutes=10) or revalidate:
            with data_lock:
                events, products = GetGoogleSheets()
                checktime = datetime.now()
                revalidate = False
                print('revalidated')
        if request.cookies.get('admin') == 'true':
            return render_template("admin-eventos.html", events=events)
        else:
            login()
        return render_template("admin-eventos.html", events=events)


@app.route('/adminprods', methods=['GET', 'POST'])
@login_required
def adminprods():
    global events, products, checktime, revalidate

    if request.method == 'POST':
        print('yee')
        if 'deleteEventButton' in request.form:
            print(request.form['deleteEventButton'])
        else:
            pass  # unknown
    elif request.method == 'GET':
        if (checktime - datetime.now()) > timedelta(minutes=10) or revalidate:
            with data_lock:
                events, products = GetGoogleSheets()
                checktime = datetime.now()
                revalidate = False
                print('revalidated')
        if request.cookies.get('admin') == 'true':
            return render_template("admin-prods.html", products=products)
        else:
            login()
        return render_template("admin-prods.html", products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        queries = db.collection(u'users').where(filter=FieldFilter(
            "username", "==", form.username.data)).stream()
        user_dict = None
        for query in queries:
            user_dict = query.to_dict()
            user_dict['id'] = query.id
            break
        if user_dict is None:
            return render_template("login.html", form=form, error=True)
        if bcrypt.check_password_hash(user_dict['password'], form.password.data):
            user = User(user_dict['id'],
                        user_dict['username'], user_dict['password'])
            login_user(
                user, remember=form.remember.data if form.remember.data else False)
            if user.is_authenticated:
                return redirect('/adminevents')

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
                    eventtoadd = NewEvent(request.form.get('name'), request.form.get('price'), request.form.get(
                        'date'), request.form.get('details'), request.form.get('imageb64'), request.form.get('dtlink'))
                    newdoc = db.collection(u'events').document()
                    newdoc.set({
                        u'name': eventtoadd.name,
                        u'date': eventtoadd.date,
                        u'details': eventtoadd.details,
                        u'imglink': eventtoadd.imglink,
                        u'dtlink': eventtoadd.dtlink
                    })

                    # db.collection(u'prods').document(request.form.get('id')).delete()
                    print("Received")
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + str(e)
            case 'product':
                try:
                    print(request.form.get('db'))
                    prodtoadd = Newproduct(request.form.get('name'), request.form.get(
                        'price'), request.form.get('details'), request.form.get('imageb64'))
                    newdoc = db.collection(u'prods').document()
                    newdoc.set({
                        u'name': prodtoadd.name,
                        u'price': prodtoadd.price,
                        u'details': prodtoadd.details,
                        u'imglink': prodtoadd.imglink
                    })

                    # db.collection(u'prods').document(request.form.get('id')).delete()
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
                    db.collection(u'events').document(
                        request.form.get('id')).delete()
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + e
            case 'product':
                try:
                    db.collection(u'prods').document(
                        request.form.get('id')).delete()
                    revalidate = True
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + e
            case 'user':
                try:
                    query = db.collection(u'users').where(
                        filter=FieldFilter('username', '==', request.form.get('id'))).stream()
                    for result in query:
                        db.collection(u'users').document(result.id).delete()
                        break
                except Exception as e:
                    return 'Error 500: ' + str(e)
                return '200'


@app.route('/set', methods=['GET', 'POST'])
def set():
    if request.method == 'GET':
        doc = db.collection(request.args.get('type')).document(
            request.args.get('id')).get()
        response = doc.to_dict()
        response['type'] = request.args.get('type')
        response["code"] = '200'
        return jsonify(response)


@app.route('/update', methods=['POST'])
def update():
    global revalidate
    if request.method == 'POST':
        match request.form.get('type'):
            case 'events':
                try:
                    updatedevent = NewEvent(request.form.get('name'), request.form.get("price"), request.form.get(
                        'date'), request.form.get('details'), request.form.get('imageb64'),
                        request.form.get('dtlink'))
                    if (request.form.get('id') != 'new'):
                        doc = db.collection('events').document(
                            request.form.get('id'))
                        doc.update({
                            u'name': updatedevent.name,
                            u'date': updatedevent.date,
                            u'details': updatedevent.details,
                            u'imglink': updatedevent.imglink,
                            u'dtlink': updatedevent.dtlink,
                            u'price': updatedevent.price,
                        })
                    else:
                        doc = db.collection('events').document()
                        doc.set({
                            u'name': updatedevent.name,
                            u'date': updatedevent.date,
                            u'details': updatedevent.details,
                            u'imglink': updatedevent.imglink,
                            u'dtlink': updatedevent.dtlink,
                            u'price': updatedevent.price,
                        })
                    revalidate = True
                    return "0"
                except Exception as e:
                    return 'Error 500: ' + str(e)
            case 'prods':
                print(request.args)
                try:
                    updateddoc = Newproduct(request.form.get('name'), request.form.get(
                        'price'), request.form.get('details'), request.form.get('imageb64'))
                    if request.form.get('id') != 'new':
                        doc = db.collection(request.form.get('type')).document(
                            request.form.get('id'))
                        doc.update({
                            u'name': updateddoc.name,
                            u'price': updateddoc.price,
                            u'details': updateddoc.details,
                            u'imglink': updateddoc.imglink
                        })
                        revalidate = True
                        return "0"
                    else:
                        doc = db.collection(
                            request.form.get('type')).document()
                        doc.set({
                            u'name': updateddoc.name,
                            u'price': updateddoc.price,
                            u'details': updateddoc.details,
                            u'imglink': updateddoc.imglink
                        })
                        revalidate = True
                        return "0"

                except Exception as e:
                    return 'Error 500: ' + str(e)
            case 'users':
                try:
                    updateduser = {
                        'username': request.form.get('username'),
                        'password': bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
                    }
                    query = db.collection(u'users').where(
                        filter=FieldFilter('username', '==', request.form.get('id'))).stream()
                    for result in query:
                        result.reference.update(updateduser)
                        break
                    return '200'
                except Exception as e:
                    return 'Error 500: ' + str(e)
            case _:
                return 'Error 500: Unknown type: ' + request.form.get('type')


class Newproduct():
    def __init__(self, name, price, details, imgb64):
        sanitized_name = name.replace('\\', '_')
        self.name = sanitized_name
        self.price = int(price)
        self.details = details
        with open(f'static/img/{self.name}.png', 'wb') as f:
            f.write(base64.b64decode(imgb64))
            self.imglink = f'{self.name}.png'


class NewEvent():
    def __init__(self, name, price, date, details, imgb64, dtlink):
        sanitized_name = name.replace('\\', '_')
        self.name = sanitized_name
        self.date = datetime.strptime(date, "%Y-%m-%d")
        self.price = int(price)
        self.details = details
        self.dtlink = dtlink
        with open(f'static/img/{self.name}.png', 'wb') as f:
            f.write(base64.b64decode(imgb64))
            self.imglink = f'{self.name}.png'


if __name__ == '__main__':

    app.run(debug=True)
