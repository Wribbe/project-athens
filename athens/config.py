import json
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

PATH_PASSWORDS = PATH_DATA / 'passwords.json'
if not PATH_PASSWORDS.is_file():
    PATH_PASSWORDS.write_text(json.dumps({}, indent=2))
PASSWORDS = {p:u for u,p in json.loads(PATH_PASSWORDS.read_text()).items()}

PATH_IMAGES = PATH_DATA / 'images'
if not PATH_IMAGES.is_dir():
    PATH_IMAGES.mkdir()
