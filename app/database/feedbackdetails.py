from app import db
from ..database import Base


class TblFeedbackDetails(db.Model):
    __tablename__ = 'feedback_details'

    id = db.Column(db.Integer, primary_key=True)
    fb_details = db.Column(db.String(45), nullable=False)


    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "fb_details": self.fb_details,
        }
