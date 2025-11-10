from core.seeders.BaseSeeder import BaseSeeder
from app.modules.fakenodo.models import Fakenodo
from app.modules.dataset.models import BaseDataset

class FakenodoSeeder(BaseSeeder):
    priority = 4  # se ejecuta después de AuthSeeder, DataSeeder y MovieSeeder

    def run(self):

        dataset1 = BaseDataset.query.filter_by(id=1).first()
        dataset2 = BaseDataset.query.filter_by(id=2).first()
        dataset3 = BaseDataset.query.filter_by(id=3).first()

        if not all([dataset1, dataset2, dataset3]):
            print("Algunos datasets no existen. Ejecuta primero el MovieSeeder o DataSeeder.")
            return

        fakenodo1 = Fakenodo(
            status="draft",
            dataset_id = dataset1.id,
            dataset=dataset1,
        )

        fakenodo2 = Fakenodo(
            status="published",
            dataset_id = dataset2.id,
            dataset=dataset2,
        )

        fakenodo3 = Fakenodo(
            status="draft",
            dataset_id = dataset3.id,
            dataset=dataset3,
        )

        self.seed([fakenodo1, fakenodo2, fakenodo3])