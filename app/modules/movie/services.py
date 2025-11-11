import os
import shutil
from flask import abort
from app import db
from app.modules.movie.models import MovieDataset, Movie


class MovieService:
    
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
        """
        raise NotImplementedError("Dataset creation not yet implemented")
    
    def update_dataset(self, dataset, form):
        """
        TODO
        """
        raise NotImplementedError("Dataset update not yet implemented")
    
    #Método delete??