from datetime import datetime


class Config:
    TESTING = True
    URI = 'postgresql://mantis_user:mantis@localhost/mantis_tester'
    SQLALCHEMY_DATABASE_URI = URI
    INITIAL_DATA = [
        (1, 'Im Haus'),
        (2, 'Im Garten'),
        (3, 'Auf dem Balkon/auf der Terrasse'),
        (4, 'Am Fenster/an der Hauswand'),
        (5, 'Industriebrache'),
        (6, 'Im Wald'),
        (7, 'Wiese/Weide'),
        (8, 'Heidelandschaft'),
        (9, 'Straßengraben/Wegesrand/Ruderalflur'),
        (10, 'Gewerbegebiet'),
        (11, 'Im oder am Auto'),
        (99, 'Anderer Fundort')
    ]

    CURRENT_YEAR = datetime.now().year
    MIN_MAP_YEAR = 2025
    CELEBRATION_THRESHOLD = 10000
