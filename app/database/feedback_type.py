from app import db

class TblFeedbackType(db.Model):
    __tablename__ = "feedback_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationship to the user feedback entries (one-to-many)
    user_feedbacks = db.relationship("TblUserFeedback", back_populates="feedback_type_rel")

    def __repr__(self):
        return f"<FeedbackType id={self.id} name='{self.name}'>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        } 