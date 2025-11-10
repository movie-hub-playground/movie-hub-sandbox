"""Add 2 versions to dataset 3 (for compare testing)"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '56a793d4d64d'
down_revision = '05662d95869a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1️⃣ Asegurar que el dataset 3 tiene un metadato válido (si no existe, lo creamos)
    conn.execute(sa.text("""
        INSERT INTO ds_meta_data (
            id, title, description, publication_type, publication_doi,
            dataset_doi, tags, deposition_id
        )
        VALUES (
            999,
            'Sample dataset 3',
            'Original dataset for version comparison testing.',
            'JOURNAL_ARTICLE',
            'https://doi.org/10.1234/moviehub.demo3',
            '10.1234/dataset3',
            'movies,testing,comparison',
            998
        )
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            publication_type = VALUES(publication_type),
            publication_doi = VALUES(publication_doi),
            dataset_doi = VALUES(dataset_doi),
            tags = VALUES(tags),
            deposition_id = VALUES(deposition_id);
    """))

    # 2️⃣ Asociar el dataset 3 con este metadato (si aún no lo está)
    conn.execute(sa.text("""
        UPDATE base_dataset
        SET ds_meta_data_id = 999,
            current_version = '2.0'
        WHERE id = 3;
    """))

    # 3️⃣ Crear dos versiones de prueba (1.0 original, 2.0 modificada)
    conn.execute(sa.text("""
        INSERT INTO version (dataset_id, version_number, created_at)
        VALUES
            (3, '1.0', '2025-01-01'),
            (3, '2.0', '2025-02-01')
        ON DUPLICATE KEY UPDATE
            created_at = VALUES(created_at);
    """))

    # 4️⃣ Simular cambio de descripción para la versión 2.0
    conn.execute(sa.text("""
        UPDATE ds_meta_data
        SET description = 'Updated dataset description for version 2.0 testing in Movie-Hub — includes new metadata and extended examples.'
        WHERE id = 999;
    """))

    print("✅ Added versions 1.0 and 2.0 to dataset 3 for comparison testing.")


def downgrade():
    conn = op.get_bind()

    # Eliminar las versiones creadas
    conn.execute(sa.text("DELETE FROM version WHERE dataset_id = 3;"))

    # Restaurar descripción original
    conn.execute(sa.text("""
        UPDATE ds_meta_data
        SET description = 'Original dataset for version comparison testing.'
        WHERE id = 999;
    """))

    print("🧹 Removed test versions for dataset 3 and restored metadata description.")
