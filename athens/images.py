from athens.config import PATH_IMAGES

def num_in_queue(session):
    return len(list(PATH_IMAGES.iterdir()))

def name_for(session, num):
    return list(PATH_IMAGES.iterdir())[num].name
