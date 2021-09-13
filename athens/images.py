from athens.config import PATH_IMAGES

def num_in_queue(session):
    return len(list(PATH_IMAGES.iterdir()))

def action(session, action, num):
    print(
        f"Performing action {action} on image {num} for user "
        f"{session['user']}"
    )

def name_for(session, num):
    return list(PATH_IMAGES.iterdir())[num].name
