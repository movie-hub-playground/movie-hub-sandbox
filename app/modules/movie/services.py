import os
from flask import abort
from app import db
from app.modules.movie.models import MovieDataset, Movie
import json
from types import SimpleNamespace
from app.modules.dataset.base_dataset import Version
from datetime import datetime
from core.services.BaseService import BaseService
from app.modules.movie.repositories import MovieRepository
from app.modules.dataset.repositories import DSDownloadRecordRepository, DSViewRecordRepository


class SnapshotDataset:
    """Dataset reconstruido desde snapshot sin usar SQLAlchemy."""
    def __init__(self, id, movies, metadata):
        self.id = id
        self.movies = movies
        self.ds_meta_data = metadata

class SnapshotMovie:
    """Película reconstruida desde snapshot."""
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

class MovieService(BaseService):
    def __init__(self):
        super().__init__(MovieRepository())
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
    
    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()
    
    def get_moviedataset(self, dataset_id):
        dataset = MovieDataset.query.get(dataset_id)
        if not dataset:
            abort(404, "Movie dataset not found")
        return dataset
    
    def get_all_moviedatasets(self):
        from app.modules.dataset.models import DSMetaData
        
        return MovieDataset.query.join(DSMetaData).filter(
            DSMetaData.dataset_doi.isnot(None)
        ).order_by(MovieDataset.created_at.desc()).all()
    
    #Se muestra lo publicado 
    def get_moviedataset_by_user(self, user_id):
        from app.modules.dataset.models import DSMetaData
        
        return MovieDataset.query.join(DSMetaData).filter(
            MovieDataset.user_id == user_id,
            DSMetaData.dataset_doi.isnot(None)
        ).order_by(MovieDataset.created_at.desc()).all()
    
    #Ahora mismo no se usa, sirve para mostrar los no publicados
    def get_unsynchronized_datasets_by_user(self, user_id):
        from app.modules.dataset.models import DSMetaData
        
        return MovieDataset.query.join(DSMetaData).filter(
            MovieDataset.user_id == user_id,
            DSMetaData.dataset_doi.is_(None)
        ).order_by(MovieDataset.created_at.desc()).all()
    
    def get_movie(self, movie_id):
        movie = Movie.query.get(movie_id)
        if not movie:
            abort(404, "Movie not found")
        return movie
    
    
    #POR HACER
    def create_dataset(self, form, current_user):
        """
        TODO
        añadir self.create_version(dataset) al final para poder crear las versiones
        """
        raise NotImplementedError("Dataset creation not yet implemented")
    
    def update_dataset(self, dataset, form):
        """
        TODO
        """
        raise NotImplementedError("Dataset update not yet implemented")
    
    #Método delete??

###################
# VERSIONING METHODS
###################


    def create_version(self, dataset: MovieDataset):
        """Crea una nueva versión del dataset guardando un snapshot JSON."""

        version_number = str(len(dataset.versions) + 1)

        version = Version(
            dataset_id=dataset.id,
            version_number=version_number,
            created_at=datetime.utcnow()
        )

        db.session.add(version)
        db.session.flush()

        version_folder = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/versions/{version.id}"
        os.makedirs(version_folder, exist_ok=True)

        snapshot = {
            "dataset_id": dataset.id,      
            "metadata": {
                "title": dataset.ds_meta_data.title,
                "description": dataset.ds_meta_data.description,
                "publication_type": dataset.ds_meta_data.publication_type.name if dataset.ds_meta_data.publication_type else None,
                "publication_doi": dataset.ds_meta_data.publication_doi,
                "dataset_doi": dataset.ds_meta_data.dataset_doi,
                "tags": dataset.ds_meta_data.tags.split(",") if dataset.ds_meta_data.tags else []
            },
            "movies": [m.to_dict() for m in dataset.movies]
        }

        snapshot_path = os.path.join(version_folder, "snapshot.json")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)

        version.snapshot_path = snapshot_path

        db.session.commit()
        return version


    def load_dataset_from_version(self, version_id):
        """Carga un dataset reconstruido desde el snapshot de una versión."""

        version = Version.query.get(version_id)
        if not version or not version.snapshot_path:
            raise ValueError("Snapshot not found for that version")

        with open(version.snapshot_path, "r", encoding="utf-8") as f:
            snap = json.load(f)

        metadata = SimpleNamespace(
            title=snap["metadata"].get("title"),
            description=snap["metadata"].get("description"),
            authors=snap["metadata"].get("authors", []),
            publication_type=snap["metadata"].get("publication_type"),
            publication_doi=snap["metadata"].get("publication_doi"),
            dataset_doi=snap["metadata"].get("dataset_doi"),
            tags=snap["metadata"].get("tags", [])
        )

        movies = [SnapshotMovie(m) for m in snap["movies"]]

        return SnapshotDataset(
            id=snap["dataset_id"],   # <-- ya existe
            movies=movies,
            metadata=metadata
        )
    
    def compare_versions(self, v1_dataset, v2_dataset):
        """
        Compara dos datasets cargados desde snapshot.
        Ambos argumentos son SnapshotDataset.
        """

        result = {
            "movies_added": [],
            "movies_removed": [],
            "movies_modified": [],
            "metadata_changed": {},
        }

        # ============================
        # COMPARAR METADATA
        # ============================
        meta1 = vars(v1_dataset.ds_meta_data)
        meta2 = vars(v2_dataset.ds_meta_data)

        for key in meta1.keys() | meta2.keys():
            if meta1.get(key) != meta2.get(key):
                result["metadata_changed"][key] = {
                    "old": meta1.get(key),
                    "new": meta2.get(key),
                }

        # ============================
        # COMPARAR MOVIES
        # ============================

        # Convert to dict by ID
        movies_v1 = {m.id: m for m in v1_dataset.movies}
        movies_v2 = {m.id: m for m in v2_dataset.movies}

        # Añadidos
        for movie_id, m in movies_v2.items():
            if movie_id not in movies_v1:
                result["movies_added"].append(vars(m))

        # Eliminados
        for movie_id, m in movies_v1.items():
            if movie_id not in movies_v2:
                result["movies_removed"].append(vars(m))

        # Modificados
        for movie_id in movies_v1.keys() & movies_v2.keys():
            m1 = vars(movies_v1[movie_id])
            m2 = vars(movies_v2[movie_id])

            diffs = {}
            for key in m1.keys() | m2.keys():
                if m1.get(key) != m2.get(key):
                    diffs[key] = {"old": m1.get(key), "new": m2.get(key)}

            if diffs:
                result["movies_modified"].append({
                    "movie_id": movie_id,
                    "changes": diffs
                })

        return result


    def compare_version_ids(self, version_id_1, version_id_2):
        v1 = self.load_dataset_from_version(version_id_1)
        v2 = self.load_dataset_from_version(version_id_2)

        return self.compare_versions(v1, v2)
