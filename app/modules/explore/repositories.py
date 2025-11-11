import re

import unidecode
from sqlalchemy import any_, or_

from app.modules.dataset.models import Author, DSMetaData, PublicationType
from app.modules.movie.models import MovieDataset, Movie
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(MovieDataset)

    def filter(self, query="", sorting="newest", publication_type="any", tags=[], **kwargs):
        # Normalize and remove unwanted characters
        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)

        # Build filters for movie datasets (search in movies too)
        filters = []
        for word in cleaned_query.split():
            # Search in dataset metadata
            filters.append(DSMetaData.title.ilike(f"%{word}%"))
            filters.append(DSMetaData.description.ilike(f"%{word}%"))
            filters.append(DSMetaData.tags.ilike(f"%{word}%"))
            filters.append(Author.name.ilike(f"%{word}%"))
            filters.append(Author.affiliation.ilike(f"%{word}%"))
            filters.append(Author.orcid.ilike(f"%{word}%"))
            
            # Search in movie information
            filters.append(Movie.title.ilike(f"%{word}%"))
            filters.append(Movie.original_title.ilike(f"%{word}%"))
            filters.append(Movie.director.ilike(f"%{word}%"))
            filters.append(Movie.genre.ilike(f"%{word}%"))
            filters.append(Movie.synopsis.ilike(f"%{word}%"))
            filters.append(Movie.production_company.ilike(f"%{word}%"))

        # Query movie datasets
        datasets = (
            MovieDataset.query
            .join(MovieDataset.ds_meta_data)
            .join(DSMetaData.authors)
            .outerjoin(MovieDataset.movies)  # Left join to include datasets without movies
            .filter(or_(*filters))
            .filter(DSMetaData.dataset_doi.isnot(None))  # Only public datasets
        )

        if publication_type != "any":
            matching_type = None
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    matching_type = member
                    break

            if matching_type is not None:
                datasets = datasets.filter(DSMetaData.publication_type == matching_type.name)

        if tags:
            datasets = datasets.filter(DSMetaData.tags.ilike(any_(f"%{tag}%" for tag in tags)))

        datasets = datasets.distinct()

        # Order by created_at
        if sorting == "oldest":
            datasets = datasets.order_by(MovieDataset.created_at.asc())
        else:
            datasets = datasets.order_by(MovieDataset.created_at.desc())

        return datasets.all()