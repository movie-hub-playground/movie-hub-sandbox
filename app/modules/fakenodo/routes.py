from flask import render_template, request, jsonify
from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.models import Fakenodo
from app.modules.movie.models import BaseDataset
from app.modules.fakenodo.services import FakenodoService
from app import db
import logging

logger = logging.getLogger(__name__)


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
