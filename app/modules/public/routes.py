import logging

from flask import render_template

from app.modules.movie.services import MovieService
from app.modules.dataset.services import DSDownloadRecordService
from app.modules.featuremodel.services import FeatureModelService
from app.modules.movie.models import MovieDataset
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    movieDS_service = MovieService()
    feature_model_service = FeatureModelService()
    download_service = DSDownloadRecordService()

    # Statistics: total datasets and feature models
    feature_models_counter = feature_model_service.count_feature_models()

    # Statistics: total downloads
    total_dataset_downloads = movieDS_service.total_dataset_downloads()
    total_feature_model_downloads = feature_model_service.total_feature_model_downloads()

    # Statistics: total views
    total_dataset_views = movieDS_service.total_dataset_views()
    total_feature_model_views = feature_model_service.total_feature_model_views()
    
    # Añadir trending datasets
    trending_datasets_data = download_service.top_downloaded_datasets_last_month(limit=3)
    
    trending_datasets = []
    for item in trending_datasets_data:
        ds_id = item.get('dataset_id')

        dataset = MovieDataset.query.get(ds_id)

        if dataset:
            trending_datasets.append({
                'dataset': dataset,
                'download_count': item.get('download_count') if isinstance(item, dict) else (item[1] if len(item) > 1 else 0),
                'author': dataset.ds_meta_data.authors[0].name if dataset.ds_meta_data and dataset.ds_meta_data.authors else "",
            })
            

    return render_template(
        "public/index.html",
        datasets=movieDS_service.get_all_moviedatasets(),
        datasets_counter=len(movieDS_service.get_all_moviedatasets()),
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
        trending_datasets=trending_datasets,
    )
