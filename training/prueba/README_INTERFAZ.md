# 🔍 Interfaz de Detección de Chalecos de Seguridad

Esta interfaz gráfica permite probar el modelo entrenado de detección de chalecos de seguridad usando la cámara en tiempo real.

## 🚀 Características

- **Detección en tiempo real** con cámara web
- **Interfaz gráfica intuitiva** con tkinter
- **Carga automática del modelo** entrenado
- **Captura de fotos** durante la detección
- **Estadísticas en tiempo real** de detecciones
- **Feedback visual** con colores para diferentes estados

## 📋 Requisitos

- Python 3.8+
- Cámara web funcionando
- Modelo entrenado (opcional, usa modelo pre-entrenado como fallback)

## 🛠️ Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements_interfaz.txt
```

2. **Ejecutar la interfaz:**
```bash
python interfaz.py
```

## 🎮 Uso de la Interfaz

### Controles Principales:

1. **▶️ Iniciar Cámara**: Comienza la detección en tiempo real
2. **⏹️ Detener Cámara**: Detiene la detección
3. **📸 Capturar Foto**: Guarda una foto del frame actual
4. **📁 Cargar Modelo**: Permite cargar un modelo personalizado

### Información Mostrada:

- **Estado del modelo**: Indica si el modelo está cargado
- **Detección actual**: Muestra qué se detectó (sin_chaleco/con_chaleco)
- **Confianza**: Nivel de confianza de la detección
- **Estadísticas**: Contador de detecciones por clase

## 📁 Estructura de Archivos

```
prueba/
├── interfaz.py              # Interfaz gráfica principal
├── requirements_interfaz.txt # Dependencias específicas
├── README_INTERFAZ.md       # Esta documentación
└── capturas/               # Fotos capturadas (se crea automáticamente)
```

## 🔧 Configuración del Modelo

La interfaz busca automáticamente el modelo entrenado en estas ubicaciones:

1. `modelo_entrenado/chaleco_detection/weights/best.pt`
2. `../modelo_entrenado/chaleco_detection/weights/best.pt`
3. `chaleco_detection/weights/best.pt`

Si no encuentra el modelo específico, usa el modelo pre-entrenado YOLOv8n como fallback.

## 🎯 Códigos de Color

- **Verde**: Persona con chaleco detectada
- **Rojo**: Persona sin chaleco detectada
- **Azul**: Otras detecciones
- **Gris**: Sin detección

## 📸 Capturas

Las fotos se guardan automáticamente en la carpeta `capturas/` con timestamp único:
- Formato: `captura_YYYYMMDD_HHMMSS.jpg`

## ⚠️ Solución de Problemas

### Error: "No se pudo abrir la cámara"
- Verifica que la cámara esté conectada y funcionando
- Cierra otras aplicaciones que puedan estar usando la cámara
- Prueba cambiar el índice de cámara en el código (0, 1, 2...)

### Error: "No se pudo importar ultralytics"
```bash
pip install ultralytics
```

### Modelo no se carga
- Verifica que el archivo `best.pt` existe en la ubicación correcta
- Usa el botón "📁 Cargar Modelo" para seleccionar manualmente

## 🔄 Flujo de Trabajo

1. **Entrenar modelo**: Ejecuta `entrenamiento.py` primero
2. **Probar modelo**: Ejecuta `interfaz.py` para probar
3. **Capturar evidencia**: Usa el botón de captura para guardar detecciones
4. **Analizar resultados**: Revisa las estadísticas y fotos capturadas

## 🎨 Personalización

Puedes modificar el archivo `interfaz.py` para:
- Cambiar el tamaño de la ventana
- Modificar los colores de la interfaz
- Ajustar la configuración de detección
- Agregar nuevas funcionalidades

## 📊 Rendimiento

- **FPS**: Depende del hardware (típicamente 15-30 FPS)
- **Latencia**: Baja latencia para detección en tiempo real
- **Precisión**: Depende del modelo entrenado

¡Disfruta probando tu modelo de detección de chalecos de seguridad! 🎉

