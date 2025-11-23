<div style="text-align: center">
  <img src="app/static/img/logos/movie-hub-dark.png" alt="Logo" />
</div>

# 🎬 Movie-Hub

**Movie-Hub** es un repositorio centralizado de *datasets* de películas diseñado para facilitar análisis de datos, investigación académica y desarrollo de modelos de machine learning. El objetivo es ofrecer datos limpios, organizados y bien documentados relacionados con el mundo del cine.

---

## 📚 Contenido del repositorio

Este proyecto incluye:

- **Metadatos de películas**  
  Títulos, años, géneros, duración, reparto, producción y más.

- **Ratings y reseñas**  
  Datos de calificaciones provenientes de diversas fuentes.

- **Taquilla (Box Office)**  
  Presupuestos, recaudación global, local y comparativa.

- **Datasets derivados o enriquecidos**  
  Construidos a partir de fuentes abiertas o APIs públicas.

- **Scripts para procesamiento**  
  Herramientas para limpieza, normalización u obtención automática de datos.

Cada dataset cuenta con su propia documentación, donde se detalla origen, estructura, licencia y método de recolección.

---

## 🗂️ Estructura del proyecto

```text
movie-hub/
├── datasets/
│   ├── movies/
│   │   ├── movies.csv
│   │   └── README.md
│   ├── ratings/
│   │   ├── ratings.csv
│   │   └── README.md
│   ├── box_office/
│   │   ├── box_office.csv
│   │   └── README.md
│   └── ...
│
├── scripts/
│   ├── fetch_data.py
│   ├── clean_data.py
│   └── utils.py
│
├── docs/
│   ├── schema_overview.md
│   └── sources.md
│
└── README.md
