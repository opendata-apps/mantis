import hashlib
from datetime import datetime
from random import randint


def get_new_id(organisation="Naturkundemusum-Potsdam"):
    "Construct an id with ramndom values"

    randomint = randint(0, 1000000)
    randomsom = str(randomint)
    now = datetime.now()
    currenttime = now.strftime(format="%Y-%m-%d %H:%M:%S")
    var = f"{currenttime}_{organisation}_{randomsom}"
    string = var.encode("utf-8")
    hash_object = hashlib.sha1(string).hexdigest()
    return hash_object
