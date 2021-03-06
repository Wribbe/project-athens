import os

from athens import images, db
from athens.config import (
    app, PASSWORDS, PATH_IMAGES, PATH_IMAGES_QUEUE, PATH_IMAGES_UPLOAD, ACTIONS
)

from flask import (
    request, abort, session, render_template, redirect, url_for, flash,
    send_from_directory
)

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
        num_images=images.num_in_queue(session.get('user'))
    )


@public
@app.route('/login', methods=['GET', 'POST'])
def login():

    if session.get('user'):
        return redirect(url_for('index'))

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


@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully logged out.")
    return redirect(url_for('index'))


@app.route('/image/<int:num>')
def image_at_index(num):
    fullsize = int(request.args.get('fullsize', 0)) == 1
    return send_from_directory(
        PATH_IMAGES_QUEUE if not fullsize else PATH_IMAGES_UPLOAD,
        images.name_for(session.get('user'), num)
    )



@app.route('/queue/', defaults={'num': 0}, methods=["GET", "POST"])
@app.route('/queue/<num>', methods=["GET", "POST"])
def image_queue(num):
    num = int(num)
    user = session.get('user')
    if num < 0 or num >= images.num_in_queue(user):
        flash("Index outside of current image queue.")
        return redirect(url_for('index'))

    if request.method == "POST":
        action = request.form.get('action').lower()
        images.action(session, action, num)
        num = num if action.startswith("rotate_") else num+1
        return redirect(url_for('image_queue', num=num))

    queue_actions = [q['action'] for q in db.queue_items(user)]

    actions = []
    for action in ACTIONS:
        actions.append({
            'value': action,
            'selected': action == queue_actions[num],
        })

    return render_template('queue.html', num=num, actions=actions)


@app.route('/upload', methods=["GET","POST"])
def upload():

    if request.method == "POST":
        for file in request.files.getlist('images'):
            images.handle_upload(file)
        return redirect(url_for('index'))

    return render_template('upload.html')


@app.route('/user/<string:username>', methods=["GET","POST"])
def user_edit(username):

    if session.get('user') != username:
        return redirect(url_for('index'))

    if request.method == "POST":
        form_data = request.form
        if not form_data.get('password', "").strip():
            flash("Password cannot be empty.")
        elif form_data['password'] != form_data['password_confirm']:
            flash("Passwords do not match.")
        else:
            db.password_set(username, form_data['password'])
            flash(f'Password for {username.title()} updated successfully.')
        return redirect(url_for('user_edit', username=username))

    return render_template('user_edit.html', username=username)


@app.route('/test/generate/<int:num>')
def test_generate(num=30):
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
