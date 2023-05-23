

class Mantis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'photo_url': self.photo_url
        }