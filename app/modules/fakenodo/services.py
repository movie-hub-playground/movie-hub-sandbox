import hashlib
import os

from app.modules.fakenodo.repositories import FakenodoRepository
from core.services.BaseService import BaseService
from app.modules.movie.models import MovieDataset
from app.modules.featuremodel.models import FeatureModel
from app.modules.fakenodo.models import Fakenodo
import uuid


class FakenodoService(BaseService):
    def __init__(self):
        super().__init__(FakenodoRepository())

    def create_fakenodo(self, dataset=MovieDataset):
        #TO-DO: funcion que cree un nuevo dataset
        pass

    def upload_dataset(self,
                       fakenodo_id,
                       dataset=MovieDataset,
                       feature_model=FeatureModel):
        # 1. Verificar si el Fakenodo existe
        fakenodo = self.get_by_id(fakenodo_id)
        if not fakenodo:
            raise ValueError(f"Fakenodo with ID {fakenodo_id} not found")

        # 2. Verificar que el dataset sea válido
        if not isinstance(dataset, MovieDataset):
            raise ValueError("Invalid dataset provided")

        # 3. Validar el FeatureModel
        if not isinstance(feature_model, FeatureModel):
            raise ValueError("Invalid FeatureModel provided")

        if not feature_model.fm_meta_data or not hasattr(
            feature_model.fm_meta_data, 'uvl_filename'
        ):
            raise ValueError(
                "FeatureModel must have 'fm_meta_data' and"
                "'uvl_filename' attribute"
                )

        # 4. Generar la ruta del archivo para guardarlo
        file_name = feature_model.fm_meta_data.uvl_filename
        file_path = os.path.join(
            'datasets', f"{fakenodo_id}_{dataset.id}_{file_name}"
        )

        # 5. Verificar si el archivo del dataset está presente
        if not hasattr(dataset, 'file') or dataset.file is None:
            raise ValueError("Dataset file is missing or invalid.")

        # 6. Subir el archivo del dataset
        try:
            with open(file_path, "wb") as file:
                file.write(dataset.file)  # Guardamos el contenido del archivo
        except Exception as e:
            raise Exception(f"Error uploading file: {str(e)}")

        # 7. Asignar el archivo y el modelo de características al Fakenodo
        fakenodo.dataset_file_path = file_path
        fakenodo.feature_model = feature_model

        # 8. Actualizar el estado del Fakenodo
        fakenodo.status = "dataset_uploaded"

        # 9. Actualizar el Fakenodo en la base de datos
        self.update(
            fakenodo.id,
            dataset_file_path=fakenodo.dataset_file_path,
            feature_model=fakenodo.feature_model,
            status=fakenodo.status
        )

        return fakenodo

    def publish_fakenodo(self, fakenodo_id):
        fakenodo = self.get_by_id(fakenodo_id)
        if not fakenodo:
            raise ValueError(f"Fakenodo with ID {fakenodo_id} not found")

        if fakenodo.status == "published":
            raise ValueError(f"Fakenodo {fakenodo_id} is already published")

        fake_doi = f"10.1234/moviehub.fake.{uuid.uuid4().hex[:8]}"

        fakenodo.status = "published"
        fakenodo.doi = fake_doi

        self.update(fakenodo.id, status=fakenodo.status, doi=fakenodo.doi)

        return fakenodo

    def get_fakenodo(self, fakenodo_id):
        dataset = Fakenodo.query.get(fakenodo_id)
        if not dataset:
            raise Exception("Dataset not found")
        response = {
            "movie_metadata": dataset.movie_metadata,
            "status": dataset.status,
            "doi": dataset.doi
        }
        return response

    def get_doi_versions(self, fakenodo_id):
        #TO-DO: funcion para listar las versiones de un dataset
        pass

    def checksum(fileName):
        try:
            with open(fileName, "rb") as file:
                file_content = file.read()
                res = hashlib.sha256(file_content).hexdigest()
            return res
        except FileNotFoundError:
            raise Exception(f"File {fileName} not found for checksum calculation")
        except Exception as e:
            raise Exception(f"Error calculating checksum for file {fileName}: {str(e)}")
