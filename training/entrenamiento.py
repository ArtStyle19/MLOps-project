#!/usr/bin/env python3
"""
Script de entrenamiento YOLO para detección de chalecos de seguridad
Entrena un modelo YOLO usando solo el 10% de las imágenes de train, valid y test
y sube el modelo resultante a S3.
"""

import os
import shutil
import random
import yaml
from pathlib import Path
from ultralytics import YOLO
import torch
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def crear_dataset_reducido(porcentaje=0.1):
    """
    Crea un dataset reducido con el porcentaje especificado de cada carpeta
    """
    print(f"Creando dataset reducido con {porcentaje*100}% de los datos...")
    dataset_reducido = Path("dataset_reducido")
    dataset_reducido.mkdir(exist_ok=True)

    for split in ['train', 'valid', 'test']:
        (dataset_reducido / split / 'images').mkdir(parents=True, exist_ok=True)
        (dataset_reducido / split / 'labels').mkdir(parents=True, exist_ok=True)

    for split in ['train', 'valid', 'test']:
        print(f"\nProcesando {split}...")
        images_dir = Path(f"dataset/{split}/images")
        labels_dir = Path(f"dataset/{split}/labels")

        if not images_dir.exists():
            print(f"Advertencia: No se encontró la carpeta {images_dir}")
            continue

        image_files = list(images_dir.glob("*.jpg"))
        total_images = len(image_files)
        num_seleccionadas = max(1, int(total_images * porcentaje))

        print(f"  Total de imágenes: {total_images}")
        print(f"  Seleccionando: {num_seleccionadas}")

        random.seed(42)
        imagenes_seleccionadas = random.sample(image_files, num_seleccionadas)

        for img_path in imagenes_seleccionadas:
            dst_img = dataset_reducido / split / 'images' / img_path.name
            shutil.copy2(img_path, dst_img)

            label_name = img_path.stem + '.txt'
            src_label = labels_dir / label_name
            if src_label.exists():
                dst_label = dataset_reducido / split / 'labels' / label_name
                shutil.copy2(src_label, dst_label)
            else:
                print(f"  Advertencia: No se encontró la etiqueta {src_label}")

    print(f"\nDataset reducido creado en: {dataset_reducido}")
    return dataset_reducido


def crear_config_yaml(dataset_path):
    """
    Crea el archivo data.yaml para el entrenamiento
    """
    config = {
        'path': str(dataset_path.absolute()),
        'train': 'train/images',
        'val': 'valid/images',
        'test': 'test/images',
        'nc': 2,
        'names': ['sin_chaleco', 'con_chaleco']
    }

    yaml_path = dataset_path / 'data.yaml'
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"Archivo de configuración creado: {yaml_path}")
    return yaml_path


def entrenar_modelo(config_path, epochs=25, imgsz=416):
    """
    Entrena el modelo YOLO con configuración optimizada para velocidad
    """
    print(f"\nIniciando entrenamiento optimizado...")
    print(f"Épocas: {epochs}")
    print(f"Tamaño de imagen: {imgsz}")

    model = YOLO('yolov8n.pt')

    results = model.train(
        data=str(config_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=32,
        device='cuda' if torch.cuda.is_available() else 'cpu',
        project='modelo_entrenado',
        name='chaleco_detection',
        exist_ok=True,
        save=True,
        save_period=5,
        val=True,
        plots=True,
        verbose=True,
        patience=10,
        lr0=0.01,
        weight_decay=0.0005,
        warmup_epochs=3,
        cos_lr=True,
        close_mosaic=10
    )
    return results


def subir_modelo_a_s3(local_path, bucket_name, s3_key):
    """
    Sube un archivo local a un bucket S3
    """
    print(f"\nSubiendo modelo a S3: {bucket_name}/{s3_key}")
    s3 = boto3.client('s3')

    try:
        s3.upload_file(local_path, bucket_name, s3_key)
        print("✅ Modelo subido exitosamente a S3")
        print(f"   S3 URI: s3://{bucket_name}/{s3_key}")
    except FileNotFoundError:
        print("❌ Archivo local no encontrado:", local_path)
    except NoCredentialsError:
        print("❌ Credenciales de AWS no configuradas correctamente")
    except ClientError as e:
        print(f"❌ Error al subir el archivo: {e}")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    print("=== ENTRENAMIENTO YOLO PARA DETECCIÓN DE CHALECOS DE SEGURIDAD ===")
    print("Este script entrenará un modelo YOLO y subirá el mejor resultado a S3\n")

    if not Path("dataset").exists():
        print("Error: No se encontró la carpeta 'dataset'")
        return

    if not Path("yolov8n.pt").exists():
        print("Descargando modelo pre-entrenado...")
        YOLO('yolov8n.pt')
        print("Modelo descargado correctamente")

    try:
        dataset_reducido = crear_dataset_reducido(porcentaje=0.1)
        config_path = crear_config_yaml(dataset_reducido)

        print(f"\n{'='*50}")
        print("INICIANDO ENTRENAMIENTO")
        print(f"{'='*50}")

        results = entrenar_modelo(config_path=config_path, epochs=25, imgsz=416)

        print(f"\n{'='*50}")
        print("ENTRENAMIENTO COMPLETADO")
        print(f"{'='*50}")
        print(f"Resultados guardados en: modelo_entrenado/chaleco_detection/")
        best_model_path = Path("modelo_entrenado/chaleco_detection/weights/best.pt")
        print(f"Mejor modelo: {best_model_path}")

        # Mostrar métricas
        if hasattr(results, 'results_dict'):
            print("\nMétricas finales:")
            for key, value in results.results_dict.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:.4f}")

        # Subir modelo a S3
        if best_model_path.exists():
            subir_modelo_a_s3(
                local_path=str(best_model_path),
                bucket_name="mlops-bucket-vicari",  # Cambia si tu bucket tiene otro nombre
                s3_key="epoch20.pt"
            )
        else:
            print("⚠️ No se encontró el archivo best.pt para subir")

    except Exception as e:
        print(f"Error durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
