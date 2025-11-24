import io
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from flask import url_for

# ---------- GET /moviedataset ----------
def test_index_redirects_to_list(test_client):
    response = test_client.get("/moviedataset")
    assert response.status_code == 302
    assert "/moviedataset/list" in response.location


# ---------- GET /moviedataset/list ----------
@patch("app.modules.movie.routes.movie_service.get_all_moviedatasets")
def test_list_datasets(mock_get_all, test_client):
    # Crear mock de dataset con estructura completa
    mock_dataset = MagicMock()
    mock_dataset.id = 1
    mock_dataset.ds_meta_data.title = "Test Dataset"
    mock_dataset.ds_meta_data.description = "Test Description"
    
    mock_get_all.return_value = [mock_dataset]
    
    response = test_client.get("/moviedataset/list")
    assert response.status_code == 200
    mock_get_all.assert_called_once()
    assert b"Test Dataset" in response.data


# ---------- GET /moviedataset/my-datasets ----------
@patch("app.modules.movie.routes.movie_service.get_moviedataset_by_user")
def test_my_datasets_requires_login(mock_get_by_user, test_client):
    # Crear mock de dataset
    mock_dataset = MagicMock()
    mock_dataset.id = 1
    mock_dataset.ds_meta_data.title = "User Dataset"
    mock_dataset.ds_meta_data.description = "User Description"
    
    mock_get_by_user.return_value = [mock_dataset]
    
    # Simular usuario autenticado usando Flask-Login
    with patch("flask_login.utils._get_user") as mock_current_user:
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.is_active = True
        mock_user.is_anonymous = False
        mock_user.id = 1
        mock_current_user.return_value = mock_user
        
        response = test_client.get("/moviedataset/my-datasets")
        
    assert response.status_code == 200
    assert b"User Dataset" in response.data
    mock_get_by_user.assert_called_once_with(1)


# ---------- GET /moviedataset/<id> ----------
from unittest.mock import patch, MagicMock

@patch("app.modules.movie.routes.ds_view_record_service.create_cookie")
@patch("app.modules.movie.routes.movie_service.get_moviedataset")
def test_view_dataset(mock_get_dataset, mock_create_cookie, test_client):
    # Mock del dataset
    mock_dataset = MagicMock()
    mock_dataset.id = 123
    mock_dataset.ds_meta_data.title = "Mock Dataset"
    mock_dataset.ds_meta_data.description = "Mock Description"
    mock_dataset.ds_meta_data.tags = "test, mock"
    mock_dataset.movies = []

    mock_get_dataset.return_value = mock_dataset

    # Mock de create_cookie para que no intente modificar BD
    mock_create_cookie.return_value = "fake-cookie-value"

    response = test_client.get("/moviedataset/123")

    # --- Asserts ---
    assert response.status_code == 200
    assert b"Mock Dataset" in response.data

    mock_get_dataset.assert_called_once_with(123)
    mock_create_cookie.assert_called_once_with(dataset=mock_dataset)

    # También podemos validar que la cookie se setea:
    assert response.headers.get("Set-Cookie") is not None
    assert "view_cookie=fake-cookie-value" in response.headers.get("Set-Cookie")



# ---------- GET /movie/<id> ----------
@patch("app.modules.movie.routes.movie_service.get_movie")
def test_view_movie(mock_get_movie, test_client):
    # Crear mock completo de la película
    mock_movie = MagicMock()
    mock_movie.id = 42
    mock_movie.title = "Mock Movie"
    mock_movie.year = 2024
    mock_movie.director = "Test Director"
    
    # Mock del dataset relacionado
    mock_dataset = MagicMock()
    mock_dataset.id = 1
    mock_dataset.ds_meta_data.title = "Dataset 1"
    
    mock_movie.dataset = mock_dataset
    mock_get_movie.return_value = mock_movie

    response = test_client.get("/movie/42")
    assert response.status_code == 200
    assert b"Mock Movie" in response.data
    mock_get_movie.assert_called_once_with(42)


# ---------- GET /moviedataset/<id>/download ----------
@patch("app.modules.movie.routes.movie_service.get_moviedataset")
@patch("app.modules.movie.routes.DSDownloadRecordService")
@patch("app.modules.movie.routes.DSDownloadRecord")
def test_download_dataset_creates_zip(mock_record_model, mock_record_service, mock_get_dataset, test_client, tmp_path):
    # --- Mock dataset ---
    dataset_mock = MagicMock()
    dataset_mock.id = 5
    dataset_mock.user_id = 99
    mock_get_dataset.return_value = dataset_mock

    # --- Crear carpeta y archivo en tmp_path ---
    folder = tmp_path / "uploads" / "user_99" / "dataset_5"
    folder.mkdir(parents=True)
    (folder / "test.txt").write_text("contenido")

    # --- Mock de query para que no toque base de datos ---
    mock_record_model.query.filter_by.return_value.first.return_value = None

    # --- Mock os.path.exists + os.walk ---
    with patch("app.modules.movie.routes.os.path.exists", return_value=True), \
         patch("app.modules.movie.routes.os.walk") as mockwalk:
        
        mockwalk.return_value = [(str(folder), [], ["test.txt"])]

        response: Response = test_client.get("/moviedataset/5/download")

    # ---- Assertions ----
    assert response.status_code == 200
    assert response.mimetype == "application/zip"

    # Se llamó al servicio para obtener el dataset
    mock_get_dataset.assert_called_once_with(5)

    # Se debería haber intentado crear un record porque no existía antes
    mock_record_service.return_value.create.assert_called_once()

    # Aseguramos que el zip se haya enviado
    content_disp = response.headers.get("Content-Disposition")
    assert "attachment" in content_disp
    assert "movie_dataset_5.zip" in content_disp



def test_download_dataset_not_found(test_client):
    with patch("app.modules.movie.routes.movie_service.get_moviedataset") as mock_get, \
         patch("app.modules.movie.routes.os.path.exists", return_value=False):
        mock_get.return_value = MagicMock(id=1, user_id=1)
        response = test_client.get("/moviedataset/1/download")
        assert response.status_code == 404

# ---------- GET /moviedataset/<id>/versions ----------
@patch("app.modules.movie.routes.movie_service.get_moviedataset")
def test_compare_versions_page_renders(mock_get_dataset, test_client):
    from datetime import datetime, timedelta

    mock_dataset = MagicMock()
    mock_dataset.id = 10
    mock_dataset.ds_meta_data.title = "Dataset test"

    mock_dataset.versions = [
        MagicMock(id=1, version_number="1", created_at=datetime.utcnow()),
        MagicMock(id=2, version_number="2", created_at=datetime.utcnow() - timedelta(minutes=1)),
    ]

    mock_get_dataset.return_value = mock_dataset

    response = test_client.get("/moviedataset/10/versions")
    assert response.status_code == 200
    assert b"Select two versions to compare" in response.data

# ---------- compare_version_ids ----------
@patch("app.modules.movie.services.MovieService.load_dataset_from_version")
def test_compare_version_ids_detects_changes(mock_load):
    from app.modules.movie.services import MovieService

    class FakeMeta:
        def __init__(self, title):
            self.title = title

    class FakeMovie:
        def __init__(self, id, title):
            self.id = id
            self.title = title

    mock_v1 = MagicMock()
    mock_v1.ds_meta_data = FakeMeta("Title A")
    mock_v1.movies = [FakeMovie(1, "Movie A")]

    mock_v2 = MagicMock()
    mock_v2.ds_meta_data = FakeMeta("Title B")
    mock_v2.movies = [
        FakeMovie(1, "Movie A"),
        FakeMovie(2, "Movie Added")
    ]

    mock_load.side_effect = [mock_v1, mock_v2]

    svc = MovieService()
    diff = svc.compare_version_ids(1, 2)

    # Assert cambios detectados
    assert "title" in diff["metadata_changed"]

    # movies_added devuelve DICTS, no objetos
    assert diff["movies_added"][0]["title"] == "Movie Added"
