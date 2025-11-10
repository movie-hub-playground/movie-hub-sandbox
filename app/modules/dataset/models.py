from datetime import datetime
from enum import Enum

from flask import request
from sqlalchemy import Enum as SQLAlchemyEnum

from app import db
from app.modules.dataset.base_dataset import BaseDataset


class PublicationType(Enum):
    NONE = "none"
    ANNOTATION_COLLECTION = "annotationcollection"
    BOOK = "book"
    BOOK_SECTION = "section"
    CONFERENCE_PAPER = "conferencepaper"
    DATA_MANAGEMENT_PLAN = "datamanagementplan"
    JOURNAL_ARTICLE = "article"
    PATENT = "patent"
    PREPRINT = "preprint"
    PROJECT_DELIVERABLE = "deliverable"
    PROJECT_MILESTONE = "milestone"
    PROPOSAL = "proposal"
    REPORT = "report"
    SOFTWARE_DOCUMENTATION = "softwaredocumentation"
    TAXONOMIC_TREATMENT = "taxonomictreatment"
    TECHNICAL_NOTE = "technicalnote"
    THESIS = "thesis"
    WORKING_PAPER = "workingpaper"
    OTHER = "other"


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
    fm_meta_data_id = db.Column(db.Integer, db.ForeignKey("fm_meta_data.id"))

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.String(120))
    number_of_features = db.Column(db.String(120))

    def __repr__(self):
        return f"DSMetrics<models={self.number_of_models}, features={self.number_of_features}>"


class DSMetaData(db.Model):
    __tablename__ = "ds_meta_data"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    deposition_id = db.Column(db.Integer)
    
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
    ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
    
    authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")
    
    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "publication_type": self.publication_type.name if self.publication_type else None,
            "publication_doi": self.publication_doi,
            "dataset_doi": self.dataset_doi,
            "tags": self.tags.split(",") if self.tags else [],
            "deposition_id": self.deposition_id,
            "metrics": {
                "number_of_models": self.ds_metrics.number_of_models if self.ds_metrics else None,
                "number_of_features": self.ds_metrics.number_of_features if self.ds_metrics else None,
            },
            "authors": [
                author.to_dict() for author in self.authors
            ] if self.authors else []
        }


class DataSet(BaseDataset):
    __tablename__ = "data_set"
    __mapper_args__ = {"polymorphic_identity": "uvl"}
    
    def to_dict(self):
        from app.modules.dataset.services import SizeService, DataSetService
        """
        Devuelve un diccionario completo con toda la información del dataset UVL:
        - Metadatos (título, descripción, autores, DOIs, tags)
        - Información de sistema (id, fecha, urls, archivos, tamaños, versiones)
        """

        meta = self.ds_meta_data

        # Archivos
        files = [file.to_dict() for fm in self.feature_models for file in fm.files]

        # Tamaños
        total_size_bytes = sum(file.size for fm in self.feature_models for file in fm.files)
        total_size_human = SizeService().get_human_readable_size(total_size_bytes)

        # Construcción del diccionario completo
        data = {
            # Identificación
            "id": self.id,
            "dataset_type": self.dataset_type,
            "current_version": self.current_version,
            "created_at": self.created_at,

            # Metadata
            "title": meta.title if meta else None,
            "description": meta.description if meta else None,
            "authors": [author.to_dict() for author in meta.authors] if meta and meta.authors else [],
            "publication_type": meta.publication_type.name.replace("_", " ").title() if meta and meta.publication_type else None,
            "publication_doi": meta.publication_doi if meta else None,
            "dataset_doi": meta.dataset_doi if meta else None,
            "tags": meta.tags.split(",") if meta and meta.tags else [],
            "deposition_id": meta.deposition_id if meta else None,

            # URLs / DOIs
            "uvlhub_doi": DataSetService().get_doi(self),
            "download": f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',

            # Archivos
            "files": files,
            "files_count": len(files),
            "total_size_in_bytes": total_size_bytes,
            "total_size_in_human_format": total_size_human,

            # Versiones
            "versions": [
                {"id": v.id, "version_number": v.version_number, "created_at": v.created_at.isoformat()}
                for v in sorted(self.versions, key=lambda v: v.created_at, reverse=True)
            ],
        }

        return data
    

class DSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return (
            f"<Download id={self.id} "
            f"dataset_id={self.dataset_id} "
            f"date={self.download_date} "
            f"cookie={self.download_cookie}>"
        )


class DSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("base_dataset.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>"


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))


# class DSMetaData(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     deposition_id = db.Column(db.Integer)
#     title = db.Column(db.String(120), nullable=False)
#     description = db.Column(db.Text, nullable=False)
#     publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
#     publication_doi = db.Column(db.String(120))
#     dataset_doi = db.Column(db.String(120))
#     tags = db.Column(db.String(120))
#     ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
#     ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
#     authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")



# class DataSet(BaseDataset):
    
#     __mapper_args__ = {"polymorphic_identity": "uvl"}

#     ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), nullable=False)
#     ds_meta_data = db.relationship("DSMetaData", backref=db.backref("data_set", uselist=False))
#     feature_models = db.relationship("FeatureModel", backref="data_set", lazy=True, cascade="all, delete")

#     def name(self):
#         return self.ds_meta_data.title

#     def files(self):
#         return [file for fm in self.feature_models for file in fm.files]

# def get_cleaned_publication_type(self):
#     return self.ds_meta_data.publication_type.name.replace("_", " ").title()

#     def get_zenodo_url(self):
#         return f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}" if self.ds_meta_data.dataset_doi else None

#     def get_files_count(self):
#         return sum(len(fm.files) for fm in self.feature_models)

#     def get_file_total_size(self):
#         return sum(file.size for fm in self.feature_models for file in fm.files)

#     def get_file_total_size_for_human(self):
#         from app.modules.dataset.services import SizeService

#         return SizeService().get_human_readable_size(self.get_file_total_size())

#     def get_doi(self):
#         from app.modules.dataset.services import DataSetService

#         return DataSetService().get_doi(self)

#     def to_dict(self):
#         return {
#             "title": self.ds_meta_data.title,
#             "id": self.id,
#             "created_at": self.created_at,
#             "created_at_timestamp": int(self.created_at.timestamp()),
#             "description": self.ds_meta_data.description,
#             "authors": [author.to_dict() for author in self.ds_meta_data.authors],
#             "publication_type": self.get_cleaned_publication_type(),
#             "publication_doi": self.ds_meta_data.publication_doi,
#             "dataset_doi": self.ds_meta_data.dataset_doi,
#             "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
#             "url": self.get_doi(),
#             "download": f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
#             "zenodo": self.get_zenodo_url(),
#             "files": [file.to_dict() for fm in self.feature_models for file in fm.files],
#             "files_count": self.get_files_count(),
#             "total_size_in_bytes": self.get_file_total_size(),
#             "total_size_in_human_format": self.get_file_total_size_for_human(),
#         }