import hashlib

from app.modules.fakenodo.repositories import FakenodoRepository
from core.services.BaseService import BaseService
from app.modules.movie.models import MovieDataset, BaseDataset
from app.modules.featuremodel.models import FeatureModel
from app.modules.fakenodo.models import Fakenodo
import uuid
import logging

logger = logging.getLogger(__name__)

class FakenodoService(BaseService):
    def __init__(self):
        super().__init__(FakenodoRepository())
    
    def create_fakenodo(self, dataset=BaseDataset):
        try:
            logger.info(f"Creating Fakenodo for dataset ID {dataset.id}...")

            fakenodo = self.repository.create_new_fakenodo(dataset_id=dataset.id)

            fakenodo_response = {
                "dataset_metadata": dataset.ds_meta_data.to_dict(),
                "status": fakenodo.status
            }

            return fakenodo_response

        except Exception as error:
            logger.exception("Error creating Fakenodo record.")
            raise Exception(f"Failed to create Fakenodo record: {str(error)}")

        
    def upload_dataset(self, fakenodo_id, dataset=MovieDataset, feature_model=FeatureModel):
        #TO-DO: funcion suba un fichero al reposiotrio de datasets
        pass
    
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
        fakenodo = Fakenodo.query.get(fakenodo_id)
        if not fakenodo:
            raise FileNotFoundError("Fakenodo object not found")
        response = {
            "dataset_metadata": fakenodo.dataset.ds_meta_data.to_dict(),
            "status": fakenodo.status,
        }
        return response
        
    
    def get_doi_versions(self, fakenodo_id):
        fakenodo = Fakenodo.query.get(fakenodo_id)
        if not fakenodo:
            raise FileNotFoundError("Fakenodo object not found")
        response = {
            "version-list": fakenodo.dataset.versions.__repr__(),
            "current-version": fakenodo.dataset.current_version,
            "doi": fakenodo.dataset.ds_meta_data.dataset_doi,
        }
        return response
    
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
