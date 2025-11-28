import os
from flask import render_template, request, jsonify
from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.models import Fakenodo
from app.modules.movie.models import BaseDataset
from app.modules.fakenodo.services import FakenodoService
from app import db
import logging

logger = logging.getLogger(__name__)

from app.modules.featuremodel.models import FeatureModel
from app.modules.movie.models import MovieDataset


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


@fakenodo_bp.route("/fakenodo/create", methods=["POST"])
def create_fakenodo():
    try:
        data = request.get_json()

        if not data or "metadata_id" not in data or "user_id" not in data:
            raise ValueError("'metadata_id' and 'user_id' fields are required.")

        # Cambiar si queremos meter más datasets a parte de movie
        movie_dataset = BaseDataset(
            user_id=data["user_id"],
            ds_meta_data_id=data["metadata_id"],
            dataset_type="movie"
        )

        db.session.add(movie_dataset)
        db.session.commit()

        service = FakenodoService()
        fakenodo_response = service.create_fakenodo(movie_dataset)

        return jsonify({
            "message": "MovieDataset successfully created in Fakenodo.",
            "dataset_id": movie_dataset.id,
            "fakenodo_id": fakenodo_response.get("id"),
            "fakenodo_response": fakenodo_response
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        db.session.rollback()
        logger.exception("Error creating MovieDataset in Fakenodo.")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@fakenodo_bp.route("/fakenodo/publish/<int:fakenodo_id>", methods=["POST"])
def publish(fakenodo_id):
    try:
        service = FakenodoService()
        fakenodo = service.publish_fakenodo(fakenodo_id)

        return jsonify({
            "message": f"Fakenodo {fakenodo_id} published successfully!",
            "id": fakenodo.id,
            "status": fakenodo.status,
            "doi": fakenodo.doi
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@fakenodo_bp.route("/fakenodo/<int:fakenodo_id>", methods=["GET"])
def getOne(fakenodo_id):
    try:
        service = FakenodoService()
        data = service.get_fakenodo(fakenodo_id)
        return jsonify(data), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Unexpected error -> " + str(e)}), 500
    
@fakenodo_bp.route("/fakenodo/<int:fakenodo_id>/versions", methods=["GET"])
def get_doi_versions(fakenodo_id):
    try:
        service = FakenodoService()
        data = service.get_doi_versions(fakenodo_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": "Unexpected error -> " + str(e)}), 500


@fakenodo_bp.route("/fakenodo/upload/<int:fakenodo_id>", methods=["POST"])
def upload_dataset(fakenodo_id: int):
    try:

        if "file" not in request.files:
            return jsonify({"ok": False, "error": "file is required"}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"ok": False, "error": "empty filename"}), 400

        dataset_id = int(request.form.get("dataset_id", 0))
        feature_model_id = int(request.form.get("feature_model_id", 0))
        uvl_filename = request.form.get("uvl_filename") or file.filename

        d = MovieDataset()
        d.id = dataset_id
        d.file = file.read()

        fm = FeatureModel.query.get(feature_model_id)
        if not fm:
            return jsonify({
                    "ok": False,
                    "error": "Feature model not found"
            }), 404

        if not getattr(fm, "fm_meta_data", None):
            class Meta:
                pass
            fm.fm_meta_data = Meta()

        fm.fm_meta_data.uvl_filename = uvl_filename

        os.makedirs("datasets", exist_ok=True)

        svc = FakenodoService()
        fakenodo = svc.upload_dataset(fakenodo_id, d, fm)

        db.session.commit()

        return jsonify(
            {
                "ok": True,
                "id": fakenodo.id,
                "status": fakenodo.status,
                "dataset_file_path": fakenodo.dataset_file_path,
            }
        ), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        msg = f"Unexpected error: {str(e)}"
        return jsonify({"ok": False, "error": msg}), 500

