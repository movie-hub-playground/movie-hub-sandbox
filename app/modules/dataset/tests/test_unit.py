from unittest.mock import patch, MagicMock

from app.modules.dataset.services import DSDownloadRecordService
from app.modules.dataset.repositories import DSDownloadRecordRepository


# ========== Tests para DSDownloadRecordRepository.top_downloaded_datasets_last_month ==========

class TestDSDownloadRecordRepositoryTopDownloaded:
    """Tests para el método top_downloaded_datasets_last_month del repositorio"""
    
    @patch('app.modules.dataset.repositories.DSDownloadRecordRepository.top_downloaded_datasets_last_month')
    def test_top_downloaded_datasets_returns_list(self, mock_method):
        """Verifica que el método retorna una lista"""
        mock_method.return_value = [(1, 5), (2, 3)]
        repository = DSDownloadRecordRepository()
        
        result = repository.top_downloaded_datasets_last_month(limit=2)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    @patch('app.modules.dataset.repositories.DSDownloadRecordRepository.top_downloaded_datasets_last_month')
    def test_top_downloaded_datasets_returns_tuples_with_dataset_id_and_count(self, mock_method):
        """Verifica que cada elemento es una tupla (dataset_id, count)"""
        mock_method.return_value = [(1, 10), (2, 8), (3, 5)]
        repository = DSDownloadRecordRepository()
        
        result = repository.top_downloaded_datasets_last_month(limit=3)
        
        assert len(result) == 3
        assert result[0] == (1, 10)
        assert result[1] == (2, 8)
        assert result[2] == (3, 5)
    
    @patch('app.modules.dataset.repositories.DSDownloadRecordRepository.top_downloaded_datasets_last_month')
    def test_top_downloaded_datasets_respects_limit_parameter(self, mock_method):
        """Verifica que el parámetro limit se respeta"""
        mock_method.return_value = [(1, 5), (2, 3)]
        repository = DSDownloadRecordRepository()
        
        result = repository.top_downloaded_datasets_last_month(limit=5)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    @patch('app.modules.dataset.repositories.DSDownloadRecordRepository.top_downloaded_datasets_last_month')
    def test_top_downloaded_datasets_filters_by_last_month(self, mock_method):
        """Verifica que solo obtiene descargas del último mes"""
        mock_method.return_value = []
        repository = DSDownloadRecordRepository()
        
        result = repository.top_downloaded_datasets_last_month(limit=3)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('app.modules.dataset.repositories.DSDownloadRecordRepository.top_downloaded_datasets_last_month')
    def test_top_downloaded_datasets_empty_results(self, mock_method):
        """Verifica que maneja correctamente cuando no hay descargas"""
        mock_method.return_value = []
        repository = DSDownloadRecordRepository()
        
        result = repository.top_downloaded_datasets_last_month(limit=3)
        
        assert result == []
        assert isinstance(result, list)


# ========== Tests para DSDownloadRecordService.top_downloaded_datasets_last_month ==========

class TestDSDownloadRecordServiceTopDownloaded:
    """Tests para el método top_downloaded_datasets_last_month del servicio"""
    
    def test_service_returns_list_of_dicts(self):
        """Verifica que el servicio retorna una lista de diccionarios"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5), (2, 3)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=2)
                
                assert isinstance(result, list)
                assert len(result) == 2
                assert all(isinstance(item, dict) for item in result)
    
    def test_service_returns_dict_with_required_keys(self):
        """Verifica que cada diccionario contiene las claves requeridas"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert 'dataset' in result[0]
                assert 'download_count' in result[0]
                assert 'author' in result[0]
    
    def test_service_includes_download_count_correctly(self):
        """Verifica que el conteo de descargas se incluye correctamente"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 10), (2, 5), (3, 3)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=3)
                
                assert result[0]['download_count'] == 10
                assert result[1]['download_count'] == 5
                assert result[2]['download_count'] == 3
    
    def test_service_extracts_author_from_dataset(self):
        """Verifica que extrae el nombre del primer autor del dataset"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                # Mock del dataset con metadata y autores
                mock_dataset = MagicMock()
                mock_author = MagicMock()
                mock_author.name = "John Doe"
                mock_dataset.ds_meta_data.authors = [mock_author]
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert result[0]['author'] == "John Doe"
    
    def test_service_handles_dataset_without_metadata(self):
        """Verifica que maneja datasets sin metadata"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert result[0]['author'] == ""
    
    def test_service_handles_dataset_without_authors(self):
        """Verifica que maneja datasets con metadata pero sin autores"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data.authors = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert result[0]['author'] == ""
    
    def test_service_handles_empty_authors_list(self):
        """Verifica que maneja listas de autores vacías"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data.authors = []
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert result[0]['author'] == ""
    
    def test_service_includes_dataset_object(self):
        """Verifica que incluye el objeto del dataset"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_dataset.id = 1
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                result = service.top_downloaded_datasets_last_month(limit=1)
                
                assert result[0]['dataset'] == mock_dataset
                assert result[0]['dataset'].id == 1
    
    def test_service_respects_limit_parameter(self):
        """Verifica que respeta el parámetro limit"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                mock_dataset = MagicMock()
                mock_dataset.ds_meta_data = None
                mock_movie_dataset_class.query.get.return_value = mock_dataset
                
                service.top_downloaded_datasets_last_month(limit=10)
                
                mock_repo_method.assert_called_once_with(10)
                
    
    def test_service_returns_only_limited_results_when_more_exist(self):
        """Verifica explícitamente que cuando hay 4 datasets se devuelven solo 3"""

        service = DSDownloadRecordService()

        # Mock del repositorio que simula que hay 4 datasets pero solo retorna 3
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            # Simular: hay 4 datasets en total, pero el repositorio retorna solo los 3 más descargados
            mock_repo_method.return_value = [
                (1, 100),  # Top 1
                (2, 80),   # Top 2
                (3, 60),   # Top 3
                # (4, 40) - Este no se devuelve porque limit=3
            ]

            # Mock de MovieDataset
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_class:
                mock_datasets = []
                for i, (dataset_id, count) in enumerate([(1, 100), (2, 80), (3, 60)]):
                    mock_dataset = MagicMock()
                    mock_dataset.id = dataset_id
                    mock_dataset.ds_meta_data = None
                    mock_datasets.append(mock_dataset)
                
                mock_movie_class.query.get.side_effect = mock_datasets

                # Ejecutar servicio con limit=3
                result = service.top_downloaded_datasets_last_month(limit=3)

                # Verificación explícita: aunque hay 4 datasets, solo se devuelven 3
                assert len(result) == 3, "Debe devolver exactamente 3 resultados aunque haya 4 disponibles"
                assert result[0]['download_count'] == 100
                assert result[1]['download_count'] == 80
                assert result[2]['download_count'] == 60
                # El dataset con 40 descargas NO está en los resultados
                download_counts = [item['download_count'] for item in result]
                assert 40 not in download_counts, "El cuarto dataset no debe estar en los resultados"
    
    def test_service_returns_empty_list_when_no_downloads(self):
        """Verifica que retorna lista vacía cuando no hay descargas"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = []
            
            result = service.top_downloaded_datasets_last_month(limit=3)
            
            assert result == []
            assert isinstance(result, list)
    
    def test_service_handles_multiple_datasets_with_authors(self):
        """Verifica que maneja correctamente múltiples datasets con autores"""
        service = DSDownloadRecordService()
        
        with patch.object(service.repository, 'top_downloaded_datasets_last_month') as mock_repo_method:
            mock_repo_method.return_value = [(1, 10), (2, 8), (3, 5)]
            
            with patch('app.modules.dataset.services.MovieDataset') as mock_movie_dataset_class:
                # Crear datasets mock con diferentes autores
                mock_datasets = []
                for i, (dataset_id, count) in enumerate([(1, 10), (2, 8), (3, 5)]):
                    mock_dataset = MagicMock()
                    mock_author = MagicMock()
                    mock_author.name = f"Author {i+1}"
                    mock_dataset.ds_meta_data.authors = [mock_author]
                    mock_dataset.id = dataset_id
                    mock_datasets.append(mock_dataset)
                
                # Mock query.get para retornar los datasets correctos
                mock_movie_dataset_class.query.get.side_effect = mock_datasets
                
                result = service.top_downloaded_datasets_last_month(limit=3)
                
                assert len(result) == 3
                assert result[0]['author'] == "Author 1"
                assert result[1]['author'] == "Author 2"
                assert result[2]['author'] == "Author 3"
                assert result[0]['download_count'] == 10
                assert result[1]['download_count'] == 8
                assert result[2]['download_count'] == 5
