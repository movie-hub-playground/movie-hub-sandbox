from app import db
from app.modules.dataset.base_dataset import BaseDataset


class Movie(db.Model):
    """Modelo para películas individuales"""
    __tablename__ = "movie"
    
    id = db.Column(db.Integer, primary_key=True)
    movie_dataset_id = db.Column(db.Integer, db.ForeignKey('movie_dataset.id'), nullable=False)
    
    # Información básica
    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255))
    year = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer)
    country = db.Column(db.String(255))
    
    # Equipo creativo
    director = db.Column(db.String(500))
    production_company = db.Column(db.String(500))
    
    # Clasificación
    genre = db.Column(db.String(255))
    synopsis = db.Column(db.Text)
    
    # IMDB
    imdb_rating = db.Column(db.Float)
    imdb_votes = db.Column(db.Integer)
    
    poster_url = db.Column(db.String(500))
    poster_local_path = db.Column(db.String(500))
    
    screenplay = db.Column(db.JSON) 
    cast = db.Column(db.JSON)
    awards = db.Column(db.JSON)
    
    def to_dict(self):
        """Convierte la película a diccionario"""
        return {
            "id": self.id,
            "title": self.title,
            "original_title": self.original_title,
            "year": self.year,
            "duration": self.duration,
            "country": self.country,
            "director": self.director,
            "production_company": self.production_company,
            "genre": self.genre,
            "synopsis": self.synopsis,
            "imdb_rating": self.imdb_rating,
            "imdb_votes": self.imdb_votes,
            "poster_url": self.poster_url,
            "screenplay": self.screenplay,
            "cast": self.cast,
            "awards": self.awards,
        }
    
    def __repr__(self):
        return f"<Movie {self.id}: {self.title} ({self.year})>"


class MovieDataset(BaseDataset):
    """Dataset que contiene múltiples películas"""
    __tablename__ = "movie_dataset"
    
    id = db.Column(db.Integer, db.ForeignKey('base_dataset.id'), primary_key=True)
    
    movies = db.relationship(
        "Movie", 
        backref="dataset", 
        lazy=True, 
        cascade="all, delete-orphan"
    )
    
    __mapper_args__ = {
        "polymorphic_identity": "movie",
    }
    
    def get_movies_count(self):
        """Retorna el número de películas en el dataset"""
        return len(self.movies)
    
    @property
    def user(self):
        from app.modules.auth.models import User
        return User.query.get(self.user_id)
    
    def to_dict(self):
        """Convierte el dataset a diccionario para JSON/APIs"""
        return {
            "id": self.id,
            "dataset_type": self.dataset_type,
            "title": self.ds_meta_data.title if self.ds_meta_data else None,
            "description": self.ds_meta_data.description if self.ds_meta_data else None,
            "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data and self.ds_meta_data.tags else [],
            "authors": [a.to_dict() for a in self.ds_meta_data.authors] if self.ds_meta_data and self.ds_meta_data.authors else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "movies_count": self.get_movies_count(),
            "movies": [movie.to_dict() for movie in self.movies],
        }
    
    def __repr__(self):
        return f"<MovieDataset {self.id}: {self.get_movies_count()} movies>"