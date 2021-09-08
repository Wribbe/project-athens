import os
import secrets

from flask import Flask
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


@app.route('/')
def index():
    return "HELLO WORLD"


def run():
    os.environ['FLASK_ENV'] = 'development'
    app.run("0.0.0.0", debug=True)
