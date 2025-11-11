from locust import HttpUser, TaskSet, task, between
from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token
from bs4 import BeautifulSoup


class MovieDatasetBehavior(TaskSet):
    def on_start(self):
        self.login()
        self.last_dataset_id = None

    def login(self):
        """Simula login con token CSRF"""
        response = self.client.get("/login")
        if response.status_code != 200:
            print(f"Login page failed: {response.status_code}")
            return

        csrf_token = get_csrf_token(response)
        response = self.client.post(
            "/login",
            data={
                "email": "user1@example.com",
                "password": "1234",
                "csrf_token": csrf_token
            },
            allow_redirects=True
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")

    @task(3)
    def list_all_datasets(self):
        """GET /moviedataset/list"""
        response = self.client.get("/moviedataset/list")
        if response.status_code != 200:
            print(f"List datasets failed: {response.status_code}")
        else:
            try:
                # Intentar capturar un ID de dataset de la tabla HTML
                soup = BeautifulSoup(response.text, "html.parser")
                link = soup.find("a", href=True)
                if link and "/moviedataset/" in link["href"]:
                    self.last_dataset_id = link["href"].rstrip("/").split("/")[-1]
            except Exception:
                self.last_dataset_id = None

    @task(2)
    def list_my_datasets(self):
        """GET /moviedataset/my-datasets"""
        response = self.client.get("/moviedataset/my-datasets")
        if response.status_code != 200:
            print(f"My datasets failed: {response.status_code}")

    @task(1)
    def download_dataset(self):
        """GET /moviedataset/<id>/download"""
        if not self.last_dataset_id:
            # Si no hay dataset previo, intenta recuperar uno
            self.list_all_datasets()
            if not self.last_dataset_id: # se queda aquí ya que no encuentra ninguno
                return

        dataset_id = self.last_dataset_id
        response = self.client.get(f"/moviedataset/{dataset_id}/download")
        if response.status_code != 200:
            print(f"Download dataset failed: {response.status_code}")

    @task(1)
    def view_dataset_detail(self):
        """GET /moviedataset/<id>"""
        if not self.last_dataset_id:
            return
        response = self.client.get(f"/moviedataset/{self.last_dataset_id}")
        if response.status_code != 200:
            print(f"View dataset failed: {response.status_code}")


class MovieDatasetUser(HttpUser):
    tasks = [MovieDatasetBehavior]
    wait_time = between(2, 5)
    host = get_host_for_locust_testing()
