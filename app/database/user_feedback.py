from app import db


class TblUserFeedback(db.Model):
    __tablename__ = "user_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    feedback_source = db.Column(db.String(20), nullable=False)
    source_detail = db.Column(db.String(255), nullable=True)

    # Relationship back to the user
    user = db.relationship("TblUsers", back_populates="feedback_source")

    @property
    def feedback_source_display(self) -> str:
        from app.database.feedback_type import FeedbackSource
        return FeedbackSource.get_display_name(self.feedback_source)

    def __repr__(self):
        return f"<UserFeedback id={self.id} user_id={self.user_id} source='{self.feedback_source}'>"

    def to_dict(self):
        from app.database.feedback_type import FeedbackSource

        return {
            "id": self.id,
            "user_id": self.user_id,
            "feedback_source": self.feedback_source,
            "source_type": FeedbackSource.get_display_name(self.feedback_source),
            "source_detail": self.source_detail,
        }
