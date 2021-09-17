from athens.config import PATH_IMAGES_UPLOAD, PATH_IMAGES_QUEUE
from athens.db import queue_items
from athens import db

from PIL import Image


def num_in_queue(user):
    return len(queue_items(user))


def action(session, action, num):
    print(
        f"Performing action {action} on image {num} for user "
        f"{session['user']}"
    )


def name_for(user, num):
    return queue_items(user)[num]['filename']


def handle_upload(file):
    session = db.db()
    cursor = session.cursor()

    filepath = PATH_IMAGES_UPLOAD / file.filename
    file.save(filepath)
    create_smaller_copy_for_queue(filepath)

    cursor.execute("INSERT INTO image (filename) VALUES (?)", (file.filename,))
    id_file = cursor.lastrowid

    for user in db.users():
        cursor.execute(
            "INSERT INTO queue_item (id_image, id_user) VALUES (?,?)",
            (id_file, user['id'])
        )

    session.commit()
    cursor.close()


def create_smaller_copy_for_queue(filepath):
    with Image.open(filepath) as im:
        div_factor = im.width // 360
        im_resized = im.resize(
            (im.width // div_factor, im.height // div_factor)
        )
        im_resized.save(PATH_IMAGES_QUEUE / filepath.name)
