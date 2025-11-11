# app/modules/dataset/seeders.py

import os
import shutil
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.dataset.base_dataset import Version
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):

    priority = 2

    def run(self):
        # 🔹 Recuperar usuarios existentes
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()
        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # 🔹 Crear métricas
        ds_metrics = DSMetrics(number_of_models="5", number_of_features="50")
        db.session.add(ds_metrics)
        db.session.flush()

        # 🔹 Crear metadatos de datasets
        ds_meta_data_list = []
        for i in range(4):
            ds_meta = DSMetaData(
                deposition_id=i + 1,
                title=f"Sample dataset {i + 1}",
                description=f"Description for dataset {i + 1}",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                publication_doi=f"10.1234/dataset{i + 1}",
                dataset_doi=f"10.1234/dataset{i + 1}",
                tags="tag1, tag2",
                ds_metrics_id=ds_metrics.id,
            )
            ds_meta_data_list.append(ds_meta)
        db.session.add_all(ds_meta_data_list)
        db.session.flush()

        # 🔹 Crear autores
        authors = []
        for i, ds_meta in enumerate(ds_meta_data_list):
            author = Author(
                name=f"Author {i + 1}",
                affiliation=f"Affiliation {i + 1}",
                orcid=f"0000-0000-0000-000{i}",
                ds_meta_data_id=ds_meta.id,
            )
            authors.append(author)
        db.session.add_all(authors)
        db.session.flush()

        # 🔹 Crear datasets
        datasets = []
        for i, ds_meta in enumerate(ds_meta_data_list):
            dataset = DataSet(
                user_id=user1.id if i % 2 == 0 else user2.id,
                ds_meta_data_id=ds_meta.id,
                created_at=datetime.now(timezone.utc) - timedelta(days=10 - i),
                dataset_type="uvl",
            )
            datasets.append(dataset)
        db.session.add_all(datasets)
        db.session.flush()

        # 🔹 Crear múltiples versiones por dataset
        all_versions = []
        for dataset in datasets:
            version_list = []
            version_dates = [
                datetime.now(timezone.utc) - timedelta(days=5),
                datetime.now(timezone.utc) - timedelta(days=2),
                datetime.now(timezone.utc),
            ]
            version_numbers = ["1.0", "1.1", "2.0"]

            for vn, vd in zip(version_numbers, version_dates):
                v = Version(
                    dataset_id=dataset.id,
                    version_number=vn,
                    created_at=vd
                )
                version_list.append(v)

            all_versions.extend(version_list)

            # Guardar la última versión como la actual
            dataset.current_version = version_numbers[-1]

        db.session.add_all(all_versions)
        db.session.flush()

        # 🔹 Crear metadatos de FeatureModels
        fm_meta_data_list = []
        for i in range(12):
            fm_meta = FMMetaData(
                filename=f"file{i + 1}.uvl",
                title=f"Feature Model {i + 1}",
                description=f"Description for feature model {i + 1}",
                publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                publication_doi=f"10.1234/fm{i + 1}",
                tags="tag1, tag2",
                version="1.0",
            )
            fm_meta_data_list.append(fm_meta)
        db.session.add_all(fm_meta_data_list)
        db.session.flush()

        # 🔹 Crear autores de FeatureModels
        fm_authors = []
        for i, fm_meta in enumerate(fm_meta_data_list):
            fm_author = Author(
                name=f"Author {i + 5}",
                affiliation=f"Affiliation {i + 5}",
                orcid=f"0000-0000-0000-000{i + 5}",
                fm_meta_data_id=fm_meta.id,
            )
            fm_authors.append(fm_author)
        db.session.add_all(fm_authors)
        db.session.flush()

        # 🔹 Crear FeatureModels (3 por dataset)
        feature_models = []
        for i in range(12):
            fm = FeatureModel(
                data_set_id=datasets[i // 3].id,
                fm_meta_data_id=fm_meta_data_list[i].id
            )
            feature_models.append(fm)
        db.session.add_all(feature_models)
        db.session.flush()

        # 🔹 Crear archivos físicos y registros Hubfile
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "uvl_examples")
        
        hubfiles = []
        for i, feature_model in enumerate(feature_models):
            file_name = f"file{i + 1}.uvl"
            dataset = datasets[i // 3]
            user_id = dataset.user_id
            dest_folder = os.path.join(working_dir, "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)

            src_file = os.path.join(src_folder, file_name)
            dest_file = os.path.join(dest_folder, file_name)
            shutil.copy(src_file, dest_file)

            hubfile = Hubfile(
                name=file_name,
                checksum=f"checksum{i + 1}",
                size=os.path.getsize(dest_file),
                feature_model_id=feature_model.id,
            )
            hubfiles.append(hubfile)
        
        db.session.add_all(hubfiles)
        db.session.flush()

        # 🔹 Actualizar info de archivos
        for dataset in datasets:
            dataset.update_files_info()
        
        # 🔹 Commit final
        db.session.commit()

        print("✅ DataSetSeeder completado: datasets, versiones y archivos creados.")