from app import db
from sqlalchemy.orm import relationship

class TblUsers(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(40), nullable=False)
    user_name = db.Column(db.String(45), nullable=False)
    user_rolle = db.Column(db.String(1), nullable=False)
    user_kontakt = db.Column(db.String(45), nullable=True)

    # Relationship to the feedback source
    feedback_source = relationship(
        "TblUserFeedback", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.id} ({self.user_name})>"

    def to_dict(self):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_kontakt": self.user_kontakt,
            "user_rolle": self.user_rolle,
        }
        if self.feedback_source:
            data["feedback_source"] = self.feedback_source.to_dict()
        return data
