from athens.config import PATH_IMAGES
from athens.db import queue_items


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

    file.save(PATH_IMAGES / file.filename)

    cursor.execute("INSERT INTO image (filename) VALUES (?)", (file.filename,))
    id_file = cursor.lastrowid

    for user in db.users():
        cursor.execute(
            "INSERT INTO queue_item (id_image, id_user) VALUES (?,?)",
            (id_file, user['id'])
        )

    session.commit()
    cursor.close()
