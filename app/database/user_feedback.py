from app import db
from sqlalchemy.orm import relationship

class TblUserFeedback(db.Model):
    __tablename__ = "user_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    feedback_type_id = db.Column(
        db.Integer, db.ForeignKey("feedback_types.id"), nullable=False
    )

    source_detail = db.Column(db.String(255), nullable=True)

    # Relationship back to the user
    user = db.relationship("TblUsers", back_populates="feedback_source")

    # Relationship to the lookup table
    source_type_rel = relationship("TblFeedbackSourceType", back_populates="user_feedbacks")

    def __repr__(self):
        source_name = self.source_type_rel.name if self.source_type_rel else 'Unknown'
        return f"<UserFeedback id={self.id} user_id={self.user_id} source='{source_name}'>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source_type": self.source_type_rel.name if self.source_type_rel else None, 
            "source_detail": self.source_detail,
            "feedback_source_type_id": self.feedback_source_type_id # Optionally include the ID
        } 