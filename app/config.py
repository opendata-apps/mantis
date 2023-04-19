import os


class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://mantis_user:mantis@localhost/mantis_tracker'
    #SQLALCHEMY_DATABASE_URI = 'postgresql://vubzupvf:abchz7rL5bXbPaWG-7Zx66_FBCRpb8o9@snuffleupagus.db.elephantsql.com/vubzupvf'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAP_CENTER_LONGITUDE = -122.4194
    MAP_CENTER_LATITUDE = 37.7749
    MAP_ZOOM = 1
    SECRET_KEY = os.urandom(24)
