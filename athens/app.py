import json
import os
import secrets

from flask import (
    Flask, request, abort, session, render_template, redirect, url_for, flash
)
from pathlib import Path

app = Flask(__name__)

PATH_ROOT = Path(__file__).parent.parent
PATH_DATA = Path(os.getenv('PATH_ATHENS_DATA', PATH_ROOT / 'data'))
if not PATH_DATA.is_dir():
    PATH_DATA.mkdir()

PATH_SECRET = PATH_DATA / 'secret.txt'
if not PATH_SECRET.is_file():
    PATH_SECRET.write_text(secrets.token_hex())
app.secret_key = PATH_SECRET.read_text()

PATH_PASSWORDS = PATH_DATA / 'passwords.json'
if not PATH_PASSWORDS.is_file():
    PATH_PASSWORDS.write_text(json.dumps({}, indent=2))
PASSWORDS = {p:u for u,p in json.loads(PATH_PASSWORDS.read_text()).items()}


def public(method):
    method.public = True
    return method


@app.before_request
def check_auth():

    def need_login():
        if request.endpoint not in app.view_functions:
            abort(404)
        if request.endpoint.startswith('static'):
            return False
        if getattr(app.view_functions[request.endpoint], 'public', False):
            return False
        if session.get('user'):
            return False
        return True

    if need_login():
        return redirect(url_for('login', next=request.endpoint))


@app.route('/')
def index():
    return render_template('index.html')


@public
@app.route('/login', methods=['GET', 'POST'])
def login():
    endpoint_next = request.args.get('next')
    if request.method == "POST":

        session['user'] = PASSWORDS.get(request.form.get('password'))
        if not session.get('user'):
            flash("Incorrect password")
            return redirect(url_for('login', next=endpoint_next))

        if endpoint_next and endpoint_next in app.view_functions:
            return redirect(url_for(endpoint_next))

        return redirect(url_for('index'))

    return render_template('login.html', next=endpoint_next)


@public
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def run():
    os.environ['FLASK_ENV'] = 'development'
    app.run("0.0.0.0", debug=True)
