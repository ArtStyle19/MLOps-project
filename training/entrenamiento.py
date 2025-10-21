import os
import boto3
import torch
import logging
from botocore.exceptions import NoCredentialsError, ClientError
from ultralytics import YOLO

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BUCKET_NAME = "mlops-bucket-vicari"
S3_KEY = "epoch20.pt"
LOCAL_OLD_MODEL = "weights/epoch20.pt"
LOCAL_NEW_MODEL = "weights/epoch20_new.pt"

AWS_ACCESS_KEY = "AKIA53Y7UDPZVDWB4TFZ"
AWS_SECRET_KEY = "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"
REGION = "us-east-1"


# ==============================
# DESCARGA DEL MODELO EXISTENTE
# ==============================
def download_model_from_s3():
    """Descarga el modelo actual desde S3"""
    if os.path.exists(LOCAL_OLD_MODEL):
        logger.info("Modelo ya existe localmente.")
        return LOCAL_OLD_MODEL

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION,
    )

    try:
        os.makedirs(os.path.dirname(LOCAL_OLD_MODEL), exist_ok=True)
        logger.info(f"Descargando modelo desde S3: {BUCKET_NAME}/{S3_KEY}")
        s3.download_file(BUCKET_NAME, S3_KEY, LOCAL_OLD_MODEL)
        logger.info("Modelo descargado correctamente.")
        return LOCAL_OLD_MODEL
    except Exception as e:
        logger.error(f"Error al descargar modelo: {e}")
        raise


# ==============================
# ENTRENAMIENTO NUEVO MODELO
# ==============================
def train_new_model():
    """Entrena un nuevo modelo YOLO."""
    logger.info("Iniciando reentrenamiento YOLO...")
    model = YOLO(LOCAL_OLD_MODEL)
    results = model.train(
        data="data.yaml",
        epochs=5,
        imgsz=640,
        project="runs/retrain",
        name="exp",
        exist_ok=True
    )

    new_model_path = "runs/retrain/exp/weights/best.pt"
    if os.path.exists(new_model_path):
        os.rename(new_model_path, LOCAL_NEW_MODEL)
        logger.info(f"Nuevo modelo entrenado guardado en {LOCAL_NEW_MODEL}")
        return LOCAL_NEW_MODEL
    else:
        logger.error("No se encontró el nuevo modelo entrenado.")
        raise FileNotFoundError(new_model_path)


# ==============================
# EVALUACIÓN Y COMPARACIÓN
# ==============================
def evaluate_model(model_path: str):
    """Evalúa un modelo YOLO y devuelve la métrica principal (mAP50)."""
    logger.info(f"Evaluando modelo: {model_path}")
    model = YOLO(model_path)
    metrics = model.val(data="data.yaml")
    map50 = metrics.results_dict.get("metrics/mAP50(B)", 0)
    logger.info(f"mAP50 = {map50:.4f}")
    return map50


# ==============================
# SUBIDA A S3 SI ES MEJOR
# ==============================
def upload_model_to_s3(local_path):
    """Sube el modelo a S3 si mejora el anterior"""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=REGION,
    )
    try:
        logger.info(f"Subiendo nuevo modelo a S3: {local_path}")
        s3.upload_file(local_path, BUCKET_NAME, S3_KEY)
        logger.info("Nuevo modelo subido correctamente a S3.")
    except Exception as e:
        logger.error(f"Error al subir modelo: {e}")
        raise


# ==============================
# PIPELINE PRINCIPAL
# ==============================
def main():
    logger.info("Iniciando pipeline de reentrenamiento...")

    old_model_path = download_model_from_s3()
    new_model_path = train_new_model()

    old_score = evaluate_model(old_model_path)
    new_score = evaluate_model(new_model_path)

    if new_score > old_score:
        logger.info(f"Nuevo modelo es mejor ({new_score:.4f} > {old_score:.4f})")
        upload_model_to_s3(new_model_path)
    else:
        logger.info(f"Nuevo modelo no mejora ({new_score:.4f} <= {old_score:.4f}). No se sube a S3.")


if __name__ == "__main__":
    main()
