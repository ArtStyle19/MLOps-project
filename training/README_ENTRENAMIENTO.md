# Entrenamiento YOLO para Detección de Chalecos de Seguridad

Este proyecto entrena un modelo YOLO para detectar si una persona lleva chaleco de seguridad o no, usando solo el 10% de los datos de cada carpeta (train, valid, test).

## 📊 Estadísticas del Dataset

- **Train**: 2,728 imágenes → 272 imágenes (10%)
- **Valid**: 779 imágenes → 77 imágenes (10%)  
- **Test**: 390 imágenes → 39 imágenes (10%)
- **Total**: 3,897 imágenes → 388 imágenes para entrenamiento

## 🚀 Cómo usar

### 1. Verificar el dataset
```bash
python verificar_dataset.py
```

### 2. Ejecutar el entrenamiento
```bash
python entrenamiento.py
```

## 📁 Estructura del proyecto

```
IX-MODELO-YOLO/
├── dataset/                    # Dataset original
│   ├── train/images/          # 2,728 imágenes
│   ├── train/labels/          # 2,728 etiquetas
│   ├── valid/images/          # 779 imágenes
│   ├── valid/labels/          # 779 etiquetas
│   ├── test/images/           # 390 imágenes
│   └── test/labels/           # 390 etiquetas
├── dataset_reducido/          # Dataset con 10% de datos (se crea automáticamente)
├── modelo_entrenado/          # Modelo entrenado y resultados
│   └── chaleco_detection/
│       ├── weights/
│       │   ├── best.pt        # Mejor modelo
│       │   └── last.pt         # Último modelo
│       ├── results.png        # Gráficos de entrenamiento
│       └── confusion_matrix.png
├── entrenamiento.py           # Script principal de entrenamiento
├── verificar_dataset.py       # Script de verificación
└── requirements.txt           # Dependencias
```

## ⚙️ Configuración del entrenamiento (OPTIMIZADA PARA VELOCIDAD)

- **Modelo**: YOLOv8n (nano)
- **Épocas**: 25 (reducidas para entrenamiento más rápido)
- **Tamaño de imagen**: 416x416 (reducido para mayor velocidad)
- **Batch size**: 32 (aumentado para mejor rendimiento)
- **Dispositivo**: CUDA (si está disponible) o CPU
- **Proyecto**: modelo_entrenado/chaleco_detection
- **Clases**: sin_chaleco, con_chaleco
- **Optimizaciones**: Early stopping, Learning rate scheduler, Mosaic augmentation

## 📋 Archivos generados

Después del entrenamiento se generarán:

- `modelo_entrenado/chaleco_detection/weights/best.pt` - Mejor modelo
- `modelo_entrenado/chaleco_detection/weights/last.pt` - Último modelo
- `modelo_entrenado/chaleco_detection/results.png` - Gráficos de entrenamiento
- `modelo_entrenado/chaleco_detection/confusion_matrix.png` - Matriz de confusión
- `modelo_entrenado/chaleco_detection/val_batch*.jpg` - Imágenes de validación

## 🔧 Requisitos

- Python 3.8+
- PyTorch
- Ultralytics YOLO
- OpenCV
- Pillow
- NumPy
- Matplotlib

Instalar dependencias:
```bash
pip install -r requirements.txt
```

## 📝 Notas importantes

1. **Dataset reducido**: Se crea automáticamente una copia con solo el 10% de los datos
2. **Reproducibilidad**: Se usa `random.seed(42)` para resultados consistentes
3. **Modelo pre-entrenado**: Se descarga automáticamente `yolov8n.pt` si no existe
4. **Validación**: El script verifica que el número de imágenes y etiquetas coincida
5. **Guardado automático**: Los resultados se guardan en `modelo_entrenado/`

## 🎯 Resultados esperados

El entrenamiento debería completarse en aproximadamente 15-30 minutos dependiendo del hardware (reducido significativamente con las optimizaciones), y generará un modelo capaz de detectar si una persona lleva chaleco de seguridad con buena precisión usando solo el 10% de los datos disponibles.
