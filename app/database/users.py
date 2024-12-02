from app import db
from ..database import Base


class TblUsers(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(40), nullable=False, unique=True)
    user_name = db.Column(db.String(45), nullable=False)
    #    finder_name = db.Column(db.String(45), nullable=True)
    user_rolle = db.Column(db.String(1), nullable=False)
    user_kontakt = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_mail": self.user__mail,
        }
