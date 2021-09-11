import json
import os
import secrets

from flask import (
    Flask, request, abort, session, render_template, redirect, url_for, flash,
    send_from_directory
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

PATH_IMAGES = PATH_DATA / 'images'
if not PATH_IMAGES.is_dir():
    PATH_IMAGES.mkdir()


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
    return render_template(
        'index.html',
        num_images=len(list(PATH_IMAGES.iterdir()))
    )


@public
@app.route('/login', methods=['GET', 'POST'])
def login():
    endpoint_next = request.args.get('next')
    if request.method == "POST":

        session['user'] = PASSWORDS.get(request.form.get('password'))
        if not session.get('user'):
            flash("Incorrect password")
            return redirect(url_for('login', next=endpoint_next))
        flash(f"Welcome to Athens {session['user'].title()}!")

        if endpoint_next and endpoint_next in app.view_functions:
            return redirect(url_for(endpoint_next))

        return redirect(url_for('index'))

    return render_template('login.html', next=endpoint_next)


@public
@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully logged out.")
    return redirect(url_for('index'))


@app.route('/image/<string:filename>')
def image(filename):
    return send_from_directory(PATH_IMAGES, filename)


@app.route('/image/queue/<int:num>')
def image_at_index(num):
    images = list(PATH_IMAGES.iterdir())
    return send_from_directory(PATH_IMAGES, images[num].name)


@app.route('/queue/<int:num>')
def image_queue(num):
    images = list(PATH_IMAGES.iterdir())
    if num >= len(images):
        flash("Index outside of current image queue.")
        return redirect(url_for('index'))
    return render_template('queue.html', num=num)


@public
@app.route('/test/generate')
def test_generate():
    num = 30
    if 'num' in request.args and request.args['num'].isdigit():
        num = int(request.args['num'])

    from PIL import Image, ImageDraw
    import random

    width_min, width_max = 400, 1920
    height_min, height_max = 300, 1200

    index_offset = max([0] + [int(p.stem) for p in PATH_IMAGES.iterdir()])

    for ii in range(num):

        ii += index_offset
        size = (
            random.randint(width_min, width_max),
            random.randint(width_min, width_max)
        )
        colors = [(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        ) for _ in range(5)]

        image = Image.new(mode="RGB", size=size, color=(0,0,0))
        draw = ImageDraw.Draw(image)

        draw.rectangle(((0, 0),size), fill=colors[0])

        size_border = 10
        size_square = (size[0]-(2*size_border))/31
        coord_x, coord_y = (size_border, size_border)
        square_draw = True
        while coord_y + size_square <= size[1]:
            coord_x = size_border
            while coord_x + size_square <= size[0]:
                if square_draw:
                    draw.rectangle(
                        (
                            (coord_x, coord_y),
                            (coord_x+size_square, coord_y+size_square),
                        ),
                        fill=colors[1]
                    )
                coord_x += size_square
                square_draw = not square_draw
            coord_y += size_square

        image.save(PATH_IMAGES / f'{ii:04d}.png')

    flash(f"Generated {num} images")

    return redirect(url_for('index'))


def run():
    os.environ['FLASK_ENV'] = 'development'
    app.run("0.0.0.0", debug=True)
