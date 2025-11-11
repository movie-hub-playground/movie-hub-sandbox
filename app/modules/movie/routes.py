import os
import shutil
import tempfile
from zipfile import ZipFile

from flask import (
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.movie import movie_bp
from app.modules.movie.forms import MovieForm
from app.modules.movie.services import MovieService

movie_service = MovieService()

#GET MOVIES
@movie_bp.route('/moviedataset', methods=['GET'])
def index():
    """Redirect to list all movie datasets"""
    return redirect(url_for('movie.list_datasets'))

@movie_bp.route("/moviedataset/list", methods=["GET"])
def list_datasets():
    datasets = movie_service.get_all_moviedatasets()
    
    return render_template(
        "movie/list_datasets.html",
        datasets=datasets
    )

#GET MY DATASETS
@movie_bp.route("/moviedataset/my-datasets", methods=["GET"])
@login_required
def my_datasets():
    #Obtengo los datasets de usuario act
    synchronized_datasets = movie_service.get_moviedataset_by_user(current_user.id)
    return render_template(
        "movie/my_datasets.html",
        synchronized_datasets=synchronized_datasets,
    )


@movie_bp.route("/moviedataset/<int:dataset_id>", methods=["GET"])
def view_dataset(dataset_id):
    """View a movie dataset with all its movies (public view)"""
    dataset = movie_service.get_moviedataset(dataset_id)
    return render_template(
        "movie/view_dataset.html",
        dataset=dataset
    )

# Manage
@movie_bp.route("/moviedataset/<int:dataset_id>/manage", methods=["GET"])
@login_required
def manage_dataset(dataset_id):
    dataset = movie_service.get_moviedataset(dataset_id)
    
    if dataset.user_id != current_user.id:
        abort(403, "You don't have permission to manage this dataset")
    
    return render_template(
        "movie/manage_dataset.html",
        dataset=dataset
    )

# Para ver los detalles de la película
@movie_bp.route("/movie/<int:movie_id>", methods=["GET"])
def view_movie(movie_id):
    movie = movie_service.get_movie(movie_id)
    dataset = movie.dataset
    
    return render_template(
        "movie/view_movie.html",
        movie=movie,
        dataset=dataset
    )

#Para la descarga 
@movie_bp.route("/moviedataset/<int:dataset_id>/download", methods=["GET"])
def download_dataset(dataset_id):
    dataset = movie_service.get_moviedataset(dataset_id)
    
    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
    
    if not os.path.exists(file_path):
        abort(404, "Dataset files not found")
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"movie_dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)
                relative_path = os.path.relpath(full_path, file_path)
                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    resp = send_from_directory(
        temp_dir,
        f"movie_dataset_{dataset_id}.zip",
        as_attachment=True,
        mimetype="application/zip",
    )

    return resp

# POR IMPLEMENTAR: PENDIENTE DE CAMBIOS (IGNORAR DE MOMENTO EN TEST)

@movie_bp.route("/moviedataset/upload", methods=["GET", "POST"])
@login_required
def upload_dataset():
    """
    TODO:
    """
    form = MovieForm()
    
    if request.method == "POST":
        return jsonify({"error": "Upload functionality not yet implemented"}), 501
    
    return render_template("movie/upload_dataset.html", form=form)


@movie_bp.route("/moviedataset/file/upload", methods=["POST"])
@login_required
def upload_file():
    """
    Upload a single file (Dropzone integration)
    TODO: Implementation pending
    """
    file = request.files.get("file")
    
    if not file:
        return jsonify({"message": "No file provided"}), 400
    
    return jsonify({
        "message": "File upload temporarily disabled",
        "filename": file.filename,
    }), 501


@movie_bp.route("/moviedataset/file/delete", methods=["POST"])
@login_required
def delete_file():
    """
    TODO
    """
    return jsonify({"message": "File deletion temporarily disabled"}), 501