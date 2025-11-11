import os
import json
import shutil
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv

from app import db
from app.modules.auth.models import User
from app.modules.movie.models import MovieDataset, Movie
from app.modules.dataset.models import DSMetaData, PublicationType, Author
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class MovieSeeder(BaseSeeder):
    priority = 3

    def run(self):
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "movie", "json_examples")

        # Dataset 1
        scifi_meta = DSMetaData(
            title="Sci-Fi Masterpieces Collection",
            description="Essential science fiction films that pushed the boundaries of cinema",
            publication_type=PublicationType.OTHER,
            tags="movies, sci-fi, classics, space",
            dataset_doi="10.1234/scify-2024"
        )
        db.session.add(scifi_meta)
        db.session.flush()

        scifi_author = Author(
            name="Sci-Fi Film Institute",
            affiliation="Future Cinema Foundation",
            ds_meta_data_id=scifi_meta.id
        )
        db.session.add(scifi_author)
        db.session.flush()

        scifi_dataset = MovieDataset(
            ds_meta_data_id=scifi_meta.id,
            user_id=user1.id,
            dataset_type="movie",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(scifi_dataset)
        db.session.flush()

        with open(os.path.join(src_folder, "movies1.json"), 'r', encoding='utf-8') as f:
            scifi_movies_data = json.load(f)

        scifi_movies = [Movie(movie_dataset_id=scifi_dataset.id, **data) for data in scifi_movies_data]
        db.session.add_all(scifi_movies)
        db.session.flush()

        # Dataset 2
        tarantino_meta = DSMetaData(
            title="Quentin Tarantino Collection",
            description="Essential films from the master of postmodern cinema",
            publication_type=PublicationType.OTHER,
            tags="movies, tarantino, crime, action",
            dataset_doi="10.1234/tarantino-movies-2024"
        )
        db.session.add(tarantino_meta)
        db.session.flush()

        tarantino_author = Author(
            name="Tarantino Film Archive",
            affiliation="Independent Cinema Society",
            ds_meta_data_id=tarantino_meta.id
        )
        db.session.add(tarantino_author)
        db.session.flush()

        tarantino_dataset = MovieDataset(
            ds_meta_data_id=tarantino_meta.id,
            user_id=user2.id,
            dataset_type="movie",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(tarantino_dataset)
        db.session.flush()

        with open(os.path.join(src_folder, "movies2.json"), 'r', encoding='utf-8') as f:
            tarantino_movies_data = json.load(f)

        tarantino_movies = [Movie(movie_dataset_id=tarantino_dataset.id, **data) for data in tarantino_movies_data]
        db.session.add_all(tarantino_movies)
        db.session.flush()

        # Crear FeatureModels y copiar archivos
        datasets_info = [
            (scifi_dataset, "movies1.json"),
            (tarantino_dataset, "movies2.json")
        ]
        
        hubfiles = []
        
        for dataset, json_filename in datasets_info:
            dest_folder = os.path.join(working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}")
            os.makedirs(dest_folder, exist_ok=True)
            
            src_file = os.path.join(src_folder, json_filename)
            dest_file = os.path.join(dest_folder, json_filename)
            shutil.copy(src_file, dest_file)
            
            with open(dest_file, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            fm_meta = FMMetaData(
                filename=json_filename,
                title=f"{dataset.ds_meta_data.title} - Data File",
                description=f"Complete movie collection data in JSON format",
                publication_type=PublicationType.OTHER,
                tags="movie, json, collection",
                version="1.0"
            )
            db.session.add(fm_meta)
            db.session.flush()
            
            fm_author = Author(
                name=dataset.ds_meta_data.authors[0].name,
                affiliation=dataset.ds_meta_data.authors[0].affiliation,
                fm_meta_data_id=fm_meta.id
            )
            db.session.add(fm_author)
            db.session.flush()
            
            feature_model = FeatureModel(
                data_set_id=dataset.id,
                fm_meta_data_id=fm_meta.id
            )
            db.session.add(feature_model)
            db.session.flush()
            
            hubfile = Hubfile(
                name=json_filename,
                checksum=file_hash,
                size=os.path.getsize(dest_file),
                feature_model_id=feature_model.id
            )
            hubfiles.append(hubfile)
        
        db.session.add_all(hubfiles)
        db.session.flush()
        
        scifi_dataset.update_files_info()
        tarantino_dataset.update_files_info()

        db.session.commit()