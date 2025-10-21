# Entrenamiento YOLO para Detección de Chalecos de Seguridad

Este proyecto entrena un modelo YOLO para detectar si una persona lleva chaleco de seguridad o no, usando solo el 10% de los datos de cada carpeta (train, valid, test).

## 📊 Estadísticas del Dataset

- _Train_: 2,728 imágenes → 272 imágenes (10%)
- _Valid_: 779 imágenes → 77 imágenes (10%)
- _Test_: 390 imágenes → 39 imágenes (10%)
- _Total_: 3,897 imágenes → 388 imágenes para entrenamiento

## 🚀 Cómo usar

### 1. Verificar el dataset

bash
python verificar_dataset.py

### 2. Ejecutar el entrenamiento

bash
python entrenamiento.py

## 📁 Estructura del proyecto

IX-MODELO-YOLO/
├── dataset/ # Dataset original
│ ├── train/images/ # 2,728 imágenes
│ ├── train/labels/ # 2,728 etiquetas
│ ├── valid/images/ # 779 imágenes
│ ├── valid/labels/ # 779 etiquetas
│ ├── test/images/ # 390 imágenes
│ └── test/labels/ # 390 etiquetas
├── dataset_reducido/ # Dataset con 10% de datos (se crea automáticamente)
├── modelo_entrenado/ # Modelo entrenado y resultados
│ └── chaleco_detection/
│ ├── weights/
│ │ ├── best.pt # Mejor modelo
│ │ └── last.pt # Último modelo
│ ├── results.png # Gráficos de entrenamiento
│ └── confusion_matrix.png
├── entrenamiento.py # Script principal de entrenamiento
├── verificar_dataset.py # Script de verificación
└── requirements.txt # Dependencias

## ⚙️ Configuración del entrenamiento (OPTIMIZADA PARA VELOCIDAD)

- _Modelo_: YOLOv8n (nano)
- _Épocas_: 25 (reducidas para entrenamiento más rápido)
- _Tamaño de imagen_: 416x416 (reducido para mayor velocidad)
- _Batch size_: 32 (aumentado para mejor rendimiento)
- _Dispositivo_: CUDA (si está disponible) o CPU
- _Proyecto_: modelo_entrenado/chaleco_detection
- _Clases_: sin_chaleco, con_chaleco
- _Optimizaciones_: Early stopping, Learning rate scheduler, Mosaic augmentation

## 📋 Archivos generados

Después del entrenamiento se generarán:

- modelo_entrenado/chaleco_detection/weights/best.pt - Mejor modelo
- modelo_entrenado/chaleco_detection/weights/last.pt - Último modelo
- modelo_entrenado/chaleco_detection/results.png - Gráficos de entrenamiento
- modelo_entrenado/chaleco_detection/confusion_matrix.png - Matriz de confusión
- modelo_entrenado/chaleco_detection/val_batch\*.jpg - Imágenes de validación

## 🔧 Requisitos

- Python 3.8+
- PyTorch
- Ultralytics YOLO
- OpenCV
- Pillow
- NumPy
- Matplotlib

Instalar dependencias:
bash
pip install -r requirements.txt

## 📝 Notas importantes

1. _Dataset reducido_: Se crea automáticamente una copia con solo el 10% de los datos
2. _Reproducibilidad_: Se usa random.seed(42) para resultados consistentes
3. _Modelo pre-entrenado_: Se descarga automáticamente yolov8n.pt si no existe
4. _Validación_: El script verifica que el número de imágenes y etiquetas coincida
5. _Guardado automático_: Los resultados se guardan en modelo_entrenado/

## 🎯 Resultados esperados

El entrenamiento debería completarse en aproximadamente 15-30 minutos dependiendo del hardware (reducido significativamente con las optimizaciones), y generará un modelo capaz de detectar si una persona lleva chaleco de seguridad con buena precisión usando solo el 10% de los datos disponibles.
