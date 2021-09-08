import os

from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return "HELLO WORLD"


def run():
    os.environ['FLASK_ENV'] = 'development'
    app.run("0.0.0.0", debug=True)
