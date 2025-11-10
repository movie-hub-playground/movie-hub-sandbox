from app import db


class Fakenodo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=True, default="draft")
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), nullable=False)
    dataset = db.relationship("BaseDataset", back_populates="fakenodo", lazy=True)

    def __repr__(self):
        return f'Fakenodo<{self.id}>'
