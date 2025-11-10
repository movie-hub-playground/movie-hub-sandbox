from enum import Enum
from app import db
from datetime import datetime
from sqlalchemy import Enum as SQLAlchemyEnum
from flask import request
from sqlalchemy.ext.declarative import declared_attr


class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"), nullable=False)
    version_number = db.Column(db.String(20), nullable=False)  # por ejemplo "1.0", "1.1", "2.0"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dataset = db.relationship("BaseDataset", back_populates="versions")

    def __repr__(self):
        return f"<Version {self.version_number} of dataset {self.dataset_id}>"


class BaseDataset(db.Model):
    
    __tablename__ = "base_dataset"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_version = db.Column(db.String(20), default="1.0")
    dataset_type = db.Column(db.String(120), nullable=False)
    files = db.Column(db.JSON, nullable=True)
    total_size_bytes = db.Column(db.Integer, default=0)
    total_size_human = db.Column(db.String(120), default="0 B")

    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), nullable=False)
    ds_meta_data = db.relationship("DSMetaData", backref=db.backref("dataset", uselist=False))

    versions = db.relationship("Version", back_populates="dataset", cascade="all, delete-orphan")
    feature_models = db.relationship("FeatureModel", backref="dataset", lazy=True, cascade="all, delete")
    fakenodo = db.relationship("Fakenodo", back_populates="dataset", lazy=True, cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_on": dataset_type,
        "polymorphic_identity": "base",
    }
    
    def update_files_info(self):
        """Actualiza la información de archivos y tamaños en la BD"""
        from app.modules.dataset.services import SizeService
        
        # Calcular archivos - SIN usar to_dict() que requiere request
        files_list = []
        for fm in self.feature_models:
            for file in fm.files:
                files_list.append({
                    "id": file.id,
                    "name": file.name,
                    "checksum": file.checksum,
                    "size": file.size,
                    "feature_model_id": file.feature_model_id
                })
        
        # Calcular tamaño total
        total_bytes = sum(file.size for fm in self.feature_models for file in fm.files)
        total_human = SizeService().get_human_readable_size(total_bytes)
        
        # Actualizar columnas
        self.files = files_list
        self.total_size_bytes = total_bytes
        self.total_size_human = total_human


    # Métodos genéricos que dependen de la metadata
    def name(self):
        return self.ds_meta_data.title

    def get_cleaned_publication_type(self):
        return self.ds_meta_data.publication_type.name.replace("_", " ").title()

    def files(self):
        return [file for fm in self.feature_models for file in fm.files]

    def get_files_count(self):
        return sum(len(fm.files) for fm in self.feature_models)

    def get_file_total_size(self):
        return sum(file.size for fm in self.feature_models for file in fm.files)

    def get_file_total_size_for_human(self):
        from app.modules.dataset.services import SizeService
        return SizeService().get_human_readable_size(self.get_file_total_size())

    def get_doi(self):
        from app.modules.dataset.services import DataSetService
        return DataSetService().get_dataset_doi(self)
