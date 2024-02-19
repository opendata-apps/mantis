from app import app
from flask_migrate import MigrateCommand, Manager

manager = Manager(app)
manager.add_command("db", MigrateCommand)


if __name__ == "__main__":
    manager.run()
1
