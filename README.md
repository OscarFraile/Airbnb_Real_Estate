# Análisis del Mercado de Alquiler Turístico en Madrid — Predicción de Rentabilidad con XGBoost

Modelo de clasificación binaria para predecir si un alojamiento de Airbnb en Madrid tiene alta o baja rentabilidad, a partir de datos de Inside Airbnb 2025.

## Tecnologías

Python · Pandas · Scikit-learn · XGBoost · Matplotlib · Folium · Jupyter Notebook

## Estructura del repositorio

```
├── 01_Documentos/        # Documentación y diseño del proyecto
├── 02_Datos/
│   ├── 01_Originales/    # Dataset crudo de Inside Airbnb
│   └── 01_Trabajo/       # Datasets procesados en cada etapa
├── 03_Notebooks/
│   └── 02_Desarrollo/    # Notebooks numerados por fase del pipeline
├── 04_Modelos/           # Pipelines serializados (.pickle)
├── 05_Resultados/        # Outputs finales y variables seleccionadas
└── README.md
```

## Pipeline

El proyecto sigue un pipeline end-to-end estructurado en notebooks numerados:

1. Diseño del problema y definición del target
2. Creación del datamart analítico
3. Preparación y limpieza de datos
4. Análisis exploratorio (EDA)
5. Calidad de datos y detección de outliers
6. Automatización del preprocesado
7. Transformación de variables
8. Preselección de features
9. Balanceo del dataset
10. Modelización para clasificación
11. Preparación para producción
12. Código de ejecución y aplicación

## Resultados

- **Modelo final:** XGBoost Classifier con búsqueda aleatoria de hiperparámetros
- **AUC-ROC sobre validación:** 0.997
- **Evaluación adicional:** Gain chart, Lift curve y ROC curve
- El modelo se ejecuta sobre un dataset de validación no visto durante el entrenamiento

## Cómo ejecutarlo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar los notebooks en orden desde 03_Notebooks/02_Desarrollo/
# Empezar por: 01_Diseño del proyecto.ipynb
```

Los modelos entrenados están serializados en `04_Modelos/` como archivos `.pickle` para su reutilización sin reentrenamiento.

## Visualización interactiva

El proyecto incluye un mapa interactivo (Folium) con los alojamientos segmentados por barrio y coloreados según su potencial de rentabilidad, combinando coordenadas geográficas con las predicciones del modelo.

---

Proyecto académico desarrollado durante el Master en Data Science de Evolve.
