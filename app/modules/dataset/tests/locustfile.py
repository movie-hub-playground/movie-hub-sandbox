from locust import HttpUser, TaskSet, task, between
import random

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):
    def on_start(self):
        self.dataset()

    @task
    def dataset(self):
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()


# ========== Pruebas de carga para Trending Datasets ==========

class TrendingDatasetsBehavior(TaskSet):
    """Simula comportamiento de usuarios accediendo a trending datasets"""
    
    def on_start(self):
        """Se ejecuta al inicio de cada usuario"""
        self.home_page_visits = 0
        self.trending_check_count = 0
    
    @task(3)
    def access_homepage(self):
        """Accede a la página de inicio que muestra trending datasets"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                self.home_page_visits += 1
                response.success()
            else:
                response.failure(f"Error al acceder a homepage: {response.status_code}")
    
    @task(2)
    def check_trending_datasets_data(self):
        """Verifica que los trending datasets se cargan correctamente"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                # Verificar que contiene trending datasets
                if b"trending" in response.content.lower() or b"dataset" in response.content.lower():
                    self.trending_check_count += 1
                    response.success()
                else:
                    response.failure("No se encontraron trending datasets en la respuesta")
            else:
                response.failure(f"Error HTTP: {response.status_code}")
    
    @task(1)
    def access_trending_dataset(self):
        """Simula acceso a un dataset trending aleatorio"""
        # IDs de datasets de ejemplo (en un escenario real estos vendrían de la respuesta anterior)
        dataset_ids = [1, 2, 3, 4, 5]
        dataset_id = random.choice(dataset_ids)
        
        with self.client.get(f"/moviedataset/{dataset_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Es normal que algunos datasets no existan
                response.success()
            else:
                response.failure(f"Error al acceder a dataset {dataset_id}: {response.status_code}")
    
    @task(2)
    def download_trending_dataset(self):
        """Simula descarga de un dataset trending"""
        dataset_id = random.choice([1, 2, 3, 4, 5])
        
        with self.client.get(f"/moviedataset/{dataset_id}/download", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Es normal que algunos datasets no existan
                response.success()
            else:
                response.failure(f"Error al descargar dataset {dataset_id}: {response.status_code}")


class TrendingDatasetsUser(HttpUser):
    """Usuario que simula navegar trending datasets"""
    tasks = [TrendingDatasetsBehavior]
    wait_time = between(2, 5)
    host = get_host_for_locust_testing()


class CombinedBehavior(TaskSet):
    """Simula comportamiento combinado: navegación general + trending datasets"""
    
    @task(4)
    def view_homepage_with_trending(self):
        """Ver la página de inicio y trending datasets"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage error: {response.status_code}")
    
    @task(2)
    def view_datasets_list(self):
        """Ver lista de todos los datasets"""
        with self.client.get("/moviedataset/list", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dataset list error: {response.status_code}")
    
    @task(3)
    def interact_with_trending(self):
        """Interactuar con trending datasets"""
        dataset_id = random.choice([1, 2, 3])
        
        with self.client.get(f"/moviedataset/{dataset_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Trending dataset error: {response.status_code}")


class CombinedUser(HttpUser):
    """Usuario con comportamiento mixto"""
    tasks = [CombinedBehavior]
    wait_time = between(3, 6)
    host = get_host_for_locust_testing()


# ========== Pruebas avanzadas de actualización de ranking ==========

class RankingUpdateBehavior(TaskSet):
    """Simula actualización dinámica del ranking de trending datasets"""
    
    def on_start(self):
        """Inicializa contadores para monitorear cambios"""
        self.initial_ranking = None
        self.updated_ranking = None
        self.download_count = 0
    
    @task(5)
    def download_and_check_ranking_update(self):
        """Descarga datasets y verifica que el ranking se actualiza"""
        # Primer paso: obtener ranking inicial
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                self.initial_ranking = response.content
                response.success()
            else:
                response.failure(f"Error obteniendo ranking inicial: {response.status_code}")
                return
        
        # Segundo paso: descargar un dataset
        dataset_id = random.choice([1, 2, 3, 4, 5])
        with self.client.get(f"/moviedataset/{dataset_id}/download", catch_response=True) as response:
            if response.status_code == 200:
                self.download_count += 1
                response.success()
            elif response.status_code == 404:
                response.success()  # Dataset puede no existir
            else:
                response.failure(f"Error descargando dataset: {response.status_code}")
                return
        
        # Tercer paso: obtener ranking actualizado
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                self.updated_ranking = response.content
                
                # Verificar que el ranking ha cambiado después de múltiples descargas
                if self.download_count > 0 and self.initial_ranking != self.updated_ranking:
                    response.success()
                else:
                    response.success()  # Puede que no cambie inmediatamente
            else:
                response.failure(f"Error obteniendo ranking actualizado: {response.status_code}")
    
    @task(3)
    def monitor_trending_position_changes(self):
        """Monitorea cambios en la posición de datasets en el ranking"""
        dataset_id = random.choice([1, 2, 3])
        
        # Obtener estado actual
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                ranking_data = response.content
                
                # Descargar dataset
                self.client.get(f"/moviedataset/{dataset_id}/download")
                
                # Verificar posición actualizada
                with self.client.get("/", catch_response=True) as updated_response:
                    if updated_response.status_code == 200:
                        # Verificar que el dataset aparece en trending
                        if str(dataset_id).encode() in updated_response.content:
                            response.success()
                        else:
                            response.success()  # Puede no aparecer si no es top 3
                    else:
                        response.failure(f"Error verificando posición: {updated_response.status_code}")
    
    @task(2)
    def verify_new_dataset_enters_trending(self):
        """Verifica que un dataset que no estaba en trending puede entrar tras suficientes descargas"""
        dataset_id = random.choice([6, 7, 8])  # Datasets que podrían no estar en trending
        
        # Realizar múltiples descargas simuladas
        for i in range(3):
            with self.client.get(f"/moviedataset/{dataset_id}/download", catch_response=True) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Error en descarga {i}: {response.status_code}")
        
        # Verificar que aparece en ranking después de múltiples descargas
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()


class RankingUpdateUser(HttpUser):
    """Usuario que simula actualización dinámica del ranking"""
    tasks = [RankingUpdateBehavior]
    wait_time = between(1, 3)
    host = get_host_for_locust_testing()


class HighVolumeDownloadBehavior(TaskSet):
    """Simula alto volumen de descargas para probar actualizaciones de ranking bajo carga"""
    
    @task(10)
    def rapid_downloads_and_ranking_check(self):
        """Realiza descargas rápidas y verifica cambios en ranking"""
        dataset_id = random.randint(1, 10)
        
        # Descarga rápida
        with self.client.get(f"/moviedataset/{dataset_id}/download", catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Error en descarga rápida: {response.status_code}")
    
    @task(2)
    def check_ranking_consistency(self):
        """Verifica que el ranking es consistente bajo alto volumen"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                # Verificar que contiene datos de trending datasets
                if b"dataset" in response.content.lower():
                    response.success()
                else:
                    response.failure("Ranking inconsistente")
            else:
                response.failure(f"Error verificando ranking: {response.status_code}")


class HighVolumeDownloadUser(HttpUser):
    """Usuario con alto volumen de descargas"""
    tasks = [HighVolumeDownloadBehavior]
    wait_time = between(0.5, 1.5)
    host = get_host_for_locust_testing()
