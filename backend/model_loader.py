import os
import time
import boto3
import logging
import schedule
import torch
from botocore.exceptions import NoCredentialsError, ClientError
from ultralytics import YOLO
from datetime import datetime
from pathlib import Path

# === CONFIGURACIÓN DE LOGGING ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === CONFIGURACIÓN GLOBAL ===
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # usar CPU
AWS_ACCESS_KEY = "AKIA53Y7UDPZVDWB4TFZ"
AWS_SECRET_KEY = "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"
AWS_REGION = "us-east-1"
BUCKET_NAME = "mlops-bucket-vicari"


def download_model_from_s3():
    """Descarga el modelo desde S3 si no está en el servidor"""
    local_path = "weights/epoch20.pt"
    s3_key = "epoch20.pt"

    if os.path.exists(local_path):
        logger.info(f"✅ Modelo ya existe en {local_path}")
        return local_path

    logger.info(f"⬇️ Descargando modelo desde S3: {BUCKET_NAME}/{s3_key}")

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION,
        )

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3.download_file(BUCKET_NAME, s3_key, local_path)
        logger.info("✅ Modelo descargado correctamente desde S3.")
        return local_path

    except (NoCredentialsError, ClientError) as e:
        logger.error(f"❌ Error descargando modelo: {e}")
        raise


def load_yolo_model(weights_path: str):
    """Carga el modelo YOLO entrenado"""
    try:
        device = torch.device('cpu')
        logger.info("🚀 Cargando modelo YOLO...")
        model = YOLO(weights_path)
        model.to(device)
        logger.info("✅ Modelo YOLO cargado correctamente en CPU")
        return model
    except Exception as e:
        logger.error(f"❌ Error al cargar el modelo YOLO: {e}")
        raise


def subir_modelo_a_s3(local_path, s3_key):
    """Sube un archivo local a S3"""
    logger.info(f"☁️ Subiendo modelo a S3: {BUCKET_NAME}/{s3_key}")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )

    try:
        s3.upload_file(local_path, BUCKET_NAME, s3_key)
        logger.info(f"Subido correctamente: s3://{BUCKET_NAME}/{s3_key}")
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {local_path}")
    except NoCredentialsError:
        logger.error("Credenciales AWS no configuradas correctamente")
    except ClientError as e:
        logger.error(f"Error al subir a S3: {e}")


def entrenar_modelo():
    """Ejecuta el entrenamiento del modelo YOLO y sube resultados a S3"""
    logger.info("\n===============================")
    logger.info("🚀 Iniciando entrenamiento YOLO")
    logger.info("===============================")

    try:
        # Descargar pesos base
        weights_path = download_model_from_s3()
        model = load_yolo_model(weights_path)

        # Entrenar
        results = model.train(
            data="dataset/data.yaml",
            epochs=20,
            imgsz=640,
            project="modelo_entrenado",
            name="chaleco_detection",
            batch=8,
            device="cpu"
        )

        # Mostrar métricas
        if hasattr(results, 'results_dict'):
            logger.info("\n📊 Métricas finales:")
            for k, v in results.results_dict.items():
                if isinstance(v, (int, float)):
                    logger.info(f"   {k}: {v:.4f}")

        # === Subir resultados a S3 ===
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        weights_dir = Path("modelo_entrenado/chaleco_detection/weights")

        # Subir best.pt
        best_model_path = weights_dir / "best.pt"
        if best_model_path.exists():
            s3_key = f"models/chaleco/best_{fecha}.pt"
            subir_modelo_a_s3(str(best_model_path), s3_key)
        else:
            logger.warning("⚠️ No se encontró best.pt para subir.")

        # Subir last.pt
        last_model_path = weights_dir / "last.pt"
        if last_model_path.exists():
            s3_key = f"models/chaleco/last_{fecha}.pt"
            subir_modelo_a_s3(str(last_model_path), s3_key)
        else:
            logger.warning("⚠️ No se encontró last.pt para subir.")

        logger.info("✅ Entrenamiento y subida completados correctamente.")

    except Exception as e:
        logger.error(f"❌ Error en entrenamiento: {e}")


# ====================================================
# 🔁 PROGRAMAR REENTRENAMIENTO CADA 7 DÍAS
# ====================================================
def iniciar_scheduler():
    """Programa la tarea de reentrenamiento cada 7 días"""
    schedule.every(7).days.do(entrenar_modelo)
    logger.info("⏰ Scheduler iniciado: el modelo se reentrenará cada 7 días")

    while True:
        schedule.run_pending()
        time.sleep(60)


# ====================================================
# 🏁 MAIN
# ====================================================
if __name__ == "__main__":
    # Entrenamiento inicial
    entrenar_modelo()

    # Activar reentrenamiento automático
    iniciar_scheduler()
