import os
from flask import render_template, request, jsonify
from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.models import Fakenodo
from app.modules.fakenodo.services import FakenodoService
from app import db
import uuid

from app.modules.featuremodel.models import FeatureModel
from app.modules.movie.models import MovieDataset


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


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
    except Exception as e:
        return jsonify({"error": str(e)}), 404


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
