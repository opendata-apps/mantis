from app import db
from database import Base


class TblFundmeldungen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funddatum = db.Column(db.date, nullable=False)
    meldedatum = db.Column(db.date, nullable=False)
    erstbearbeiter = db.Column(db.varchar, nullable=False)
    bearbeitungsdatum = db.Column(db.date, nullable=False)
    bildpfad = db.Column(db.varchar, nullable=False)

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "funddatum": self.funddatum,
            "meldetatum": self.meldedatum,
            "erstbearbeiter": self.erstbearbeiter,
            "bearbeitungsdatum": self.bearbeitungsdatum,
            "bildpfad": self.bildpfad,
        }
