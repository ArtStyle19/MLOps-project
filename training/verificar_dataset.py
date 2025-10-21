#!/usr/bin/env python3
"""
Script para verificar el dataset y mostrar estadísticas antes del entrenamiento
"""

import os
from pathlib import Path

def contar_archivos(directorio, extension="*.jpg"):
    """Cuenta archivos con una extensión específica en un directorio"""
    if not Path(directorio).exists():
        return 0
    return len(list(Path(directorio).glob(extension)))

def verificar_dataset():
    """Verifica la estructura del dataset y muestra estadísticas"""
    print("=== VERIFICACIÓN DEL DATASET ===")
    
    # Verificar estructura del dataset
    dataset_path = Path("dataset")
    if not dataset_path.exists():
        print("[ERROR] No se encontró la carpeta 'dataset'")
        return False
    
    print("[OK] Carpeta 'dataset' encontrada")
    
    # Verificar cada split
    splits = ['train', 'valid', 'test']
    total_imagenes = 0
    total_etiquetas = 0
    
    for split in splits:
        images_dir = dataset_path / split / 'images'
        labels_dir = dataset_path / split / 'labels'
        
        num_imagenes = contar_archivos(images_dir, "*.jpg")
        num_etiquetas = contar_archivos(labels_dir, "*.txt")
        
        print(f"\n[FOLDER] {split.upper()}:")
        print(f"   Imágenes: {num_imagenes}")
        print(f"   Etiquetas: {num_etiquetas}")
        
        if num_imagenes != num_etiquetas:
            print(f"   [WARNING] Advertencia: Número de imágenes y etiquetas no coincide")
        
        total_imagenes += num_imagenes
        total_etiquetas += num_etiquetas
    
    print(f"\n[SUMMARY] RESUMEN TOTAL:")
    print(f"   Total imágenes: {total_imagenes}")
    print(f"   Total etiquetas: {total_etiquetas}")
    
    # Calcular 10% de cada split
    print(f"\n[TARGET] DATOS PARA ENTRENAMIENTO (10% de cada split):")
    for split in splits:
        images_dir = dataset_path / split / 'images'
        num_imagenes = contar_archivos(images_dir, "*.jpg")
        num_10_porciento = max(1, int(num_imagenes * 0.1))
        print(f"   {split}: {num_10_porciento} imágenes (de {num_imagenes})")
    
    # Verificar modelo pre-entrenado
    print(f"\n[MODEL] MODELO PRE-ENTRENADO:")
    if Path("yolov8n.pt").exists():
        print("   [OK] yolov8n.pt encontrado")
    else:
        print("   [WARNING] yolov8n.pt no encontrado (se descargará automáticamente)")
    
    # Verificar carpeta de salida
    print(f"\n[OUTPUT] CARPETA DE SALIDA:")
    modelo_path = Path("modelo_entrenado")
    if modelo_path.exists():
        print("   [OK] Carpeta 'modelo_entrenado' lista")
    else:
        print("   [WARNING] Carpeta 'modelo_entrenado' no existe (se creará)")
    
    return True

def mostrar_configuracion_entrenamiento():
    """Muestra la configuración que se usará para el entrenamiento"""
    print(f"\n[CONFIG] CONFIGURACIÓN DE ENTRENAMIENTO OPTIMIZADA:")
    print(f"   Modelo: YOLOv8n (nano)")
    print(f"   Épocas: 25 (reducidas para entrenamiento más rápido)")
    print(f"   Tamaño de imagen: 416x416 (reducido para mayor velocidad)")
    print(f"   Batch size: 32 (aumentado para mejor rendimiento)")
    print(f"   Dispositivo: CUDA (si está disponible) o CPU")
    print(f"   Proyecto: modelo_entrenado/chaleco_detection")
    print(f"   Clases: sin_chaleco, con_chaleco")
    print(f"   Optimizaciones: Early stopping, Learning rate scheduler, Mosaic augmentation")
    
    print(f"\n[FILES] ARCHIVOS QUE SE GENERARÁN:")
    print(f"   - modelo_entrenado/chaleco_detection/weights/best.pt")
    print(f"   - modelo_entrenado/chaleco_detection/weights/last.pt")
    print(f"   - modelo_entrenado/chaleco_detection/results.png")
    print(f"   - modelo_entrenado/chaleco_detection/confusion_matrix.png")
    print(f"   - modelo_entrenado/chaleco_detection/val_batch*.jpg")

if __name__ == "__main__":
    if verificar_dataset():
        mostrar_configuracion_entrenamiento()
        print(f"\n[START] Para iniciar el entrenamiento, ejecuta:")
        print(f"   python entrenamiento.py")
    else:
        print(f"\n[ERROR] No se puede proceder con el entrenamiento")
