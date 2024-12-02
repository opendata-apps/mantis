from app import db
from ..database import Base


class TblFeedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    fb_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    fb_details = db.Column(
        db.Integer, db.ForeignKey("feedback_details.id"), nullable=False)


    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "fb_kontakt": self.fb_kontakt,
            "fb_details": self.fb_details,
        }
